if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/static/service-worker.js").catch((err) => {
            console.error("Service worker registration failed:", err);
        });
    });
}

function insertTextAtCursor(field, text) {
    const start = field.selectionStart ?? field.value.length;
    const end = field.selectionEnd ?? field.value.length;
    field.value = `${field.value.slice(0, start)}${text}${field.value.slice(end)}`;
    const newPos = start + text.length;
    field.setSelectionRange(newPos, newPos);
    field.focus();
}

document.addEventListener("click", (event) => {
    const emojiButton = event.target.closest(".emoji-btn");
    if (!emojiButton) return;

    const toolbar = emojiButton.closest(".emoji-toolbar");
    const targetId = toolbar?.dataset?.target;
    const emoji = emojiButton.dataset.emoji || "";
    if (!targetId || !emoji) return;

    const noteField = document.getElementById(targetId);
    if (!noteField) return;

    insertTextAtCursor(noteField, emoji);
});
