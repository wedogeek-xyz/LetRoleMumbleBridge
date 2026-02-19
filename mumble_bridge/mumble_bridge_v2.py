import asyncio
import websockets
import json
import mmap
import ctypes
import math
import sys
import os

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
        print(f"✅ Config scènes chargée : {len(config.get('scenes', {}))} scène(s) configurée(s)")
        return config
    except FileNotFoundError:
        print(f"⚠️ Fichier scenes_config.json introuvable, valeur par défaut : 50 px/m")
        return {"default_pixels_per_meter": 50, "scenes": {}}
    except json.JSONDecodeError as e:
        print(f"⚠️ Erreur de lecture scenes_config.json : {e}, valeur par défaut : 50 px/m")
        return {"default_pixels_per_meter": 50, "scenes": {}}

SCENES_CONFIG = load_scenes_config()
PIXELS_PER_METER = SCENES_CONFIG["default_pixels_per_meter"]  # valeur par défaut

# ==========================================
# STRUCTURE MUMBLE LINK
# ==========================================
class Link(ctypes.Structure):
    _fields_ = [
        ("uiVersion", ctypes.c_uint32),
        ("uiTick", ctypes.c_uint32),
        ("fAvatarPosition", ctypes.c_float * 3),
        ("fAvatarFront", ctypes.c_float * 3),
        ("fAvatarTop", ctypes.c_float * 3),
        ("name", ctypes.c_wchar * 256),
        ("fCameraPosition", ctypes.c_float * 3),
        ("fCameraFront", ctypes.c_float * 3),
        ("fCameraTop", ctypes.c_float * 3),
        ("identity", ctypes.c_wchar * 256),
        ("context_len", ctypes.c_uint32),
        ("context", ctypes.c_ubyte * 256),
        ("description", ctypes.c_wchar * 2048)
    ]

# Variables globales
current_pos = {"x": 0.0, "z": 0.0}
start_offset = {"x": None, "z": None}
pixels_per_meter = PIXELS_PER_METER  # sera mis à jour selon la scène active

def init_mumble():
    try:
        shm = mmap.mmap(0, ctypes.sizeof(Link), "MumbleLink", mmap.ACCESS_WRITE)
        return shm
    except Exception:
        return None

# ==========================================
# HB
# ==========================================
async def mumble_heartbeat():
    print("❤️ Heartbeat activé (50Hz)...")
    shm = init_mumble()
    if not shm:
        print("❌ Impossible d'accéder à la Mumble")
        return

    lnk = Link.from_buffer(shm)
    tick = 0

    while True:
        lnk.uiVersion = 2
        lnk.uiTick = tick
        tick += 1
        
        lnk.name = "Let's Role"
        lnk.description = "Audio Spatialisé"
        context_str = "wdg" 
        lnk.context_len = len(context_str)
        ctypes.memmove(lnk.context, context_str.encode('utf-8'), lnk.context_len)   

        # Lecture de la position actuelle
        x = current_pos["x"]
        z = current_pos["z"]

        # Mise à jour Avatar
        lnk.fAvatarPosition[0] = x
        lnk.fAvatarPosition[1] = 0.0
        lnk.fAvatarPosition[2] = z

        # Vecteur avant (Nord)
        lnk.fAvatarFront[0] = 0.0
        lnk.fAvatarFront[1] = 0.0
        lnk.fAvatarFront[2] = 1.0 
        lnk.fAvatarTop[0] = 0.0
        lnk.fAvatarTop[1] = 1.0
        lnk.fAvatarTop[2] = 0.0

        # Mise à jour Caméra
        lnk.fCameraPosition[0] = x
        lnk.fCameraPosition[1] = 0.0
        lnk.fCameraPosition[2] = z
        lnk.fCameraFront[0] = 0.0
        lnk.fCameraFront[1] = 0.0
        lnk.fCameraFront[2] = 1.0
        lnk.fCameraTop[0] = 0.0
        lnk.fCameraTop[1] = 1.0
        lnk.fCameraTop[2] = 0.0

        await asyncio.sleep(0.02) # 50 fois par seconde

# ==========================================
# 📡 SERVEUR WEBSOCKET (VERSION MULTIJOUEUR)
# ==========================================
async def websocket_server(websocket):
    global pixels_per_meter
    print("🟢 Navigateur connecté ! En attente de mouvement...")
    try:
        async for message in websocket:
            data = json.loads(message)

            # On prend les vraies coordonnées de la carte Let's Role
            raw_x = float(data.get('x', 0))
            raw_y = float(data.get('y', 0))
            scene = str(data.get('scene', ""))
            idPlayer = str(data.get('player_id', ""))
            # Sélection du pixels_per_meter selon la scène
            scenes = SCENES_CONFIG.get("scenes", {})
            if scene in scenes:
                pixels_per_meter = scenes[scene]
            else:
                pixels_per_meter = SCENES_CONFIG["default_pixels_per_meter"]

            # PLUS DE CALIBRAGE ! On convertit directement en mètres
            current_pos["x"] = raw_x / pixels_per_meter
            current_pos["z"] = raw_y / pixels_per_meter

            # Affichage console
            print(f"📍 Scène {scene} ({pixels_per_meter}px/m) | X={current_pos['x']:.1f}m, Z={current_pos['z']:.1f}m   {idPlayer}  ", end="\r")
            
    except websockets.exceptions.ConnectionClosed:
        print("\n🔴 Navigateur déconnecté.")

async def console_listener():
    print("💡 Tape 'r' + Entrée pour recharger scenes_config.json")
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if line.strip().lower() == "r":
            global SCENES_CONFIG
            SCENES_CONFIG = load_scenes_config()
            print("🔄 Config rechargée !")

async def main():
    print("🚀 Pont Mumble V2 démarré...")
    asyncio.create_task(mumble_heartbeat())
    asyncio.create_task(console_listener())
    async with websockets.serve(websocket_server, "localhost", 8080):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())