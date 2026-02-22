document.addEventListener('DOMContentLoaded', () => {
  const manifest = chrome.runtime.getManifest();
  document.getElementById('version').textContent =
    'v' + (manifest.version_name || manifest.version);
  const input = document.getElementById('characterName');
  const status = document.getElementById('status');
  const tokenDisplay = document.getElementById('tokenDisplay');

  chrome.storage.local.get(['myCharacterName', 'myTokenId'], (data) => {
    if (data.myCharacterName) input.value = data.myCharacterName;
    tokenDisplay.textContent = data.myTokenId || '—';
  });

  document.getElementById('save').addEventListener('click', () => {
    const name = input.value.trim();
    chrome.storage.local.set({ myCharacterName: name }, () => {
      status.textContent = '✅ Enregistré ! Sera actif au prochain chargement de scène.';
      setTimeout(() => status.textContent = '', 3000);
    });
  });

  // Mise à jour du token affiché si détecté pendant que le popup est ouvert
  chrome.storage.onChanged.addListener((changes) => {
    if (changes.myTokenId) {
      tokenDisplay.textContent = changes.myTokenId.newValue || '—';
    }
  });
});
