import asyncio
import random
import json
import csv
import os
import re
from datetime import datetime
from dateutil import parser
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()
TARGET_USER = os.getenv('THREADS_TARGET_USERNAME', 'ginoinoo')
TARGET_URL = f"https://www.threads.net/@ginoinoo"
MAX_POSTS = 30 # Sesuai target evaluasi 20-50 unggahan

# --- DATA CLEANING FUNCTIONS ---
def clean_text(text):
    if not text:
        return ""
    # Hapus line break ganda dan spasi berlebih
    text = re.sub(r'\n+', '\n', text)
    return re.sub(r'\s+', ' ', text).strip()

def parse_interaction(metric_str):
    if not metric_str:
        return 0
    metric_str = metric_str.lower().replace(',', '.')
    try:
        if 'k' in metric_str or 'rb' in metric_str:
            num = float(re.sub(r'[^\d.]', '', metric_str))
            return int(num * 1000)
        elif 'm' in metric_str or 'jt' in metric_str:
            num = float(re.sub(r'[^\d.]', '', metric_str))
            return int(num * 1000000)
        else:
            return int(re.sub(r'\D', '', metric_str))
    except ValueError:
        return 0

def format_timestamp(time_str):
    if not time_str:
        return None
    try:
        # Threads sering menggunakan tag <time datetime="..."> yang sudah baku
        # Jika mendapatkan string ISO, langsung di-parse
        dt = parser.isoparse(time_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        # Fallback jika waktu saat ini (untuk format "2j", "1m")
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# --- MAIN SCRAPER LOPIC ---
async def scrape_threads():
    async with async_playwright() as p:
        # A. Setup & Navigasi Peramban
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="id-ID"
        )
        page = await context.new_page()
        
        print(f"Membuka halaman: {TARGET_URL}")
        await page.goto(TARGET_URL, wait_until="networkidle")
        
        scraped_data = []
        seen_posts = set()
        scroll_attempts = 0
        max_scrolls = 20 # B. Safety Limit untuk mencegah infinite loop

        # B. Penanganan Konten Dinamis & Infinite Scroll
        while len(scraped_data) < MAX_POSTS and scroll_attempts < max_scrolls:
            # Wait Strategy: Tunggu hingga elemen container post muncul
            # Catatan: Class pada SPA Meta bersifat dinamis, gunakan role atau penanda umum.
            await page.wait_for_selector('div[data-pressable-container="true"], article', timeout=10000)
            
            posts = await page.query_selector_all('div[data-pressable-container="true"], article')
            
            for post in posts:
                if len(scraped_data) >= MAX_POSTS:
                    break
                    
                try:
                    # Ekstraksi URL & ID
                    url_el = await post.query_selector('a[href*="/post/"]')
                    post_url = await url_el.get_attribute('href') if url_el else None
                    if not post_url or post_url in seen_posts:
                        continue
                    
                    full_url = f"https://www.threads.net{post_url}"
                    seen_posts.add(post_url)
                    
                    # C. Ekstraksi Atribut
                    # Ekstrak Username
                    username = TARGET_USER 
                    
                    # Ekstrak Timestamp (Cari atribut datetime pada tag time)
                    time_el = await post.query_selector('time')
                    raw_time = await time_el.get_attribute('datetime') if time_el else None
                    
                    # Ekstrak Konten Teks
                    # div[dir="auto"] sering digunakan Meta untuk teks konten
                    text_els = await post.query_selector_all('span[dir="auto"], div[dir="auto"]')
                    raw_text = " ".join([await el.inner_text() for el in text_els])
                    
                    # Ekstrak Metrik (Like/Reply)
                    metrics_el = await post.query_selector_all('div[role="button"]:has-text("suka"), div[role="button"]:has-text("likes")')
                    raw_likes = await metrics_el[0].inner_text() if metrics_el else "0"

                    # Data Cleaning Eksekusi
                    scraped_data.append({
                        "username": username,
                        "timestamp": format_timestamp(raw_time),
                        "content": clean_text(raw_text),
                        "likes": parse_interaction(raw_likes),
                        "post_url": full_url
                    })
                    print(f"Berhasil ekstrak: {full_url} | Likes: {parse_interaction(raw_likes)}")
                    
                except Exception as e:
                    continue # Skip post yang error strukturnya agar loop tidak terhenti

            # Simulasi Scroll Bertahap & Jeda Acak
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            delay = random.uniform(2.5, 5.0)
            print(f"Scrolling... Menunggu {delay:.2f} detik.")
            await asyncio.sleep(delay)
            scroll_attempts += 1

        await browser.close()
        return scraped_data

def save_data(data):
    if not os.path.exists('data'):
        os.makedirs('data')
        
    # D. Penyimpanan JSON (UTF-8)
    json_path = 'data/threads_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    # D. Penyimpanan CSV (UTF-8)
    csv_path = 'data/threads_data.csv'
    if data:
        keys = data[0].keys()
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
            
    print(f"\nProses selesai. {len(data)} data disimpan ke {json_path} dan {csv_path}")

if __name__ == "__main__":
    data = asyncio.run(scrape_threads())
    save_data(data)