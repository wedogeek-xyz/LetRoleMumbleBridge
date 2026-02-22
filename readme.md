# 🎙️ Let's Role — Mumble Spatial Audio Bridge

## C'est quoi ?

Ce projet permet d'avoir de l'**audio spatial automatique** dans Mumble lors de vos sessions de jeu de rôle sur **Let's Role**. Concrètement : si votre personnage est loin d'un autre sur la carte, vous entendrez sa voix comme si elle venait de loin. Si vous êtes côte à côte, il sera juste à côté de vous dans votre casque.

L'orientation compte aussi : si votre personnage fait face au nord, vous entendrez les voix venir de la gauche, de la droite ou de derrière selon leur position relative.

Pas besoin de régler quoi que ce soit pendant la session — positions et orientations se mettent à jour automatiquement en temps réel selon les tokens sur la carte.

---

## Comment ça marche ?

```
Let's Role (navigateur Chrome)
        │
        │  Extension Chrome intercepte les événements WebSocket du jeu
        ▼
  Bridge Python (sur le PC de chaque joueur)
        │
        │  Reçoit position + orientation via WebSocket local
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
Intercepte les événements WebSocket de Let's Role pour détecter les mouvements et l'orientation du token du joueur. Elle identifie automatiquement l'ID du token à partir du nom du personnage configuré — même si cet ID change en cours de partie (recréation de token, rechargement de scène).

**2. Le bridge Python** (chez chaque joueur)
Script Python qui tourne en arrière-plan avec une petite interface graphique. Il reçoit les données de position et d'orientation envoyées par l'extension et les écrit dans MumbleLink — la mémoire partagée que Mumble surveille pour positionner les voix en 3D.

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

Une petite interface graphique s'ouvre avec :
- L'état de la connexion MumbleLink et du navigateur
- La scène active, la position et l'orientation du token en temps réel
- Un bouton **Recharger la configuration** pour prendre en compte les modifications de `scenes_config.json` sans redémarrer

### 2. L'extension Chrome

1. Télécharge **lets-role-spatial-audio.zip** depuis la [dernière release](../../releases)
2. Extraire le zip
3. Dans Chrome, ouvre `chrome://extensions`
4. Active le **Mode développeur** (en haut à droite)
5. Clique sur **"Charger l'extension non empaquetée"** et sélectionne le dossier extrait
6. Clique sur l'icône de l'extension dans la barre Chrome
7. Saisis le **nom de ton personnage** (ex: `Thalgrum`) et clique **Enregistrer**

> Le token ID est détecté automatiquement au chargement de la scène. Si le token est recréé en cours de partie (drag & drop depuis le bestiaire, rechargement), la mise à jour est automatique.

### 3. Lancer une session

1. Lance **run.bat** avant d'ouvrir Let's Role
2. Connecte-toi à Mumble normalement
3. Ouvre Let's Role dans Chrome — dès que la scène se charge, le bridge se synchronise

---

## Événements interceptés

L'extension injecte un proxy WebSocket dans la page Let's Role pour écouter les messages du jeu. Elle filtre quatre types d'événements :

### `InitScene` — Chargement de scène
**Déclenché par :** l'ouverture ou le rechargement d'une scène dans Let's Role.

L'extension reçoit la structure complète de la scène (tous les tokens, toutes les couches). Elle parcourt les tokens pour retrouver celui dont le nom du personnage correspond au nom configuré dans le popup, et sauvegarde sa `key`. C'est le mécanisme principal de détection du token du joueur.

### `LetsRoleTokenMove` — Déplacement du token
**Déclenché par :** le déplacement d'un token sur la carte (drag & drop).

L'extension reçoit les coordonnées pixel `x` et `y` du token. Si l'ID correspond au token du joueur, elles sont converties en mètres (selon la valeur `pixels_per_meter` de la scène) et envoyées au bridge. Mumble positionne alors la voix en 3D en conséquence.

### `TransformItem` — Rotation du token
**Déclenché par :** la rotation d'un token sur la carte.

L'extension reçoit l'angle de rotation en degrés. Si l'ID correspond au token du joueur, il est transmis au bridge, qui calcule le vecteur d'orientation (`fAvatarFront`) correspondant pour MumbleLink. Cela permet à Mumble de savoir dans quelle direction le joueur "regarde" et de positionner les voix des autres joueurs relativement à cette orientation.

### `AddToken` — Dépôt d'un nouveau token
**Déclenché par :** le glisser-déposer d'un avatar depuis le bestiaire ou le panneau personnages sur la carte.

L'extension reçoit les données du nouveau token. Si le nom du personnage correspond, elle met à jour l'ID sauvegardé et envoie immédiatement la nouvelle position au bridge. Cela gère le cas où un token est supprimé et recréé en cours de partie.

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
- **`scenes`** : map `"ID de scène" → pixels/mètre`

L'ID de scène est visible dans l'URL Let's Role ou dans l'interface du bridge (champ **Scène**).

Pour recharger sans redémarrer : clique sur **Recharger la configuration** dans l'interface du bridge.

### Isolation audio par scène

Le bridge encode l'ID de scène dans le champ `context` de MumbleLink. Mumble n'applique l'audio positionnel qu'entre joueurs partageant le même contexte — ce qui signifie que des joueurs sur des scènes différentes n'interféreront pas entre eux, même s'ils sont connectés au même serveur Mumble.

---

## Pourquoi cette architecture ?

L'audio positionnel dans Mumble fonctionne **entièrement côté client**. Le serveur ne fait que redistribuer les données de position — il ne calcule rien lui-même. Chaque client Mumble doit donc recevoir et traiter sa propre position localement via MumbleLink. Le bridge est inévitable, mais volontairement minimaliste : pas de configuration serveur, juste un script léger en arrière-plan.

Let's Role n'expose pas d'API publique de positions. L'extension intercepte les messages WebSocket internes au jeu pour en extraire les données pertinentes, sans modifier le comportement du jeu.

---

## Limites connues

- **Windows uniquement** pour les joueurs (MumbleLink est une API Windows)
- **Chrome uniquement** (l'extension utilise les APIs Chrome)
- Le bridge doit être lancé avant d'ouvrir Let's Role

---

## Crédits

Projet développé pour les sessions JDR en ligne avec Let's Role + Mumble.
Basé sur le protocole **MumbleLink** (standard officiel Mumble pour l'audio positionnel).
