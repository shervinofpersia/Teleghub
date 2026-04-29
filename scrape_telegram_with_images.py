import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

# ========== تنظیمات ==========
CHANNELS = [
    "aishervin", "appxa", "appxa2", "IRNOTPHONE",
    "SlipNet_decode", "blackRay", "SparrK_VPN", "slipnet_chat",
    "SlipNet_app", "VConfing", "capcutchina"
]

MAX_POSTS = 5
OUTPUT_HTML = "index.html"
IMAGE_FOLDER = "images"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ========== توابع کمکی ==========
def fetch_channel_page(channel):
    url = f"https://t.me/s/{channel}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[!] خطا در دریافت {channel}: {e}")
        return None

def download_image(img_url, channel, post_idx, img_idx):
    try:
        ext = os.path.splitext(urlparse(img_url).path)[1]
        if not ext or len(ext) > 5:
            ext = ".jpg"
        safe_ch = re.sub(r'[^a-zA-Z0-9]', '_', channel)
        fname = f"{safe_ch}_post{post_idx}_img{img_idx}{ext}"
        fpath = os.path.join(IMAGE_FOLDER, fname)
        if not os.path.exists(fpath):
            resp = requests.get(img_url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            with open(fpath, "wb") as f:
                f.write(resp.content)
            print(f"      ✅ عکس دانلود شد: {fname}")
        return f"{IMAGE_FOLDER}/{fname}"
    except Exception as e:
        print(f"      ❌ خطا در دانلود عکس: {e}")
        return ""

def extract_posts(html, channel, channel_idx):
    soup = BeautifulSoup(html, "html.parser")
    posts = []
    for post_idx, div in enumerate(soup.select(".tgme_widget_message"), start=1):
        if post_idx > MAX_POSTS:
            break
        post = {"channel": channel, "text": "", "datetime": "", "images": [], "files": []}
        
        # متن
        txt_div = div.select_one(".tgme_widget_message_text")
        if txt_div:
            post["text"] = txt_div.get_text(strip=False)  # حفظ خطوط
        
        # زمان
        time_tag = div.select_one("time")
        if time_tag and time_tag.get("datetime"):
            dt = time_tag["datetime"].replace("T", " ").replace("+00:00", "")
            post["datetime"] = dt
        
        # تصاویر
        for img_idx, img in enumerate(div.select("img.tgme_widget_message_photo"), start=1):
            src = img.get("src")
            if src:
                local_path = download_image(src, channel, post_idx, img_idx)
                if local_path:
                    post["images"].append(local_path)
        
        # فایل‌های ضمیمه (PDF, APK, ZIP, ...)
        for file_link in div.select("a.tgme_widget_message_document"):
            url = file_link.get("href")
            if url:
                full_url = urljoin("https://t.me", url)
                file_name = file_link.get_text(strip=True) or "دانلود فایل"
                post["files"].append({"name": file_name, "url": full_url})
        
        posts.append(post)
    return posts

def generate_html(all_posts):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>آرشیو کانال‌های تلگرام با تصاویر و فایل‌ها</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #0a0c10;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
            color: #e0e0e0;
            direction: rtl;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{
            color: #2AABEE;
            border-right: 4px solid #2AABEE;
            padding-right: 15px;
            margin-bottom: 30px;
            font-weight: 500;
        }}
        .post {{
            background: #1a1d24;
            border-radius: 20px;
            margin-bottom: 30px;
            padding: 20px;
            transition: 0.2s;
            border: 1px solid #2a2e38;
        }}
        .post:hover {{ border-color: #2AABEE; }}
        .post-header {{
            display: flex;
            align-items: baseline;
            gap: 12px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}
        .channel {{
            background: #2AABEE20;
            color: #2AABEE;
            padding: 4px 12px;
            border-radius: 30px;
            font-weight: bold;
            font-size: 0.9rem;
        }}
        .datetime {{
            color: #888;
            font-size: 0.75rem;
        }}
        .text {{
            background: #0f1117;
            padding: 15px;
            border-radius: 16px;
            line-height: 1.7;
            white-space: pre-wrap;
            word-break: break-word;
            margin: 15px 0;
            font-size: 0.9rem;
            border-right: 3px solid #2AABEE;
        }}
        .images {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin: 15px 0;
        }}
        .images img {{
            max-width: 100%;
            max-height: 250px;
            border-radius: 12px;
            border: 1px solid #333;
            cursor: pointer;
            transition: 0.2s;
        }}
        .images img:hover {{ transform: scale(1.02); }}
        .files {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }}
        .file-link {{
            background: #2AABEE10;
            border: 1px solid #2AABEE;
            color: #2AABEE;
            padding: 6px 14px;
            border-radius: 30px;
            text-decoration: none;
            font-size: 0.8rem;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .file-link:hover {{
            background: #2AABEE;
            color: #000;
        }}
        .slipnet-url {{
            background: #0a0c10;
            padding: 8px 12px;
            border-radius: 12px;
            font-family: monospace;
            font-size: 12px;
            word-break: break-all;
            margin: 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .copy-btn {{
            background: #2AABEE20;
            border: none;
            color: #2AABEE;
            padding: 4px 12px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 11px;
            transition: 0.2s;
        }}
        .copy-btn:hover {{
            background: #2AABEE;
            color: #000;
        }}
        .toast {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #2AABEE;
            color: #000;
            padding: 8px 16px;
            border-radius: 40px;
            font-size: 13px;
            opacity: 0;
            transition: 0.2s;
            pointer-events: none;
            z-index: 999;
        }}
        footer {{
            text-align: center;
            margin-top: 40px;
            color: #555;
            font-size: 0.7rem;
        }}
        hr {{ border-color: #2a2e38; margin: 20px 0; }}
    </style>
</head>
<body>
<div class="container">
    <h1>📡 آخرین پست‌های کانال‌های تلگرام</h1>
"""
    for post in all_posts:
        html += f"""
    <div class="post">
        <div class="post-header">
            <span class="channel">@{post['channel']}</span>
            <span class="datetime">{post['datetime'] or 'نامشخص'}</span>
        </div>
"""
        if post["text"]:
            # فرار از کاراکترهای HTML
            text_safe = post["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # شناسایی لینک‌های slipnet و تبدیل به دکمه کپی
            slipnet_pattern = re.compile(r'(slipnet(?:-enc)?:\/\/[^\s<>"\'\[\]{}|\\^`]+)')
            parts = []
            last = 0
            for match in slipnet_pattern.finditer(text_safe):
                start, end = match.span()
                parts.append(text_safe[last:start])
                link = match.group(1)
                parts.append(f'<div class="slipnet-url"><span style="word-break:break-all;">{link}</span><button class="copy-btn" onclick="copyToClipboard(\'{link}\')">📋 کپی</button></div>')
                last = end
            parts.append(text_safe[last:])
            text_with_copy = ''.join(parts)
            html += f'        <div class="text">{text_with_copy}</div>\n'
        
        if post["images"]:
            html += '        <div class="images">\n'
            for img in post["images"]:
                html += f'            <img src="{img}" loading="lazy">\n'
            html += '        </div>\n'
        
        if post["files"]:
            html += '        <div class="files">\n'
            for f in post["files"]:
                html += f'            <a class="file-link" href="{f["url"]}" target="_blank">📎 {f["name"]}</a>\n'
            html += '        </div>\n'
        
        html += "    </div>\n"
    
    html += f"""
    <div id="toast" class="toast">✅ کپی شد!</div>
    <footer>آخرین به‌روزرسانی: {now_str} | تصاویر به صورت محلی در مخزن ذخیره شده‌اند.</footer>
</div>
<script>
    function copyToClipboard(text) {{
        navigator.clipboard.writeText(text).then(() => {{
            let toast = document.getElementById('toast');
            toast.style.opacity = '1';
            setTimeout(() => {{ toast.style.opacity = '0'; }}, 1500);
        }}).catch(() => {{
            alert('کپی دستی: ' + text);
        }});
    }}
</script>
</body>
</html>"""
    return html

def main():
    print(f"[{datetime.now()}] شروع اسکرپینگ و دانلود تصاویر...")
    all_posts = []
    for ch in CHANNELS:
        print(f"  -> دریافت کانال: {ch}")
        html = fetch_channel_page(ch)
        if html:
            posts = extract_posts(html, ch, 0)
            all_posts.extend(posts)
            print(f"      {len(posts)} پست استخراج شد")
        else:
            print(f"      خطا در دریافت")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(generate_html(all_posts))
    print(f"✅ فایل {OUTPUT_HTML} و تصاویر در پوشه {IMAGE_FOLDER}/ ساخته شدند.")

if __name__ == "__main__":
    main()
