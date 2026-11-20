import requests
import feedparser
import json
import os
from datetime import datetime
from sources import SOURCES
from config import (
    FETCH_TIMEOUT, HEADERS,
    HEALTH_FILE, DATA_DIR
)

# غیرفعال کردن هشدار SSL برای سایت‌های ایرانی
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_health():
    """بارگذاری فایل سلامت منابع"""
    if os.path.exists(HEALTH_FILE):
        try:
            with open(HEALTH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_health(health_data):
    """ذخیره فایل سلامت منابع"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(HEALTH_FILE, "w", encoding="utf-8") as f:
            json.dump(health_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Health] Save error: {e}")


def fetch_feed(source):
    """دریافت یک فید RSS با روش مطمئن"""
    name = source["name"]
    url = source["url"]
    group = source.get("group", "عمومی")

    for attempt in range(2):
        try:
            verify_ssl = (attempt == 0)

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=FETCH_TIMEOUT,
                verify=verify_ssl,
                allow_redirects=True
            )

            if response.status_code == 200:
                feed = feedparser.parse(response.content)

                if feed.entries:
                    entries = []
                    for entry in feed.entries:
                        entry["source_name"] = name
                        entry["source_group"] = group
                        entries.append(entry)

                    print(f"  ✅ {name}: {len(entries)} خبر")
                    return {
                        "name": name,
                        "group": group,
                        "status": "ok",
                        "count": len(entries),
                        "entries": entries
                    }
                else:
                    feed2 = feedparser.parse(url)
                    if feed2.entries:
                        entries = []
                        for entry in feed2.entries:
                            entry["source_name"] = name
                            entry["source_group"] = group
                            entries.append(entry)
                        print(f"  ✅ {name}: {len(entries)} خبر (direct)")
                        return {
                            "name": name,
                            "group": group,
                            "status": "ok",
                            "count": len(entries),
                            "entries": entries
                        }

                    print(f"  ⚠️ {name}: فید خالی")
                    return {
                        "name": name,
                        "group": group,
                        "status": "empty",
                        "count": 0,
                        "entries": []
                    }

            else:
                if attempt == 1:
                    print(f"  ❌ {name}: HTTP {response.status_code}")
                    return {
                        "name": name,
                        "group": group,
                        "status": f"http_{response.status_code}",
                        "count": 0,
                        "entries": []
                    }

        except requests.exceptions.Timeout:
            if attempt == 1:
                print(f"  ⏱️ {name}: Timeout")
                return {
                    "name": name,
                    "group": group,
                    "status": "timeout",
                    "count": 0,
                    "entries": []
                }

        except requests.exceptions.SSLError:
            continue

        except Exception as e:
            if attempt == 1:
                print(f"  ❌ {name}: {type(e).__name__}")
                return {
                    "name": name,
                    "group": group,
                    "status": "error",
                    "count": 0,
                    "entries": []
                }

    return {
        "name": name,
        "group": group,
        "status": "error",
        "count": 0,
        "entries": []
    }


def fetch_all_sources():
    """دریافت اخبار از تمامی منابع"""
    print(f"\n[Fetcher] شروع دریافت از {len(SOURCES)} منبع...")
    print(f"[Fetcher] زمان شروع: {datetime.now().strftime('%H:%M:%S')}\n")

    all_entries = []
    health_data = load_health()

    source_ok = 0
    source_fail = 0
    source_empty = 0

    for i, source in enumerate(SOURCES, 1):
        name = source["name"]
        print(f"[{i}/{len(SOURCES)}] {name}")

        result = fetch_feed(source)

        health_data[name] = {
            "status": result["status"],
            "count": result["count"],
            "group": result.get("group", "عمومی"),
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if result["status"] == "ok":
            all_entries.extend(result["entries"])
            source_ok += 1
        elif result["status"] == "empty":
            source_empty += 1
        else:
            source_fail += 1

    save_health(health_data)

    print(f"\n[Fetcher] نتیجه:")
    print(f"  ✅ موفق: {source_ok} منبع")
    print(f"  ⚠️ خالی: {source_empty} منبع")
    print(f"  ❌ ناموفق: {source_fail} منبع")
    print(f"  📰 کل اخبار دریافتی: {len(all_entries)}")

    stats = {
        "total_sources_ok": source_ok,
        "total_sources_fail": source_fail + source_empty,
        "total_sources_empty": source_empty,
    }

    return all_entries, stats
