// Core state
let currentUsername = localStorage.getItem('username') || 'anonymous';

// DOM Elements
const messagesContainer = document.getElementById('messages-container');
const messageForm = document.querySelector('.message-form');
const usernameDisplay = document.getElementById('current-username');
const changeUsernameBtn = document.getElementById('change-username-btn');

// Mark body as having JS
document.body.classList.add('has-js');

// Main functions
async function loadMessages() {
    const response = await fetch('/messages');
    const messages = await response.json();
    displayMessages(messages);
}

function displayMessages(messages) {
    messagesContainer.innerHTML = messages.map(msg => `
        <div class="message">
            <div class="message-header">
                <span class="message-author">${msg.author}</span>
                <span class="message-date">${new Date(msg.date).toLocaleString()}</span>
            </div>
            <div class="message-content">${msg.content}</div>
        </div>
    `).join('');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendMessage(content, type = 'message') {
    const response = await fetch('/messages', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ content, type, author: currentUsername })
    });
    
    if (response.ok) {
        await loadMessages();
        return true;
    }
    return false;
}

async function changeUsername(newUsername) {
    if (!/^[a-zA-Z0-9_]{3,20}$/.test(newUsername)) {
        alert('Invalid username format. Use 3-20 letters, numbers, or underscores.');
        return false;
    }
    
    const content = JSON.stringify({
        old_username: currentUsername,
        new_username: newUsername
    });
    
    const success = await sendMessage(content, 'username_change');
    if (success) {
        currentUsername = newUsername;
        localStorage.setItem('username', newUsername);
        usernameDisplay.textContent = `Current username: ${newUsername}`;
        return true;
    }
    return false;
}

// Event listeners
messageForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const textarea = messageForm.querySelector('textarea');
    const content = textarea.value.trim();
    
    if (content) {
        if (await sendMessage(content)) {
            textarea.value = '';
        }
    }
});

changeUsernameBtn.addEventListener('click', () => {
    const newUsername = prompt('Enter new username:');
    if (newUsername) {
        changeUsername(newUsername);
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMessages();
    usernameDisplay.textContent = `Current username: ${currentUsername}`;
    
    // Poll for new messages every 5 seconds
    setInterval(loadMessages, 5000);
});
