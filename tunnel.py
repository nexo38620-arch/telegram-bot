# tunnel.py
import os
import re
import shutil
import subprocess
import threading
from config import FLASK_PORT

def get_base_url() -> str:
    if os.path.exists("cloudflare_url.txt"):
        try:
            with open("cloudflare_url.txt", "r") as f:
                saved = f.read().strip()
                if saved and "trycloudflare.com" in saved:
                    return saved
        except:
            pass
    return "http://localhost:5000"

def start_cloudflare_tunnel():
    if not shutil.which("cloudflared"):
        print("⚠️ [Cloudflare Tunnel] cloudflared is not installed.")
        return False

    print("⚡ Spawning Cloudflare Quick Tunnel...")
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{FLASK_PORT}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        def monitor_output():
            for line in iter(proc.stdout.readline, ""):
                match = re.search(r"https://[-a-zA-Z0-9]+\.trycloudflare\.com", line)
                if match:
                    public_url = match.group(0)
                    with open("cloudflare_url.txt", "w") as f:
                        f.write(public_url)
                    print(f"✅ Cloudflare Tunnel Active: {public_url}")
                    break
        
        threading.Thread(target=monitor_output, daemon=True).start()
        return True
    except Exception as e:
        print(f"⚠️ Cloudflare Startup Error: {e}")
        return False