"""
Script de build portable — génère le .exe sans dépendre du poste.
Usage : python build.py
"""
import subprocess
import sys
import os
import shutil
import Ice



# Nettoyage
for folder in ["build", "dist"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"🧹 Dossier '{folder}' supprimé")
if os.path.exists("mumble_bridge_v2.spec"):
    os.remove("mumble_bridge_v2.spec")
    print("🧹 Fichier .spec supprimé")

# Commande PyInstaller
cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "mumble_bridge_v2.py"
]

print(f"\n🔨 Compilation en cours...")
print(f"   Commande : {' '.join(cmd)}\n")

result = subprocess.run(cmd)

if result.returncode != 0:
    print("\n❌ Build échoué.")
    sys.exit(1)

print("\n✅ Build réussi ! Exécutable : dist\\mumble_bridge_v2.exe")