document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("chatbot-btn");
    const box = document.getElementById("chatbot-float-box");
    const chat = document.getElementById("chatbox");
    const input = document.getElementById("chat-input");
    const send = document.getElementById("chat-send");

    // Floating button toggle
    toggleBtn.onclick = function () {
        box.style.display = box.style.display === "block" ? "none" : "block";
    };

    // Add message bubbles
    function appendMessage(text, who = "bot") {
        const div = document.createElement("div");
        div.className = who === "user" ? "msg user" : "msg bot";
        div.innerText = text;
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
    }

    // Send message to backend
    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        appendMessage(text, "user");
        input.value = "";

        try {
            const response = await fetch("/chatbot", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();
            appendMessage(data.reply, "bot");
        } catch (err) {
            appendMessage("Error connecting to server.", "bot");
        }
    }

    send.addEventListener("click", sendMessage);

    // Enter key sends message
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    // Initial greeting
    appendMessage("Hello! I am Event Bot X,your event assistant.");
});

