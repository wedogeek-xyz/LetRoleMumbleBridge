// ==========================================
// 📡 LE PONT
// ==========================================
let localSocket = null;
function connectToPython() {
    localSocket = new WebSocket('ws://localhost:8080');
    localSocket.onopen = () => console.log("🟢 [PONT] Connecté au Python !");
    localSocket.onclose = () => setTimeout(connectToPython, 3000);
}
connectToPython();

// ==========================================
// ⚙️ TOKEN ID + NOM DU PERSONNAGE
// ==========================================
let MY_TOKEN_ID = null;
let MY_CHARACTER_NAME = null;

chrome.storage.local.get(['myTokenId', 'myCharacterName'], (data) => {
    MY_TOKEN_ID = data.myTokenId || null;
    MY_CHARACTER_NAME = data.myCharacterName || null;
    if (MY_TOKEN_ID) {
        console.log(`🎯 [PONT] Token chargé : ${MY_TOKEN_ID}`);
    } else if (MY_CHARACTER_NAME) {
        console.warn(`⚠️ [PONT] Personnage "${MY_CHARACTER_NAME}" configuré, en attente du chargement de scène...`);
    } else {
        console.warn("⚠️ [PONT] Aucun personnage configuré. Clique sur l'icône de l'extension.");
    }
});

chrome.storage.onChanged.addListener((changes) => {
    if (changes.myTokenId) {
        MY_TOKEN_ID = changes.myTokenId.newValue || null;
        console.log(`🔄 [PONT] Token mis à jour : ${MY_TOKEN_ID}`);
    }
    if (changes.myCharacterName) {
        MY_CHARACTER_NAME = changes.myCharacterName.newValue || null;
    }
});

// ==========================================
// 🕵️ INJECTION
// ==========================================
const script = document.createElement('script');
script.src = chrome.runtime.getURL('inject.js');
(document.head || document.documentElement).appendChild(script);

window.addEventListener('LetsRoleTokenMove', (event) => {
    const data = event.detail;

    if (!MY_TOKEN_ID || data.key !== MY_TOKEN_ID) {
        return;
    }

    console.log(`📤 Envoi vers Mumble : X=${data.x}, Y=${data.y}`);

    if (localSocket && localSocket.readyState === WebSocket.OPEN) {
        localSocket.send(JSON.stringify({
            player_id: data.key,
            x: data.x,
            y: data.y,
            scene: data.scene
        }));
    }
});


// ==========================================
// 🔄 TRANSFORM ITEM : rotation du token
// ==========================================
window.addEventListener('TransformItem', (event) => {
    const data = event.detail;

    if (!MY_TOKEN_ID || data.key !== MY_TOKEN_ID) return;

    if (localSocket && localSocket.readyState === WebSocket.OPEN) {
        localSocket.send(JSON.stringify({
            player_id: data.key,
            rotation: data.rotation,
            scene: data.scene
        }));
    }
});

// ==========================================
// ➕ ADD TOKEN : mise à jour si le token du personnage est recréé
// ==========================================
window.addEventListener('AddToken', (event) => {
    const data = event.detail;

    if (!MY_CHARACTER_NAME) return;

    const token = data?.token;
    if (token?.character?.name?.toLowerCase() === MY_CHARACTER_NAME.toLowerCase()) {
        console.log(`🔄 [PONT] Token de "${MY_CHARACTER_NAME}" recréé, nouvelle key : ${token.key}`);
        chrome.storage.local.set({ myTokenId: token.key });

        if (localSocket && localSocket.readyState === WebSocket.OPEN) {
            localSocket.send(JSON.stringify({
                player_id: token.key,
                x: token.x,
                y: token.y,
                scene: data.sceneId
            }));
        }
    }
});

// ==========================================
// 🗺️ INIT SCÈNE : détection automatique du token
// ==========================================
window.addEventListener('InitScene', (event) => {
    const data = event.detail;

    if (!MY_CHARACTER_NAME) {
        console.warn("⚠️ [PONT] InitScene reçu mais aucun nom de personnage configuré.");
        return;
    }

    const layers = data?.scene?.data?.layers;
    if (!layers) return;

    const searchName = MY_CHARACTER_NAME.toLowerCase();
    let foundKey = null;

    for (const layer of Object.values(layers)) {
        if (!layer.token) continue;
        for (const item of Object.values(layer.items || {})) {
            if (item.character?.name?.toLowerCase() === searchName) {
                foundKey = item.key;
                break;
            }
        }
        if (foundKey) break;
    }

    if (foundKey) {
        console.log(`✅ [PONT] Token de "${MY_CHARACTER_NAME}" détecté : ${foundKey}`);
        chrome.storage.local.set({ myTokenId: foundKey });
    } else {
        console.warn(`⚠️ [PONT] Personnage "${MY_CHARACTER_NAME}" introuvable dans la scène.`);
    }
});
