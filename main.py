# -*- coding: utf-8 -*-
# Pydroid 3 launcher - v5
import os
import sys
import threading

def find_project_dir():
    """Find the directory containing bot.py and config.py.
    Pydroid may execute this file as <string>, so __file__ is not reliable.
    """
    candidates = []
    for p in [os.getcwd()] + list(sys.path):
        if not p:
            continue
        try:
            p = os.path.abspath(p)
        except Exception:
            continue
        if p not in candidates:
            candidates.append(p)

    # Search current directory and a few levels below it.
    for base in candidates[:8]:
        if os.path.isfile(os.path.join(base, "bot.py")):
            return base
        try:
            for dirpath, dirnames, filenames in os.walk(base):
                # Avoid huge/system directories.
                dirnames[:] = [d for d in dirnames if d not in {
                    ".git", "__pycache__", "node_modules"
                }]
                if "bot.py" in filenames and "config.py" in filenames:
                    return dirpath
        except (OSError, PermissionError):
            pass

    return os.getcwd()

PROJECT_DIR = find_project_dir()
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)

print("[OK] Project directory:", PROJECT_DIR)
print("[OK] Pydroid launcher v5")

# Verify local modules before importing the bot.
required = ["bot.py", "config.py", "database.py", "garena.py",
            "spam_manager.py", "ban_manager.py"]
missing = [f for f in required if not os.path.isfile(os.path.join(PROJECT_DIR, f))]
if missing:
    print("[!] Missing project files:", ", ".join(missing))
    print("[!] Put main.py in the same extracted folder as the project files.")
    raise SystemExit(1)

def start_optional_flask():
    try:
        from flask import Flask
        from config import FLASK_PORT
        app = Flask(__name__)

        @app.route("/")
        def health():
            return "SERVER ONLINE"

        app.run(host="0.0.0.0", port=FLASK_PORT,
                debug=False, use_reloader=False)
    except Exception as e:
        print("[!] Optional Flask server not started:", e)

def main():
    try:
        from bot import run_telegram_bot
    except ModuleNotFoundError as e:
        print("[!] Failed to load bot:", e)
        print("[!] Make sure all project files are in:", PROJECT_DIR)
        raise

    try:
        threading.Thread(target=start_optional_flask, daemon=True).start()
    except Exception as e:
        print("[!] Optional web server disabled:", e)

    run_telegram_bot()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Stopped.")
