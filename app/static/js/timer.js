class PomodoroTimer {
    constructor() {
        this.timeLeft = 25 * 60; // 25 minutes in seconds
        this.isRunning = false;
        this.interval = null;
        this.state = 'IDLE';
        this.socket = io();
        
        this.initializeElements();
        this.initializeEventListeners();
    }
    
    initializeElements() {
        this.minutesDisplay = document.getElementById('timer-minutes');
        this.secondsDisplay = document.getElementById('timer-seconds');
        this.startButton = document.getElementById('start-timer');
        this.pauseButton = document.getElementById('pause-timer');
        this.resetButton = document.getElementById('reset-timer');
        this.stateDisplay = document.getElementById('current-state');
    }
    
    initializeEventListeners() {
        this.startButton.addEventListener('click', () => this.start());
        this.pauseButton.addEventListener('click', () => this.pause());
        this.resetButton.addEventListener('click', () => this.reset());
    }
    
    updateDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        
        this.minutesDisplay.textContent = minutes.toString().padStart(2, '0');
        this.secondsDisplay.textContent = seconds.toString().padStart(2, '0');
        this.stateDisplay.textContent = this.state;
    }
    
    start() {
        if (!this.isRunning) {
            this.isRunning = true;
            this.state = 'FOCUSING';
            this.startButton.disabled = true;
            this.pauseButton.disabled = false;
            
            this.interval = setInterval(() => {
                this.timeLeft--;
                this.updateDisplay();
                
                if (this.timeLeft <= 0) {
                    this.complete();
                }
            }, 1000);
            
            this.socket.emit('timer_sync', {
                state: this.state,
                remaining: this.timeLeft
            });
        }
    }
    
    pause() {
        if (this.isRunning) {
            this.isRunning = false;
            this.state = 'IDLE';
            this.startButton.disabled = false;
            this.pauseButton.disabled = true;
            clearInterval(this.interval);
            
            this.socket.emit('timer_sync', {
                state: this.state,
                remaining: this.timeLeft
            });
        }
    }
    
    reset() {
        this.pause();
        this.timeLeft = 25 * 60;
        this.updateDisplay();
    }
    
    complete() {
        this.pause();
        this.state = 'BREAK';
        this.timeLeft = 5 * 60; // 5 minute break
        this.updateDisplay();
        
        // Play notification sound and show browser notification
        this.notify();
    }
    
    notify() {
        const audio = new Audio('/static/audio/notification.mp3');
        audio.play();
        
        if (Notification.permission === 'granted') {
            new Notification('Pomodoro Complete!', {
                body: 'Time for a break!',
                icon: '/static/img/icon.png'
            });
        }
    }
}

// Initialize timer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const timer = new PomodoroTimer();
    
    // Request notification permission
    if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
});
