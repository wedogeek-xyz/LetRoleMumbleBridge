# 🎙️ Let's Role — Mumble Spatial Audio Bridge

## C'est quoi ?

Ce projet permet d'avoir de l'**audio spatial automatique** dans Mumble lors de vos sessions de jeu de rôle sur **Let's Role**. Concrètement : si votre personnage est loin d'un autre sur la carte, vous entendrez sa voix comme si elle venait de loin. Si vous êtes côte à côte, il sera juste à côté de vous dans votre casque.

Pas besoin de régler quoi que ce soit pendant la session — les positions se mettent à jour automatiquement en temps réel selon où se trouvent les tokens sur la carte.

---

## Comment ça marche ?

```
Let's Role (navigateur Chrome)
        │
        │  Extension Chrome lit la position du token en temps réel
        ▼
  Bridge Python (sur le PC de chaque joueur)
        │
        │  Reçoit la position via WebSocket
        ▼
  MumbleLink (mémoire partagée Windows)
        │
        │  Protocole standard de Mumble
        ▼
  Client Mumble 🎧
        │
        │  Positionne les voix en 3D automatiquement
        ▼
  Vous entendez vos amis selon leur position sur la carte !
```

### Les deux composants

**1. L'extension Chrome** (chez chaque joueur)
Lit en temps réel la position du token du joueur sur la carte Let's Role et l'envoie au bridge local. Elle détecte automatiquement l'ID du token à partir du nom du personnage configuré — même si cet ID change en cours de partie.

**2. Le bridge Python** (chez chaque joueur)
Petit script Python qui tourne en arrière-plan. Il reçoit la position envoyée par l'extension et l'écrit dans MumbleLink — la mémoire partagée que Mumble surveille pour positionner les voix en 3D.

---

## Prérequis

- Windows (MumbleLink est une API Windows)
- **Google Chrome** avec l'extension installée
- **Python 3.x** — téléchargeable sur [python.org](https://www.python.org/downloads/) — cocher **"Add Python to PATH"** lors de l'installation
- **Client Mumble** installé et connecté au serveur

---

## Installation

### 1. Le bridge Python

1. Télécharge **mumble-bridge.zip** depuis la [dernière release](../../releases)
2. Extraire le zip dans un dossier de ton choix
3. Double-clique sur **run.bat** — les dépendances s'installent automatiquement au premier lancement

> Le fichier `scenes_config.json` (dans le même dossier) permet de configurer le nombre de pixels par mètre selon l'ID de la scène. Tu peux l'éditer sans relancer le bridge : tape `r` + Entrée dans la console pour recharger la configuration à chaud.

### 2. L'extension Chrome

1. Télécharge **lets-role-spatial-audio.zip** depuis la [dernière release](../../releases)
2. Extraire le zip
3. Dans Chrome, ouvre `chrome://extensions`
4. Active le **Mode développeur** (en haut à droite)
5. Clique sur **"Charger l'extension non empaquetée"** et sélectionne le dossier extrait
6. Clique sur l'icône de l'extension dans la barre Chrome
7. Saisis le **nom de ton personnage** (ex: `thalgrum`) et clique **Enregistrer**

> Le token ID est détecté automatiquement au chargement de la scène. Si le token est recréé en cours de partie, la mise à jour est automatique.

### 3. Lancer une session

1. Lance **run.bat** avant d'ouvrir Let's Role
2. Connecte-toi à Mumble normalement
3. Ouvre Let's Role dans Chrome — dès que les tokens bougent, les voix se positionnent automatiquement

---

## Configuration des scènes (`scenes_config.json`)

Ce fichier associe un ID de scène Let's Role à une valeur de pixels par mètre, qui calibre la distance sonore.

```json
{
    "default_pixels_per_meter": 50,
    "scenes": {
        "408970": 50,
        "123456": 100
    }
}
```

- **`default_pixels_per_meter`** : valeur utilisée si la scène n'est pas listée
- **`scenes`** : map `ID de scène → pixels/mètre`

Pour recharger sans redémarrer : tape **`r`** + Entrée dans la console du bridge.

---

## Pourquoi cette architecture ?

L'audio positionnel dans Mumble fonctionne **entièrement côté client**. Le serveur ne fait que redistribuer les données de position — il ne calcule rien lui-même. Chaque client Mumble doit donc recevoir et traiter sa propre position localement via MumbleLink. Le bridge est inévitable, mais volontairement minimaliste : pas de configuration serveur, juste un script léger en arrière-plan.

---

## Limites connues

- **Windows uniquement** pour les joueurs (MumbleLink est une API Windows)
- **Chrome uniquement** (l'extension utilise les APIs Chrome)
- Le bridge doit être lancé avant d'ouvrir Let's Role

---

## Crédits

Projet développé pour les sessions JDR en ligne avec Let's Role + Mumble.
Basé sur le protocole **MumbleLink** (standard officiel Mumble pour l'audio positionnel).
