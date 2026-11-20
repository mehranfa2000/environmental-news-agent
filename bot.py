import json
import os
import hashlib
from datetime import datetime
import jdatetime
import pytz

from config import (
    DATA_DIR, NEWS_FILE, MAX_NEWS_STORED
)
from fetcher import fetch_all_sources
from analyzer import analyze_entries
from dedup import deduplicate
from messenger import send_all
from health import update_stats

IRAN_TZ = pytz.timezone("Asia/Tehran")


def get_item_id(item):
    """ساخت شناسه یکتا برای هر خبر"""
    content = f"{item.get('title', '')}|{item.get('link', '')}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()[:12]


def load_news():
    """بارگذاری اخبار ذخیره شده برای داشبورد"""
    if os.path.exists(NEWS_FILE):
        try:
            with open(NEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_news(news_list):
    """ذخیره اخبار برای داشبورد"""
    os.makedirs(DATA_DIR, exist_ok=True)

    # محدود کردن تعداد اخبار ذخیره شده
    if len(news_list) > MAX_NEWS_STORED:
        news_list = news_list[-MAX_NEWS_STORED:]

    try:
        with open(NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
        print(f"[Bot] news.json ذخیره شد: {len(news_list)} خبر")
    except Exception as e:
        print(f"[Bot] خطا در ذخیره news.json: {e}")


def format_dashboard_item(item):
    """فرمت یک خبر برای ذخیره در داشبورد"""
    now_utc = datetime.now(pytz.utc)
    now_iran = now_utc.astimezone(IRAN_TZ)
    jdt = jdatetime.datetime.fromgregorian(datetime=now_iran)

    WEEKDAYS_FA = {
        0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه",
        3: "پنج‌شنبه", 4: "جمعه", 5: "شنبه", 6: "یکشنبه",
    }

    return {
        "id": get_item_id(item),
        "title": item.get("title", ""),
        "link": item.get("link", ""),
        "source": item.get("source", "نامشخص"),
        "group": item.get("group", "عمومی"),
        "cat_key": item.get("cat_key", "pollution"),
        "cat_emoji": item.get("cat_emoji", "🌿"),
        "cat_label": item.get("cat_label", "محیط‌زیست"),
        "cat_color": item.get("cat_color", "#94a3b8"),
        "urgency": item.get("urgency", "low"),
        "date": f"{jdt.year}/{jdt.month:02d}/{jdt.day:02d}",
        "weekday": WEEKDAYS_FA.get(jdt.weekday(), ""),
        "time": f"{jdt.hour:02d}:{jdt.minute:02d}",
        "full": item.get("summary", ""),
        "score": item.get("score", 0),
    }


def run():
    """اجرای اصلی بات"""
    print("=" * 60)
    print("🌿 پایش اخبار محیط‌زیست — شروع اجرا")
    print(f"⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ===== مرحله ۱: دریافت اخبار =====
    print("\n📡 مرحله ۱: دریافت اخبار از منابع RSS")
    entries, fetch_stats = fetch_all_sources()

    if not entries:
        print("\n⚠️ هیچ خبری از منابع دریافت نشد.")
        # ذخیره آمار حتی اگر خبری نباشد
        update_stats(
            fetch_stats=fetch_stats,
            analyze_stats={"total_checked": 0, "passed": 0,
                           "filtered_blacklist": 0, "filtered_low_title": 0,
                           "filtered_low_total": 0, "filtered_other": 0},
            dedup_stats={"filtered_duplicate": 0, "unique_count": 0},
            send_stats={"total_sent": 0, "tg_sent": 0, "bale_sent": 0},
            sent_items=[]
        )
        print("\n✅ اجرا پایان یافت (بدون خبر جدید)")
        return

    # ===== مرحله ۲: تحلیل و فیلتر =====
    print("\n🔍 مرحله ۲: تحلیل و فیلتر سه‌لایه")
    approved, analyze_stats = analyze_entries(entries)

    if not approved:
        print("\n⚠️ هیچ خبری از فیلتر رد نشد.")
        update_stats(
            fetch_stats=fetch_stats,
            analyze_stats=analyze_stats,
            dedup_stats={"filtered_duplicate": 0, "unique_count": 0},
            send_stats={"total_sent": 0, "tg_sent": 0, "bale_sent": 0},
            sent_items=[]
        )
        print("\n✅ اجرا پایان یافت (همه فیلتر شدند)")
        return

    # ===== مرحله ۳: حذف تکراری =====
    print("\n🔁 مرحله ۳: حذف اخبار تکراری")
    unique_items, dedup_stats = deduplicate(approved)

    if not unique_items:
        print("\n⚠️ همه اخبار تکراری بودند.")
        update_stats(
            fetch_stats=fetch_stats,
            analyze_stats=analyze_stats,
            dedup_stats=dedup_stats,
            send_stats={"total_sent": 0, "tg_sent": 0, "bale_sent": 0},
            sent_items=[]
        )
        print("\n✅ اجرا پایان یافت (همه تکراری)")
        return

    # ===== مرحله ۴: ارسال =====
    print(f"\n📤 مرحله ۴: ارسال {len(unique_items)} خبر")
    sent_items, send_stats = send_all(unique_items)

    # ===== مرحله ۵: ذخیره در داشبورد =====
    print("\n💾 مرحله ۵: ذخیره در داشبورد")
    if sent_items:
        existing_news = load_news()
        new_dashboard_items = [format_dashboard_item(item) for item in sent_items]
        updated_news = existing_news + new_dashboard_items
        save_news(updated_news)

    # ===== مرحله ۶: آپدیت آمار =====
    print("\n📊 مرحله ۶: آپدیت آمار")
    update_stats(
        fetch_stats=fetch_stats,
        analyze_stats=analyze_stats,
        dedup_stats=dedup_stats,
        send_stats=send_stats,
        sent_items=sent_items
    )

    # ===== خلاصه نهایی =====
    print("\n" + "=" * 60)
    print("🌿 خلاصه اجرا:")
    print(f"  📡 منابع موفق: {fetch_stats.get('total_sources_ok', 0)}")
    print(f"  📰 اخبار دریافتی: {len(entries)}")
    print(f"  ✅ تایید شده: {analyze_stats.get('passed', 0)}")
    print(f"  🔁 تکراری: {dedup_stats.get('filtered_duplicate', 0)}")
    print(f"  📤 ارسال شده: {send_stats.get('total_sent', 0)}")
    print("=" * 60)
    print("✅ اجرا با موفقیت پایان یافت")


if __name__ == "__main__":
    run()
