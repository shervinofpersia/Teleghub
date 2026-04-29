import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

# ========== تنظیمات ==========
CHANNELS = [
    "xgvpn", "appxa", "appxa2", "IRNOTPHONE", "IRAN_V2RAY1",
    "SlipNet_decode", "blackRay", "SparrK_VPN", "slipnet_chat",
    "SlipNet_app", "VConfing", "capcutchina"
]

MAX_POSTS = 5
OUTPUT_HTML = "index.html"
IMAGE_FOLDER = "images"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ایجاد پوشه تصاویر اگر وجود ندارد
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ========== توابع ==========
def fetch_channel_page(channel: str) -> str | None:
    url = f"https://t.me/s/{channel}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[!] خطا در دریافت {channel}: {e}")
        return None

def download_image(img_url: str, channel: str, post_index: int, img_index: int) -> str:
    """دانلود عکس و ذخیره در پوشه images، برگرداندن مسیر نسبی"""
    try:
        # استخراج پسوند (مثلاً .jpg, .png)
        ext = os.path.splitext(urlparse(img_url).path)[1]
        if not ext or len(ext) > 5:
            ext = ".jpg"
        # نام فایل: کانال_پست_شماره_عکس.ext
        safe_channel = re.sub(r'[^a-zA-Z0-9]', '_', channel)
        filename = f"{safe_channel}_post{post_index}_img{img_index}{ext}"
        filepath = os.path.join(IMAGE_FOLDER, filename)
        
        # فقط اگه فایل وجود ندارد دانلود کن
        if os.path.exists(filepath):
            return f"{IMAGE_FOLDER}/{filename}"
        
        resp = requests.get(img_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"      ✅ دانلود عکس: {filename}")
        return f"{IMAGE_FOLDER}/{filename}"
    except Exception as e:
        print(f"      ❌ خطا در دانلود عکس {img_url}: {e}")
        return ""  # برگشت مسیر خالی در صورت خطا

def extract_posts(html: str, channel: str, channel_index: int) -> list:
    soup = BeautifulSoup(html, "html.parser")
    posts = []
    message_divs = soup.select(".tgme_widget_message")
    
    for post_idx, div in enumerate(message_divs[:MAX_POSTS], start=1):
        post = {"channel": channel}
        
        # متن پست
        text_elem = div.select_one(".tgme_widget_message_text")
        post["text"] = text_elem.get_text(strip=True) if text_elem else ""
        
        # زمان
        time_elem = div.select_one("time")
        post["datetime"] = time_elem.get("datetime", "") if time_elem else ""
        
        # تصاویر - دانلود و ذخیره محلی
        images_local = []
        img_tags = div.select("img.tgme_widget_message_photo")
        for img_idx, img in enumerate(img_tags, start=1):
            src = img.get("src")
            if src:
                local_path = download_image(src, channel, post_idx, img_idx)
                if local_path:
                    images_local.append(local_path)
        post["images_local"] = images_local
        
        # فایل‌های ضمیمه (لینک مستقیم - قابل دانلود در مرورگر)
        files = []
        file_links = div.select("a.tgme_widget_message_document")
        for a in file_links:
            href = a.get("href")
            if href:
                full_url = urljoin("https://t.me", href)
                file_name = a.get_text(strip=True) or "دانلود فایل"
                files.append({"name": file_name, "url": full_url})
        post["files"] = files
        
        posts.append(post)
    
    return posts

def generate_html(all_posts: list) -> str:
    html = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>آرشیو کانال‌های تلگرام با تصاویر محلی</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #121212;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
            color: #e0e0e0;
            direction: rtl;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #2AABEE; border-right: 4px solid #2AABEE; padding-right: 15px; margin-bottom: 30px; }
        .post {
            background: #1e1e1e;
            border-radius: 12px;
            margin-bottom: 30px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .channel { color: #2AABEE; font-weight: bold; font-size: 1.2rem; }
        .datetime { color: #888; font-size: 0.8rem; margin-right: 15px; }
        .text {
            margin: 15px 0;
            line-height: 1.6;
            background: #0a0a0a;
            padding: 12px;
            border-radius: 8px;
            border-right: 2px solid #2AABEE;
        }
        .images { display: flex; flex-wrap: wrap; gap: 10px; margin: 15px 0; }
        .images img { max-width: 100%; max-height: 300px; border-radius: 8px; border: 1px solid #333; }
        .files { margin-top: 15px; display: flex; flex-wrap: wrap; gap: 10px; }
        .files a {
            background: #2AABEE20; border: 1px solid #2AABEE; color: #2AABEE;
            padding: 8px 15px; border-radius: 20px; text-decoration: none; font-size: 0.85rem;
        }
        .files a:hover { background: #2AABEE; color: #121212; }
        footer { text-align: center; margin-top: 40px; color: #555; font-size: 0.8rem; }
    </style>
</head>
<body>
<div class="container">
    <h1>📸 آخرین پست‌های کانال‌های تلگرام (با تصاویر محلی)</h1>
"""
    for post in all_posts:
        pub_date = post["datetime"].replace("T", " ").replace("+00:00", "") if post["datetime"] else "نامشخص"
        html += f"""
    <div class="post">
        <div>
            <span class="channel">@{post['channel']}</span>
            <span class="datetime">{pub_date}</span>
        </div>
"""
        if post["text"]:
            html += f"""        <div class="text">{post["text"].replace("<", "&lt;").replace(">", "&gt;")}</div>\n"""
        if post["images_local"]:
            html += '        <div class="images">\n'
            for img_path in post["images_local"]:
                html += f'            <img src="{img_path}" loading="lazy">\n'
            html += '        </div>\n'
        if post["files"]:
            html += '        <div class="files">\n'
            for f in post["files"]:
                html += f'            <a href="{f["url"]}" target="_blank">📎 {f["name"]}</a>\n'
            html += '        </div>\n'
        html += "    </div>\n"
    
    html += f"""
    <footer>
        آخرین به‌روزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | تصاویر به صورت محلی در مخزن ذخیره شده‌اند.
    </footer>
</div>
</body>
</html>"""
    return html

def main():
    print(f"[{datetime.now()}] شروع اسکرپینگ و دانلود تصاویر...")
    all_posts = []
    
    for ch_idx, ch in enumerate(CHANNELS, start=1):
        print(f"  -> دریافت کانال: {ch}")
        html = fetch_channel_page(ch)
        if html:
            posts = extract_posts(html, ch, ch_idx)
            all_posts.extend(posts)
            print(f"      {len(posts)} پست استخراج شد")
        else:
            print(f"      خطا در دریافت")
    
    final_html = generate_html(all_posts)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"✅ فایل {OUTPUT_HTML} و تصاویر در پوشه {IMAGE_FOLDER}/ ساخته شدند.")

if __name__ == "__main__":
    main()
