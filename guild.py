import json
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# API endpoint (আগের Vercel লিংক বর্তমানে 404 দেখায়; সচল লিংক পেলে এখানে পরিবর্তন করুন)
API_BASE = "https://danger-guild-management-web.vercel.app/join"
ACCOUNTS_FILE = "accounts.json"

# --- Render Web Service-এর পোর্ট বাইন্ডিং ও সার্ভার ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot service is active on Render!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# --- অ্যাকাউন্ট লোড করার ফাংশন ---
def load_accounts(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "accounts" in data:
            data = data["accounts"]
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[ERROR] Accounts file load error: {e}")
        return []

# --- গিল্ড জয়েন রিকোয়েস্ট ফাংশন ---
def join_guild(guild_id, uid, password, session=None):
    url = f"{API_BASE}?guild_id={guild_id}&uid={uid}&password={password}"
    try:
        requester = session if session else requests
        resp = requester.get(url, timeout=15)
        try:
            body = resp.json()
        except Exception:
            body = resp.text

        if resp.status_code == 200:
            return True, f"SUCCESS — {body}"
        else:
            return False, f"HTTP {resp.status_code} — {body}"
    except Exception as e:
        return False, str(e)

# --- মূল জয়েনিং লজিক ---
def bot_worker():
    # Render-এর Environment Variable থেকে Guild ID নেবে, না থাকলে ডিফল্ট মান ব্যবহার করবে
    guild_id = os.environ.get("GUILD_ID", "123456789")  # আপনার গিল্ড আইডি এখানে বসান
    
    accounts = load_accounts(ACCOUNTS_FILE)
    if not accounts:
        print("[ERROR] No accounts found in accounts.json.")
        return

    session = requests.Session()
    print("-" * 50)
    print(f"[INFO] Target Guild ID: {guild_id}")
    print(f"[INFO] Loaded Accounts: {len(accounts)}")
    print("-" * 50)

    for idx, acc in enumerate(accounts, start=1):
        uid = str(acc.get("uid", "")).strip()
        password = str(acc.get("password", "")).strip()

        if not uid or not password:
            print(f"[{idx}/{len(accounts)}] SKIPPED — Missing UID/PW")
            continue

        ok, msg = join_guild(guild_id, uid, password, session)
        if ok:
            print(f"[{idx}/{len(accounts)}] UID: {uid} -> ✅ JOINED")
        else:
            print(f"[{idx}/{len(accounts)}] UID: {uid} -> ❌ FAILED ({msg})")

        time.sleep(0.5)

    print("-" * 50)
    print("[DONE] Process finished.")

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে জয়েনিং প্রসেস চালু করা
    worker_thread = threading.Thread(target=bot_worker)
    worker_thread.daemon = True
    worker_thread.start()

    # মেইন থ্রেডে ওয়েব সার্ভার চালু রাখা (Render সার্ভিস সচল রাখার জন্য)
    run_web_server()
