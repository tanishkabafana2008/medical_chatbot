const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("message");
const sendBtn = document.getElementById("sendBtn");
const typing = document.getElementById("typing");
const historyList = document.getElementById("historyList");
const newChatBtn = document.getElementById("newChat");
const uploadBtn = document.getElementById("uploadBtn");
const voiceBtn = document.getElementById("voiceBtn");
const speakBtn = document.getElementById("speakBtn");

let lastBotMessage = "";

// Send message when button is clicked
sendBtn.addEventListener("click", sendMessage);

// Send message when Enter is pressed
messageInput.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// Start a new chat (clears server-side session history too)
newChatBtn.addEventListener("click", async function () {
    await fetch("/new_chat", { method: "POST" });

    chatBox.innerHTML = `
        <div class="bot-message">
            <div class="avatar">🤖</div>
            <div class="message">
                <h4>MediBot AI</h4>
                <p>Hello 👋<br><br>How can I help you today?</p>
            </div>
        </div>
    `;
});

// Main function: send the typed message to the server
async function sendMessage() {
    const message = messageInput.value.trim();

    if (message === "") return;

    addUserMessage(message);
    messageInput.value = "";

    typing.style.display = "block";
    scrollBottom();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        typing.style.display = "none";
        addBotMessage(data.response);
        loadHistory();
    } catch (error) {
        typing.style.display = "none";
        addBotMessage("Sorry, something went wrong.");
    }
}

// Ask a suggested question (used by the suggestion buttons in index.html)
function askQuestion(question) {
    messageInput.value = question;
    sendMessage();
}

function addUserMessage(message) {
    chatBox.innerHTML += `
        <div class="user-message">
            <div class="message">
                <h4>You</h4>
                <p>${escapeHtml(message)}</p>
            </div>
            <div class="avatar">😊</div>
        </div>
    `;
    scrollBottom();
}

function addBotMessage(message) {
    lastBotMessage = message;

    chatBox.innerHTML += `
        <div class="bot-message">
            <div class="avatar">🤖</div>
            <div class="message ai-response">
                <h4>MediBot AI</h4>
                <div>${message}</div>
            </div>
        </div>
    `;
    scrollBottom();
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function scrollBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Load recent chat history into the sidebar
async function loadHistory() {
    try {
        const response = await fetch("/history");
        const history = await response.json();

        historyList.innerHTML = "";

        history.slice(-10).reverse().forEach(function (item) {
            const li = document.createElement("li");
            li.textContent = item.user.substring(0, 40) + "...";
            historyList.appendChild(li);
        });
    } catch (error) {
        console.log(error);
    }
}

// Upload a PDF medical report for explanation
uploadBtn.addEventListener("click", async function () {
    const file = document.getElementById("pdfFile").files[0];

    if (!file) {
        alert("Select a PDF first");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    typing.style.display = "block";

    try {
        const response = await fetch("/upload_report", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        typing.style.display = "none";
        addBotMessage(data.response);
    } catch (error) {
        typing.style.display = "none";
        addBotMessage("Sorry, I couldn't process that report.");
    }
});

// Voice input (speech-to-text)
voiceBtn.addEventListener("click", function () {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Voice recognition is not supported in this browser");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    recognition.onstart = function () {
        voiceBtn.innerHTML = "🎙️";
    };

    recognition.onresult = function (event) {
        messageInput.value = event.results[0][0].transcript;
    };

    recognition.onend = function () {
        voiceBtn.innerHTML = "🎤";
    };
});

// Voice output (text-to-speech) for the last bot reply
speakBtn.addEventListener("click", function () {
    if (lastBotMessage === "") {
        alert("No response available");
        return;
    }

    const speech = new SpeechSynthesisUtterance(
        // Strip HTML tags before reading it aloud
        lastBotMessage.replace(/<[^>]*>/g, "")
    );
    speech.lang = "en-US";
    speech.rate = 1;
    speech.pitch = 1;

    window.speechSynthesis.speak(speech);
});

// Load history and initial greeting when the page opens
window.onload = function () {
    renderInitialGreeting();
    loadHistory();
};

function renderInitialGreeting() {
    if (chatBox.innerHTML.trim() !== "") return;

    chatBox.innerHTML = `
        <div class="bot-message">
            <div class="avatar">🤖</div>
            <div class="message">
                <h4>MediBot AI</h4>
                <div>Hello 👋 I am your trusted medical assistant. Ask me about symptoms, medications, test reports, or care guidance and I will explain it clearly with professional detail.</div>
                <small>⚠ This is informational only. Please consult a healthcare professional for diagnosis and treatment.</small>
            </div>
        </div>
        <div class="suggestions">
            <h3>Try one of these:</h3>
            <button type="button" onclick="askQuestion('What are the symptoms of hypertension?')">Symptoms of hypertension</button>
            <button type="button" onclick="askQuestion('How can I manage my medicine schedule?')">Medicine schedule guidance</button>
            <button type="button" onclick="askQuestion('What should I do if I have a fever?')">Fever care steps</button>
        </div>
    `;
    scrollBottom();
}
