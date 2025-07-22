import asyncio
import aiohttp
import aiofiles
import itertools
import time
import os
import threading
import pickle
import csv
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tqdm import tqdm
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import requests

# --- CONFIG ---
ROBLOX_API_URL = "https://users.roblox.com/v1/users/search"
SESSION_FILE = "roblox_cookies.pkl"
CACHE_FILE = "variant_cache.pkl"
RESULTS_FILE = "roblox_users.csv"
RATE_LIMIT_DELAY = 1.5
RETRY_DELAY = 5
MAX_RETRIES = 3
THREAD_COUNT = 20
CONCURRENT_WORKERS = 15
SAVE_INTERVAL = 5
PROXY = None  # e.g., "http://proxy.com:port"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("RobloxScraper")

# --- CHARACTER SUBSTITUTIONS ---
CHAR_SUBS = {
    'a': ['a', 'A', '@', '4', '^'], 'A': ['a', 'A', '@', '4', '^'],
    'b': ['b', 'B', '8'], 'B': ['b', 'B', '8'],
    'c': ['c', 'C', '(', '{'], 'C': ['c', 'C', '(', '{'],
    'd': ['d', 'D', ')'], 'D': ['d', 'D', ')'],
    'e': ['e', 'E', '3'], 'E': ['e', 'E', '3'],
    'f': ['f', 'F'], 'F': ['f', 'F'],
    'g': ['g', 'G', '9'], 'G': ['g', 'G', '9'],
    'h': ['h', 'H', '#'], 'H': ['h', 'H', '#'],
    'i': ['i', 'I', '1', '!'], 'I': ['i', 'I', '1', '!'],
    'j': ['j', 'J'], 'J': ['j', 'J'],
    'k': ['k', 'K'], 'K': ['k', 'K'],
    'l': ['l', 'L', '|'], 'L': ['l', 'L', '|'],
    'm': ['m', 'M'], 'M': ['m', 'M'],
    'n': ['n', 'N'], 'N': ['n', 'N'],
    'o': ['o', 'O', '0'], 'O': ['o', 'O', '0'],
    'p': ['p', 'P'], 'P': ['p', 'P'],
    'q': ['q', 'Q'], 'Q': ['q', 'Q'],
    'r': ['r', 'R'], 'R': ['r', 'R'],
    's': ['s', 'S', '5', '$'], 'S': ['s', 'S', '5', '$'],
    't': ['t', 'T', '7'], 'T': ['t', 'T', '7'],
    'u': ['u', 'U'], 'U': ['u', 'U'],
    'v': ['v', 'V'], 'V': ['v', 'V'],
    'w': ['w', 'W'], 'W': ['w', 'W'],
    'x': ['x', 'X'], 'X': ['x', 'X'],
    'y': ['y', 'Y'], 'Y': ['y', 'Y'],
    'z': ['z', 'Z'], 'Z': ['z', 'Z'],
    '0': ['0', 'O', 'o'], '1': ['1', 'I', 'i'], '2': ['2', 'Z', 'z'],
    '3': ['3', 'E', 'e'], '4': ['4', 'A', 'a'], '5': ['5', 'S', 's'],
    '6': ['6', 'G', 'g'], '7': ['7', 'T', 't'], '8': ['8', 'B', 'b'],
    '9': ['9', 'g', 'q']
}

# --- CACHE ---
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return set()
    return set()

def save_cache(cache):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

# --- COOKIES ---
def roblox_login():
    options = Options()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.roblox.com/login")
    messagebox.showinfo("Login", "Log in manually in the browser. Click OK when done.")
    cookies = driver.get_cookies()
    with open(SESSION_FILE, "wb") as f:
        pickle.dump(cookies, f)
    driver.quit()

def load_cookies_to_session(session):
    if not os.path.exists(SESSION_FILE):
        roblox_login()
    with open(SESSION_FILE, "rb") as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

# --- VARIANT GENERATOR ---
def generate_variants(base):
    variants = set()
    pools = [CHAR_SUBS.get(ch.lower(), [ch]) for ch in base]
    base_variants = set(''.join(p) for p in itertools.product(*pools))
    from string import ascii_lowercase, digits
    chars = ascii_lowercase + digits + "_"
    for variant in base_variants:
        variants.add(variant)
        variants.add(variant + base)
        variants.add(base + variant)
    return variants

# --- ASYNC API CALL ---
async def get_session(proxy=None):
    connector = aiohttp.TCPConnector(limit=None)
    timeout = aiohttp.ClientTimeout(total=30)
    if proxy:
        return aiohttp.ClientSession(connector=connector, timeout=timeout, trust_env=True, proxy=proxy)
    else:
        return aiohttp.ClientSession(connector=connector, timeout=timeout)

async def search_user(session, keyword, variant):
    try:
        async with session.get(ROBLOX_API_URL, params={"keyword": variant, "limit": 50}) as resp:
            if resp.status == 429:
                return "RATE_LIMIT"
            if resp.status != 200:
                return None
            data = await resp.json()
            found = []
            for user in data.get('data', []):
                username = user.get('name', '')
                display_name = user.get('displayName', '')
                if keyword.lower() in username.lower() or keyword.lower() in display_name.lower():
                    profile_url = f"https://www.roblox.com/users/{user['id']}/profile"
                    found.append((user['id'], username, profile_url))
            return found
    except Exception:
        return None

# --- SMART SCHEDULER ---
async def smart_scheduler(variants, keyword, gui_state):
    cache = load_cache()
    found_users = set()
    buffer = []
    total_found = 0
    variants = list(variants - cache)
    total = len(variants)
    completed = 0
    start_time = time.time()

    worker_batches = [variants[i:i+CONCURRENT_WORKERS] for i in range(0, total, CONCURRENT_WORKERS)]
    for batch in worker_batches:
        tasks = []
        async with await get_session(PROXY) as session:
            for variant in batch:
                tasks.append(search_user(session, keyword, variant))
            results = await asyncio.gather(*tasks)

            for i, result in enumerate(results):
                completed += 1
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                remaining = total - completed
                eta = remaining / rate if rate > 0 else 0
                eta_d = int(eta // 86400)
                eta_h = int((eta % 86400) // 3600)
                eta_m = int((eta % 3600) // 60)
                eta_s = int(eta % 60)

                percent = (completed / total) * 100
                finish_time = time.localtime(time.time() + eta)
                finish_str = time.strftime('%Y-%m-%d %H:%M:%S', finish_time)
                gui_state['progress_var'].set(percent)
                gui_state['progress_label'].config(
                    text=f"Progress: {completed}/{total} ({percent:.2f}%) | ETA: {eta_d}d {eta_h}h {eta_m}m {eta_s}s | Ends: {finish_str}"
                )

                variant = batch[i]
                if result and result != "RATE_LIMIT":
                    for uid, name, url in result:
                        if uid not in found_users:
                            found_users.add(uid)
                            buffer.append((name, uid, url))
                    cache.add(variant)

        await asyncio.sleep(SAVE_INTERVAL)

    save_cache(cache)
    with open(RESULTS_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Username", "User ID", "Profile URL"])
        for name, uid, url in buffer:
            writer.writerow([name, uid, url])

    messagebox.showinfo("Done", f"Found {len(buffer)} users.")

# --- GUI ---
def launch_gui():
    root = tk.Tk()
    root.title("Roblox Ultimate Scraper")
    root.geometry("500x250")

    tk.Label(root, text="Enter base word:").pack(pady=5)
    entry = tk.Entry(root, width=40)
    entry.pack(pady=5)

    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, maximum=100, variable=progress_var)
    progress_bar.pack(fill="x", padx=10, pady=10)

    progress_label = tk.Label(root, text="Progress: 0/0 (0.00%) | ETA: 0d 0h 0m 0s | Ends: 0000-00-00 00:00:00")
    progress_label.pack()

    def start():
        base = entry.get().strip()
        if not base:
            return messagebox.showerror("Error", "Please enter a base word")
        threading.Thread(target=run_async_scheduler, args=(base, progress_var, progress_label), daemon=True).start()

    tk.Button(root, text="Start Search", command=start).pack(pady=5)
    root.mainloop()

def run_async_scheduler(base, progress_var, progress_label):
    asyncio.run(wrapper(base, progress_var, progress_label))

def wrapper(base, progress_var, progress_label):
    session = requests.Session()
    load_cookies_to_session(session)
    variants = generate_variants(base)
    gui_state = {
        'progress_var': progress_var,
        'progress_label': progress_label
    }
    return smart_scheduler(variants, base, gui_state)

if __name__ == "__main__":
    launch_gui()
