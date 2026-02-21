const OrigWebSocket = window.WebSocket;

const wsProxy = new Proxy(OrigWebSocket, {
    construct(target, args) {
        //console.log("🌐 [ESPION] Une connexion WebSocket a été interceptée !");
        const ws = new target(...args);

        // --- 1. Écouter ce qui RENTRE (Les mouvements des potes) ---
        ws.addEventListener('message', function(event) {
            analyserMessage(event.data, "REÇU 📥");
        });

        // --- 2. Écouter ce qui SORT (Tes propres mouvements) ---
        const originalSend = ws.send;
        ws.send = function(data) {
            analyserMessage(data, "ENVOYÉ 📤");
            // On n'oublie pas d'envoyer réellement le message pour ne pas casser le jeu !
            originalSend.apply(ws, arguments); 
        };

        return ws;
    }
});

// On installe le mouchard
window.WebSocket = wsProxy;

// --- La fonction qui cherche les X et Y dans le texte ---
function analyserMessage(dataStr, direction) {
    try {
        // On s'assure que c'est bien du texte
        if (typeof dataStr !== 'string') return; 

        let jsonStart = dataStr.indexOf('{'); 
        
        if (jsonStart !== -1) {
            let jsonStr = dataStr.substring(jsonStart);
            let data = JSON.parse(jsonStr);

            // C'est ici qu'on filtre !
            if (data.a === 'moveItem' && data.x !== undefined && data.y !== undefined) {
                //console.log(`🎯 [ESPION] Mouvement ${direction} capturé ! ID:`, data.key);
                // On passe le relais au facteur (content.js)
                window.dispatchEvent(new CustomEvent('LetsRoleTokenMove', { detail: data }));
            }

            if (data.a === 'display' && data.c === "scene" ) {
                window.dispatchEvent(new CustomEvent('InitScene', { detail: data }));
            }

            if (data.a === 'addToken' && data.c === "scene") {
                window.dispatchEvent(new CustomEvent('AddToken', { detail: data }));
            }

            if (data.a === 'transformItem' && data.c === "scene") {
                window.dispatchEvent(new CustomEvent('TransformItem', { detail: data }));
            }
        }
    } catch (e) {
        // On ignore silencieusement tout ce qui n'est pas du JSON
    }
}