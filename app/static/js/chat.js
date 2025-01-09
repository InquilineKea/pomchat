class ChatApp {
    constructor() {
        this.socket = io();
        this.currentRoom = null;
        this.messages = [];
        this.users = new Set();
        
        this.initializeElements();
        this.initializeSocketListeners();
        this.initializeEventListeners();
        this.loadRooms();
    }
    
    initializeElements() {
        this.messagesList = document.getElementById('messages');
        this.messageForm = document.getElementById('message-form');
        this.messageInput = document.getElementById('message-input');
        this.roomsList = document.getElementById('rooms-list');
        this.usersList = document.getElementById('users-list');
        this.createRoomButton = document.getElementById('create-room');
    }
    
    initializeSocketListeners() {
        this.socket.on('message', (data) => this.handleNewMessage(data));
        this.socket.on('user_status', (data) => this.handleUserStatus(data));
        this.socket.on('focus_change', (data) => this.handleFocusChange(data));
    }
    
    initializeEventListeners() {
        this.messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        this.createRoomButton.addEventListener('click', () => this.createRoom());
    }
    
    async loadRooms() {
        const response = await fetch('/api/rooms');
        const rooms = await response.json();
        
        this.roomsList.innerHTML = rooms.map(room => `
            <div class="room-item" data-room-id="${room.id}">
                <span class="room-name">${room.name}</span>
                <span class="room-count">${room.member_count}</span>
            </div>
        `).join('');
        
        this.roomsList.querySelectorAll('.room-item').forEach(item => {
            item.addEventListener('click', () => {
                const roomId = item.dataset.roomId;
                this.joinRoom(roomId);
            });
        });
    }
    
    async createRoom() {
        const name = prompt('Enter room name:');
        if (!name) return;
        
        const response = await fetch('/api/rooms', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        
        if (response.ok) {
            this.loadRooms();
        }
    }
    
    async joinRoom(roomId) {
        if (this.currentRoom) {
            this.socket.emit('leave_room', { room_id: this.currentRoom });
        }
        
        this.currentRoom = roomId;
        this.socket.emit('join_room', { room_id: roomId });
        
        // Load room messages
        const response = await fetch(`/api/messages?room_id=${roomId}`);
        const messages = await response.json();
        
        this.messages = messages;
        this.renderMessages();
    }
    
    async sendMessage() {
        if (!this.currentRoom || !this.messageInput.value.trim()) return;
        
        const response = await fetch('/api/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: this.messageInput.value,
                room_id: this.currentRoom
            })
        });
        
        if (response.ok) {
            this.messageInput.value = '';
        }
    }
    
    handleNewMessage(data) {
        this.messages.push(data);
        this.renderMessages();
    }
    
    handleUserStatus(data) {
        if (data.status === 'online') {
            this.users.add(data.username);
        } else if (data.status === 'offline') {
            this.users.delete(data.username);
        }
        
        this.renderUsers();
    }
    
    handleFocusChange(data) {
        const userElement = this.usersList.querySelector(`[data-username="${data.username}"]`);
        if (userElement) {
            userElement.dataset.focusState = data.focus_state;
        }
    }
    
    renderMessages() {
        this.messagesList.innerHTML = this.messages.map(msg => `
            <div class="message" data-type="${msg.type}">
                <div class="message-header">
                    <span class="message-author">${msg.author}</span>
                    <span class="message-time">${new Date(msg.created_at).toLocaleTimeString()}</span>
                </div>
                <div class="message-content">${msg.content}</div>
            </div>
        `).join('');
        
        this.messagesList.scrollTop = this.messagesList.scrollHeight;
    }
    
    renderUsers() {
        this.usersList.innerHTML = Array.from(this.users).map(username => `
            <div class="user-item" data-username="${username}">
                <span class="user-name">${username}</span>
                <span class="user-status"></span>
            </div>
        `).join('');
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const chat = new ChatApp();
});
