import asyncio
import websockets
import json
import mmap
import ctypes
import math
import sys
import os
import threading
import queue
import tkinter as tk
import platform
import os
from tkinter import ttk

# ==========================================
# CONFIGURATION
# ==========================================
def load_scenes_config():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "scenes_config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        n = len(config.get('scenes', {}))
        ui_queue.put({'type': 'log', 'text': f"✅ Config chargée : {n} scène(s)"})
        return config
    except FileNotFoundError:
        ui_queue.put({'type': 'log', 'text': "⚠️ scenes_config.json introuvable, défaut : 50 px/m"})
        return {"default_pixels_per_meter": 50, "scenes": {}}
    except json.JSONDecodeError as e:
        ui_queue.put({'type': 'log', 'text': f"⚠️ Erreur JSON : {e}"})
        return {"default_pixels_per_meter": 50, "scenes": {}}

# ==========================================
# STRUCTURE MUMBLE LINK
# ==========================================
class Link(ctypes.Structure):
    _fields_ = [
        ("uiVersion",        ctypes.c_uint32),
        ("uiTick",           ctypes.c_uint32),
        ("fAvatarPosition",  ctypes.c_float * 3),
        ("fAvatarFront",     ctypes.c_float * 3),
        ("fAvatarTop",       ctypes.c_float * 3),
        ("name",             ctypes.c_wchar * 256),
        ("fCameraPosition",  ctypes.c_float * 3),
        ("fCameraFront",     ctypes.c_float * 3),
        ("fCameraTop",       ctypes.c_float * 3),
        ("identity",         ctypes.c_wchar * 256),
        ("context_len",      ctypes.c_uint32),
        ("context",          ctypes.c_ubyte * 256),
        ("description",      ctypes.c_wchar * 2048)
    ]

# ==========================================
# ÉTAT GLOBAL
# ==========================================
current_pos    = {"x": 0.0, "z": 0.0, "scene": "default", "rotation": 0.0}
pixels_per_meter = 50
ui_queue       = queue.Queue()
reload_event   = threading.Event()
SCENES_CONFIG  = {}   # initialisé après démarrage du thread asyncio

def init_mumble():
    try:
        if platform.system() == "Windows":
            # --- Méthode Windows ---
            shm = mmap.mmap(0, ctypes.sizeof(Link), "MumbleLink", mmap.ACCESS_WRITE)
            return shm
        else:
            # --- Méthode Linux ---
            # Mumble crée un fichier virtuel en RAM. Il contient souvent l'UID de l'utilisateur.
            uid = os.getuid()
            shm_path = f"/dev/shm/MumbleLink.{uid}"
            
            # Fallback au cas où Mumble utiliserait l'ancien nommage sans l'UID
            if not os.path.exists(shm_path):
                shm_path = "/dev/shm/MumbleLink"
                
            # On ouvre le descripteur du fichier en lecture/écriture
            fd = os.open(shm_path, os.O_RDWR)
            
            # On mappe le fichier en mémoire RAM
            shm = mmap.mmap(fd, ctypes.sizeof(Link), mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
            return shm
            
    except Exception as e:
        # Afficher l'erreur exacte aide beaucoup au débogage sur Linux
        print(f"❌ Impossible d'accéder à la mémoire Mumble : {e}")
        return None
    
# ==========================================
# HEARTBEAT
# ==========================================
async def mumble_heartbeat():
    shm = init_mumble()
    if not shm:
        ui_queue.put({'type': 'log', 'text': "❌ Impossible d'accéder à MumbleLink"})
        ui_queue.put({'type': 'mumble', 'ok': False})
        return

    ui_queue.put({'type': 'mumble', 'ok': True})
    lnk  = Link.from_buffer(shm)
    tick = 0

    while True:
        lnk.uiVersion = 2
        lnk.uiTick    = tick
        tick += 1

        lnk.name        = "Let's Role"
        lnk.description = "Audio Spatialisé"

        context_bytes   = ("wdg_" + current_pos["scene"]).encode('utf-8')
        lnk.context_len = len(context_bytes)
        ctypes.memmove(lnk.context, context_bytes, lnk.context_len)

        x = current_pos["x"]
        z = current_pos["z"]

        lnk.fAvatarPosition[0] = x
        lnk.fAvatarPosition[1] = 0.0
        lnk.fAvatarPosition[2] = z

        rot_rad = math.radians(current_pos["rotation"])
        lnk.fAvatarFront[0] = math.sin(rot_rad)
        lnk.fAvatarFront[1] = 0.0
        lnk.fAvatarFront[2] = -math.cos(rot_rad)
        lnk.fAvatarTop[0]   = 0.0
        lnk.fAvatarTop[1]   = 1.0
        lnk.fAvatarTop[2]   = 0.0

        lnk.fCameraPosition[0] = x
        lnk.fCameraPosition[1] = 0.0
        lnk.fCameraPosition[2] = z
        lnk.fCameraFront[0]    = 0.0
        lnk.fCameraFront[1]    = 0.0
        lnk.fCameraFront[2]    = 1.0
        lnk.fCameraTop[0]      = 0.0
        lnk.fCameraTop[1]      = 1.0
        lnk.fCameraTop[2]      = 0.0

        await asyncio.sleep(0.02)

# ==========================================
# SERVEUR WEBSOCKET
# ==========================================
async def websocket_server(websocket):
    global pixels_per_meter
    ui_queue.put({'type': 'browser', 'connected': True})
    ui_queue.put({'type': 'log', 'text': "🟢 Navigateur connecté"})
    try:
        async for message in websocket:
            data  = json.loads(message)
            scene = str(data.get('scene', ""))

            if 'rotation' in data:
                current_pos["rotation"] = float(data['rotation'])

            if 'x' in data and 'y' in data:
                raw_x = float(data['x'])
                raw_y = float(data['y'])
                scenes = SCENES_CONFIG.get("scenes", {})
                pixels_per_meter = scenes.get(scene, SCENES_CONFIG.get("default_pixels_per_meter", 50))
                current_pos["x"] = raw_x / pixels_per_meter
                current_pos["z"] = raw_y / pixels_per_meter

            current_pos["scene"] = scene

            ui_queue.put({'type': 'position',
                          'scene':     scene,
                          'x':         current_pos["x"],
                          'z':         current_pos["z"],
                          'rotation':  current_pos["rotation"],
                          'ppm':       pixels_per_meter,
                          'player_id': data.get('player_id', '')})
    except websockets.exceptions.ConnectionClosed:
        ui_queue.put({'type': 'browser', 'connected': False})
        ui_queue.put({'type': 'log', 'text': "🔴 Navigateur déconnecté"})

# ==========================================
# RECHARGEMENT CONFIG (déclenché par le bouton)
# ==========================================
async def reload_watcher():
    loop = asyncio.get_event_loop()
    while True:
        triggered = await loop.run_in_executor(None, lambda: reload_event.wait(timeout=1.0))
        if triggered:
            reload_event.clear()
            global SCENES_CONFIG
            SCENES_CONFIG = load_scenes_config()

# ==========================================
# BOUCLE ASYNCIO (thread secondaire)
# ==========================================
async def main():
    global SCENES_CONFIG
    SCENES_CONFIG = load_scenes_config()
    ui_queue.put({'type': 'log', 'text': "🚀 Pont Mumble démarré"})
    asyncio.create_task(mumble_heartbeat())
    asyncio.create_task(reload_watcher())
    async with websockets.serve(websocket_server, "localhost", 8080):
        await asyncio.Future()

def run_asyncio():
    asyncio.run(main())

# ==========================================
# INTERFACE GRAPHIQUE
# ==========================================
class BridgeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Let's Role · Spatial Audio")
        self.root.resizable(False, False)
        self.root.configure(padx=14, pady=14)

        # ── Statuts ───────────────────────────────────
        status_frame = ttk.Frame(root)
        status_frame.pack(fill='x', pady=(0, 10))

        # Mumble
        mumble_col = ttk.Frame(status_frame)
        mumble_col.pack(side='left', expand=True)
        self.mumble_dot   = tk.Label(mumble_col, text='●', fg='#888888', font=('', 13))
        self.mumble_dot.pack()
        ttk.Label(mumble_col, text='MumbleLink').pack()

        # Navigateur
        browser_col = ttk.Frame(status_frame)
        browser_col.pack(side='left', expand=True)
        self.browser_dot  = tk.Label(browser_col, text='●', fg='#888888', font=('', 13))
        self.browser_dot.pack()
        ttk.Label(browser_col, text='Navigateur').pack()

        ttk.Separator(root, orient='horizontal').pack(fill='x', pady=(0, 10))

        # ── Données temps réel ────────────────────────
        info_frame = ttk.Frame(root)
        info_frame.pack(fill='x', pady=(0, 10))

        self.scene_var  = tk.StringVar(value='—')
        self.pos_var    = tk.StringVar(value='—')
        self.rot_var    = tk.StringVar(value='—')
        self.ppm_var    = tk.StringVar(value='—')
        self.token_var  = tk.StringVar(value='—')

        rows = [
            ('Scène',       self.scene_var),
            ('Position',    self.pos_var),
            ('Rotation',    self.rot_var),
            ('Px / mètre',  self.ppm_var),
            ('Token ID',    self.token_var),
        ]
        for i, (label, var) in enumerate(rows):
            ttk.Label(info_frame, text=label + ' :', anchor='w', width=12).grid(
                row=i, column=0, sticky='w', pady=2)
            ttk.Label(info_frame, textvariable=var, anchor='w', width=30).grid(
                row=i, column=1, sticky='w', pady=2)

        ttk.Separator(root, orient='horizontal').pack(fill='x', pady=(0, 10))

        # ── Boutons ───────────────────────────────────
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill='x', pady=(0, 10))
        ttk.Button(btn_frame, text='🔄  Recharger la configuration',
                   command=self.reload_config).pack(side='left', expand=True, fill='x', padx=(0, 4))
        ttk.Button(btn_frame, text='Quitter',
                   command=root.destroy).pack(side='left')

        # ── Journal ───────────────────────────────────
        ttk.Label(root, text='Journal :', anchor='w').pack(fill='x')
        self.log_text = tk.Text(root, height=7, width=50, state='disabled',
                                font=('Consolas', 9), bg='#1e1e1e', fg='#cccccc',
                                relief='flat', wrap='word', padx=4, pady=4)
        self.log_text.pack(fill='both', expand=True)

        self.poll()

    def poll(self):
        try:
            while True:
                msg = ui_queue.get_nowait()
                t   = msg['type']
                if t == 'mumble':
                    color = '#33cc66' if msg['ok'] else '#cc3333'
                    self.mumble_dot.config(fg=color)
                elif t == 'browser':
                    color = '#33cc66' if msg['connected'] else '#cc3333'
                    self.browser_dot.config(fg=color)
                elif t == 'position':
                    self.scene_var.set(msg['scene'] or '—')
                    self.pos_var.set(f"X: {msg['x']:.2f} m   Z: {msg['z']:.2f} m")
                    self.rot_var.set(f"{msg['rotation']:.1f}°")
                    self.ppm_var.set(str(msg['ppm']))
                    self.token_var.set(msg['player_id'] or '—')
                elif t == 'log':
                    self._add_log(msg['text'])
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def _add_log(self, text):
        self.log_text.config(state='normal')
        self.log_text.insert('end', text + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def reload_config(self):
        reload_event.set()

# ==========================================
# POINT D'ENTRÉE
# ==========================================
if __name__ == "__main__":
    threading.Thread(target=run_asyncio, daemon=True).start()
    root = tk.Tk()
    BridgeApp(root)
    root.mainloop()
