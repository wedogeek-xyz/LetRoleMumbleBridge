// ==========================================
// ⚙️ TA CONFIGURATION
// ==========================================
// Remets bien ton ID de token ici !
const MY_TOKEN_ID = "3597e7fd-5c03-418a-905d-4e7e898a72c6"; 

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
// 🕵️ INJECTION
// ==========================================
const script = document.createElement('script');
script.src = chrome.runtime.getURL('inject.js');
(document.head || document.documentElement).appendChild(script);

window.addEventListener('LetsRoleTokenMove', (event) => {
    const data = event.detail;

    // Affiche l'ID dans la console pour debug
    // console.log("Token bougé:", data.key);

    // On ne traite que TON token
    if (data.key !== MY_TOKEN_ID) {
        return; 
    }

    console.log(`📤 Envoi vers Mumble : X=${data.x}, Y=${data.y}`);

    if (localSocket && localSocket.readyState === WebSocket.OPEN) {
        localSocket.send(JSON.stringify({
            player_id: data.key,
            x: data.x,
            y: data.y
        }));
    }
});