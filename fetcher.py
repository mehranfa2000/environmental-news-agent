import requests
import feedparser
import time
import logging
from config import SOURCES, FETCH_TIMEOUT, MAX_CONCURRENT
from datetime import datetime

# تنظیمات هدر برای دور زدن فیلتر آی‌پی و بلاک شدن
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
}

def fetch_all_sources():
    """دریافت اخبار از تمامی منابع به روش همگام و پایدار"""
    all_entries = []
    stats = {
        "success": 0,
        "failed": 0,
        "details": []
    }

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting to fetch {len(SOURCES)} sources...")

    for source in SOURCES:
        name = source['name']
        url = source['url']
        group = source.get('group', 'عمومی')
        
        try:
            # استفاده از requests با غیرفعال کردن چک کردن SSL برای سایت‌های ایرانی
            response = requests.get(url, headers=HEADERS, timeout=FETCH_TIMEOUT, verify=False)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                if feed.entries:
                    source_entries = []
                    for entry in feed.entries:
                        # اضافه کردن متادیتای منبع به هر خبر
                        entry['source_name'] = name
                        entry['source_group'] = group
                        source_entries.append(entry)
                    
                    all_entries.extend(source_entries)
                    stats["success"] += 1
                    stats["details"].append({"name": name, "status": "ok", "count": len(feed.entries)})
                    print(f"✅ {name}: {len(feed.entries)} entries found.")
                else:
                    stats["failed"] += 1
                    stats["details"].append({"name": name, "status": "empty"})
                    print(f"⚠️ {name}: Feed is empty.")
            else:
                stats["failed"] += 1
                stats["details"].append({"name": name, "status": f"error_{response.status_code}"})
                print(f"❌ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            stats["failed"] += 1
            stats["details"].append({"name": name, "status": "exception"})
            print(f"❌ {name}: Connection failed.")

    print(f"\n[Summary] Success: {stats['success']} | Failed: {stats['failed']}")
    return all_entries, stats
