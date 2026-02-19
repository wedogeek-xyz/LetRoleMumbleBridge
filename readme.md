# 🎙️ Let's Role — Mumble Spatial Audio Bridge

## C'est quoi ?

Ce projet permet d'avoir de l'**audio spatial automatique** dans Mumble lors de vos sessions de jeu de rôle sur **Let's Role**. Concrètement : si votre personnage est loin d'un autre sur la carte, vous entendrez sa voix comme si elle venait de loin. Si vous êtes côte à côte, il sera juste à côté de vous dans votre casque.

Pas besoin de régler quoi que ce soit pendant la session — les positions se mettent à jour automatiquement en temps réel selon où se trouvent les tokens sur la carte.

---

## Comment ça marche ?

### Vue d'ensemble

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

**1. L'extension Chrome (chez chaque joueur)**
Une extension installée dans Chrome lit en temps réel la position du token du joueur sur la carte Let's Role et l'envoie au bridge Python local via WebSocket. Pas de configuration complexe — l'extension tourne automatiquement dès que Let's Role est ouvert.

Code source dans `extension` 

**2. Le bridge Python (chez chaque joueur)**
Un petit script Python tourne en arrière-plan sur le PC de chaque joueur. Il reçoit la position envoyée par l'extension Chrome et l'écrit dans MumbleLink — la mémoire partagée que Mumble surveille pour positionner les voix en 3D. C'est le seul "pont" entre le navigateur et Mumble.


Code source dans `mumble_bridge` 

---

## Prérequis

### Côté serveur Mumble
- **Mumble Server (Murmur)** installé et fonctionnel
- L'audio positionnel fonctionne entièrement **côté client** — aucune configuration serveur particulière n'est nécessaire pour la spatialisation

### Chez chaque joueur
- Windows (MumbleLink utilise la mémoire partagée Windows)
- **Google Chrome** avec l'extension installée
- **Python 3.x** avec la bibliothèque `websockets`
- **Client Mumble** installé et connecté au serveur

---

## Configuration initiale (à faire une seule fois)

### 1. Installer l'extension Chrome
Chaque joueur installe l'extension dans Chrome. Elle se connecte automatiquement au bridge Python local au démarrage de Let's Role.

### 2. Lancer le bridge Python
Chaque joueur lance le bridge Python en arrière-plan avant la session. Il suffit de le démarrer une fois — il tourne silencieusement et ne nécessite aucune interaction.

### 3. Se connecter à Mumble normalement
La session Let's Role commence — dès que les tokens bougent sur la carte, les voix se positionnent automatiquement dans Mumble.

---

## Pourquoi cette architecture ?

### Ce qu'on a exploré
L'idée initiale était de tout gérer côté serveur Mumble via l'API Ice (interface d'administration de Murmur), sans que les joueurs aient à faire tourner quoi que ce soit localement.

### Ce qu'on a découvert
L'audio positionnel dans Mumble fonctionne **entièrement côté client**. Le serveur ne fait que redistribuer les données de position entre les clients — il ne calcule rien lui-même. Il est donc impossible de "pousser" des positions depuis le serveur : chaque client Mumble doit recevoir et traiter sa propre position localement via MumbleLink.

C'est d'ailleurs une conception intelligente : avec N joueurs, il y aurait N² flux audio à calculer côté serveur. En le faisant côté client, chaque machine ne calcule que les N-1 autres positions qui la concernent.

### Conclusion
Le mini-script client est inévitable, mais il est volontairement **très simple** : pas de configuration Ice, pas de serveur à administrer. Juste un script léger qui tourne en arrière-plan.

---

## Limites connues

- **Windows uniquement** pour les joueurs (MumbleLink est une API Windows)
- **Chrome uniquement** pour le navigateur (l'extension est développée pour Chrome)
- Le bridge Python doit être lancé avant d'ouvrir Let's Role

---

## Crédits

Projet développé pour les sessions JDR en ligne avec Let's Role + Mumble.  
Basé sur le protocole **MumbleLink** (standard officiel Mumble pour l'audio positionnel).