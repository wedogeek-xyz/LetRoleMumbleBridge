import asyncio
import websockets
import json
import sys
import os

# ==========================================
# DÉPENDANCES REQUISES
# pip install zeroc-ice websockets
#
# Télécharger MumbleServer.ice depuis :
# https://raw.githubusercontent.com/mumble-voip/mumble/master/src/murmur/MumbleServer.ice
# et le placer dans le même dossier que ce script.
# ==========================================

try:
    import Ice
    import IcePy
except ImportError:
    print("❌ zeroc-ice non installé. Lancez : pip install zeroc-ice")
    sys.exit(1)

# ==========================================
# CONFIGURATION
# ==========================================

PIXELS_PER_METER = 50

# Adresse et port Ice de Murmur (machine distante)
MURMUR_HOST = "192.168.1.115"   # ← Remplacer par l'IP de ton serveur Murmur
MURMUR_ICE_PORT = 16502
MURMUR_ICE_SECRET = "ton_secret"  # ← icesecretread/write dans murmur.ini
MURMUR_VIRTUAL_SERVER_ID = 1    # ID du serveur virtuel Murmur (1 par défaut)

# Port WebSocket que Let's Role contacte
WEBSOCKET_PORT = 8080

# ==========================================
# MAPPING userId Let's Role → pseudo Mumble
# ==========================================
# Clé   = userId envoyé par Let's Role  (string ou int, à adapter)
# Valeur = pseudo exact du joueur dans Mumble
USER_MAPPING = {
    "3597e7fd-5c03-418a-905d-4e7e898a72c6": "nayosis",
    "user_def456": "Legolas",
    "user_ghi789": "Gimli",
    # Ajouter autant de joueurs que nécessaire
}

# ==========================================
# STATE — positions de tous les joueurs
# ==========================================
# { mumble_username: {"x": float, "z": float} }
players_positions = {}

# ==========================================
# CONNEXION ICE À MURMUR
# ==========================================

murmur_server = None  # Instance du serveur virtuel Murmur

def connect_murmur():
    global murmur_server
    try:
        # Charger le fichier MumbleServer.ice (compatible exe et script)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(__file__)
        ice_file = os.path.join(base_dir, "MumbleServer.ice")
        if not os.path.exists(ice_file):
            print(f"❌ Fichier MumbleServer.ice introuvable : {ice_file}")
            print("   Téléchargez-le depuis : https://raw.githubusercontent.com/mumble-voip/mumble/master/src/murmur/MumbleServer.ice")
            return False

        communicator = Ice.initialize(["--Ice.ImplicitContext=Shared"])
        communicator.getImplicitContext().put("secret", MURMUR_ICE_SECRET)

        # Slice dynamique
        slice_dir = Ice.getSliceDir()
        Ice.loadSlice([f"-I{slice_dir}", ice_file])
        import MumbleServer  # importé dynamiquement après loadSlice

        proxy = communicator.stringToProxy(
            f"Meta:tcp -h {MURMUR_HOST} -p {MURMUR_ICE_PORT}"
        )
        meta = MumbleServer.MetaPrx.checkedCast(proxy)
        if not meta:
            print("❌ Impossible de caster le proxy MumbleServer Meta")
            return False

        murmur_server = meta.getServer(MURMUR_VIRTUAL_SERVER_ID)
        if not murmur_server:
            print(f"❌ Serveur virtuel ID={MURMUR_VIRTUAL_SERVER_ID} introuvable")
            return False

        print(f"✅ Connecté à MumbleServer ({MURMUR_HOST}:{MURMUR_ICE_PORT}), serveur virtuel #{MURMUR_VIRTUAL_SERVER_ID}")
        return True

    except Exception as e:
        print(f"❌ Erreur connexion Murmur Ice : {e}")
        return False


def get_mumble_session_id(username: str) -> int | None:
    """Retrouve le session ID Mumble d'un joueur par son pseudo."""
    if murmur_server is None:
        return None
    try:
        users = murmur_server.getUsers()
        for session_id, user in users.items():
            if user.name == username:
                return session_id
        return None
    except Exception as e:
        print(f"⚠️  Erreur getUsers() : {e}")
        return None


def push_positions_to_murmur():
    """
    Envoie la position 3D de chaque joueur à Murmur via Ice.
    MumbleServer.User.pos est un MumbleServer.Position3D {x, y, z} (float).
    """
    if murmur_server is None:
        return

    import MumbleServer  # disponible après loadSlice

    for username, pos in players_positions.items():
        session_id = get_mumble_session_id(username)
        if session_id is None:
            # Joueur pas encore connecté à Mumble, on ignore silencieusement
            continue
        try:
            state = murmur_server.getState(session_id)
            state.pos = MumbleServer.Position3D(
                x=pos["x"],
                y=0.0,
                z=pos["z"]
            )
            murmur_server.setState(state)
        except Exception as e:
            print(f"⚠️  Erreur setState pour {username} : {e}")


# ==========================================
# BOUCLE D'ENVOI DES POSITIONS (50 Hz)
# ==========================================

async def position_push_loop():
    print("📡 Boucle d'envoi des positions démarrée (50Hz)...")
    while True:
        push_positions_to_murmur()
        await asyncio.sleep(0.02)


# ==========================================
# SERVEUR WEBSOCKET
# ==========================================

async def websocket_server(websocket):
    client_addr = websocket.remote_address
    print(f"🟢 Navigateur connecté depuis {client_addr}")

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                print("⚠️  Message non-JSON reçu, ignoré.")
                continue

            # Identification du joueur
            user_id = str(data.get("userId") or data.get("playerId", "") or data.get("player_id", ""))
            raw_x = float(data.get("x", 0))
            raw_y = float(data.get("y", 0))

            if not user_id:
                print("⚠️  Message sans userId/playerId, ignoré.")
                continue

            mumble_name = USER_MAPPING.get(user_id)
            if mumble_name is None:
                print(f"⚠️  userId '{user_id}' absent du mapping, ignoré.")
                continue

            # Conversion pixels → mètres
            players_positions[mumble_name] = {
                "x": raw_x / PIXELS_PER_METER,
                "z": raw_y / PIXELS_PER_METER,
            }

            print(
                f"📍 {mumble_name:15s} | "
                f"X={players_positions[mumble_name]['x']:6.1f}m  "
                f"Z={players_positions[mumble_name]['z']:6.1f}m   ",
                end="\r"
            )

    except websockets.exceptions.ConnectionClosed:
        print(f"\n🔴 Navigateur {client_addr} déconnecté.")


# ==========================================
# MAIN
# ==========================================

async def main():
    print("🚀 Mumble Bridge V3 — Multi-joueurs via Ice/RPC (MumbleServer)")
    print(f"   Murmur cible : {MURMUR_HOST}:{MURMUR_ICE_PORT}")
    print(f"   WebSocket    : ws://localhost:{WEBSOCKET_PORT}")
    print(f"   Joueurs mappés : {len(USER_MAPPING)}")
    print()

    if not connect_murmur():
        print("❌ Impossible de démarrer sans connexion Murmur. Vérifiez la config.")
        sys.exit(1)

    asyncio.create_task(position_push_loop())

    async with websockets.serve(websocket_server, "0.0.0.0", WEBSOCKET_PORT):
        print(f"✅ Serveur WebSocket en écoute sur 0.0.0.0:{WEBSOCKET_PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())