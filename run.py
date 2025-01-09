from app import create_app, socketio
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    socketio.run(app, host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'True').lower() == 'true')
