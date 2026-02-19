"""
Script de build portable — génère le .exe sans dépendre du poste.
Usage : python build.py
"""
import subprocess
import sys
import os
import shutil
import Ice

# Trouve automatiquement le dossier slice de zeroc-ice sur ce poste
slice_dir = os.path.normpath(Ice.getSliceDir())
print(f"📦 Dossier slice Ice trouvé : {slice_dir}")

# Nettoyage
for folder in ["build", "dist"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"🧹 Dossier '{folder}' supprimé")
if os.path.exists("mumble_bridge_v3.spec"):
    os.remove("mumble_bridge_v3.spec")
    print("🧹 Fichier .spec supprimé")

# Commande PyInstaller
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--add-data", f"{slice_dir}{os.pathsep}slice",
    "mumble_bridge_v3.py"
]

print(f"\n🔨 Compilation en cours...")
print(f"   Commande : {' '.join(cmd)}\n")

result = subprocess.run(cmd)

if result.returncode == 0:
    print("\n✅ Build réussi ! Exécutable : dist\\mumble_bridge_v3.exe")
    print("   N'oublie pas de copier MumbleServer.ice dans dist\\")
else:
    print("\n❌ Build échoué.")
    sys.exit(1)