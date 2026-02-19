import asyncio
import websockets
import json
import mmap
import ctypes
import math
import sys

# ==========================================
# CONFIGURATION
# ==========================================
# 10 pixels pour 1 m = Très sensible
PIXELS_PER_METER = 50 

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
    print("🟢 Navigateur connecté ! En attente de mouvement...")
    try:
        async for message in websocket:
            data = json.loads(message)
            
            # On prend les vraies coordonnées de la carte Let's Role
            raw_x = float(data.get('x', 0))
            raw_y = float(data.get('y', 0))

            # PLUS DE CALIBRAGE ! On convertit directement en mètres
            current_pos["x"] = raw_x / PIXELS_PER_METER
            current_pos["z"] = raw_y / PIXELS_PER_METER
            
            # Affichage console
            print(f"📍 Position absolue : X={current_pos['x']:.1f}m, Z={current_pos['z']:.1f}m   ", end="\r")
            
    except websockets.exceptions.ConnectionClosed:
        print("\n🔴 Navigateur déconnecté.")

async def main():
    print("🚀 Pont Mumble V2 démarré...")
    asyncio.create_task(mumble_heartbeat())
    async with websockets.serve(websocket_server, "localhost", 8080):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())