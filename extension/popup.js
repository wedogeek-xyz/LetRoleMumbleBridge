document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('tokenId');
  const status = document.getElementById('status');

  chrome.storage.local.get('myTokenId', (data) => {
    if (data.myTokenId) input.value = data.myTokenId;
  });

  document.getElementById('save').addEventListener('click', () => {
    const token = input.value.trim();
    chrome.storage.local.set({ myTokenId: token }, () => {
      status.textContent = '✅ Token enregistré !';
      setTimeout(() => status.textContent = '', 2000);
    });
  });
});
