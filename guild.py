import json
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# --- আপনার সেটিংস (এখানে পরিবর্তন করুন) ---
# আপনি যে গিল্ডে সবাইকে জয়েন করাতে চান, তার আইডি নিচে কোটেশনের ভেতর লিখুন
TARGET_GUILD_ID = "123456789"  # <--- এখানে আপনার আসল Guild ID বসিয়ে দিন

# API লিংক (নতুন বা কার্যকর লিংক পেলে এখানে পরিবর্তন করবেন)
API_BASE = "https://danger-guild-management-web.vercel.app/join"
ACCOUNTS_FILE = "accounts.json"


# --- Render Web Service সচল রাখার জন্য ফেক সার্ভার ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("বট সার্ভিস সফলভাবে সচল রয়েছে!".encode("utf-8"))

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()


# --- accounts.json ফাইল থেকে অ্যাকাউন্ট লোড করা ---
def load_accounts(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "accounts" in data:
            data = data["accounts"]
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[ত্রুটি] অ্যাকাউন্ট ফাইল লোড করা যায়নি: {e}")
        return []


# --- গিল্ডে জয়েন করার রিকোয়েস্ট পাঠানো ---
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
            return True, f"সফল — {body}"
        else:
            return False, f"HTTP {resp.status_code} — {body}"
    except Exception as e:
        return False, str(e)


# --- মূল প্রসেসিং ফাংশন ---
def bot_worker():
    # যদি Render Environment-এ GUILD_ID থাকে তবে সেটি নেবে, না থাকলে কোডের TARGET_GUILD_ID ব্যবহার করবে
    guild_id = os.environ.get("GUILD_ID", TARGET_GUILD_ID).strip()
    
    accounts = load_accounts(ACCOUNTS_FILE)
    if not accounts:
        print("[ত্রুটি] accounts.json ফাইলে কোনো অ্যাকাউন্ট পাওয়া যায়নি।")
        return

    session = requests.Session()
    print("=" * 50)
    print(f"[তথ্য] টার্গেট গিল্ড আইডি : {guild_id}")
    print(f"[তথ্য] মোট অ্যাকাউন্ট সংখ্যা : {len(accounts)}")
    print("=" * 50)

    for idx, acc in enumerate(accounts, start=1):
        uid = str(acc.get("uid", "")).strip()
        password = str(acc.get("password", "")).strip()

        if not uid or not password:
            print(f"[{idx}/{len(accounts)}] বাদ দেওয়া হয়েছে — UID বা পাসওয়ার্ড খালি।")
            continue

        ok, msg = join_guild(guild_id, uid, password, session)
        if ok:
            print(f"[{idx}/{len(accounts)}] UID: {uid} -> ✅ যুক্ত হয়েছে")
        else:
            print(f"[{idx}/{len(accounts)}] UID: {uid} -> ❌ ব্যর্থ ({msg})")

        time.sleep(0.5)

    print("=" * 50)
    print("[সমাপ্ত] সকল অ্যাকাউন্টের কাজ শেষ হয়েছে।")


if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে জয়েনিং প্রসেস শুরু করা
    worker_thread = threading.Thread(target=bot_worker)
    worker_thread.daemon = True
    worker_thread.start()

    # মূল থ্রেডে ওয়েব সার্ভার চালু রাখা (Render সার্ভিস যাতে স্লিপে না যায় বা এরর না দেয়)
    run_web_server()
