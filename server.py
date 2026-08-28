# server.py
from flask import Flask
from config import FLASK_PORT

flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "⚡ R32 SHADOW PREMIUM SERVER IS ONLINE AND WORK STABLE!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=FLASK_PORT, debug=False, use_reloader=False)