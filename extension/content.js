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
// ⚙️ TOKEN ID (chargé depuis le stockage de l'extension)
// ==========================================
let MY_TOKEN_ID = null;

chrome.storage.local.get('myTokenId', (data) => {
    MY_TOKEN_ID = data.myTokenId || null;
    if (MY_TOKEN_ID) {
        console.log(`🎯 [PONT] Token chargé : ${MY_TOKEN_ID}`);
    } else {
        console.warn("⚠️ [PONT] Aucun token configuré. Clique sur l'icône de l'extension pour le saisir.");
    }
});

chrome.storage.onChanged.addListener((changes) => {
    if (changes.myTokenId) {
        MY_TOKEN_ID = changes.myTokenId.newValue || null;
        console.log(`🔄 [PONT] Token mis à jour : ${MY_TOKEN_ID}`);
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
    
    console.log(`📤 TOEKN INFO  =${data.key}, =${MY_TOKEN_ID}`);
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