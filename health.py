import json
import os
import jdatetime
import pytz
from datetime import datetime
from config import (
    HEALTH_FILE, STATS_FILE, DATA_DIR
)

IRAN_TZ = pytz.timezone("Asia/Tehran")


def get_jalali_now():
    """دریافت تاریخ و زمان کنونی به شمسی"""
    now_utc = datetime.now(pytz.utc)
    now_iran = now_utc.astimezone(IRAN_TZ)
    jdt = jdatetime.datetime.fromgregorian(datetime=now_iran)
    date_str = f"{jdt.year}/{jdt.month:02d}/{jdt.day:02d}"
    time_str = f"{jdt.hour:02d}:{jdt.minute:02d}"
    today_key = f"{jdt.year}{jdt.month:02d}{jdt.day:02d}"
    hour_key = str(jdt.hour)
    return date_str, time_str, today_key, hour_key


def load_stats():
    """بارگذاری فایل آمار"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return build_empty_stats()


def build_empty_stats():
    """ساخت ساختار خالی آمار"""
    return {
        "total_sent": 0,
        "total_checked": 0,
        "filtered_irrelevant": 0,
        "filtered_duplicate": 0,
        "total_sources_ok": 0,
        "total_sources_fail": 0,
        "run_count": 0,
        "last_run": "",
        "by_source": {},
        "by_category": {},
        "by_group": {},
        "hourly": {},
        "today_key": "",
        "today": {
            "sent": 0,
            "checked": 0,
            "filtered_irrelevant": 0,
            "filtered_duplicate": 0,
        },
        "daily_top": {},
        "health": {},
    }


def save_stats(stats):
    """ذخیره فایل آمار"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Health] Stats save error: {e}")


def load_health():
    """بارگذاری فایل سلامت منابع"""
    if os.path.exists(HEALTH_FILE):
        try:
            with open(HEALTH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def classify_source_status(status):
    """تبدیل وضعیت منبع به دسته‌بندی داشبورد"""
    if status == "ok":
        return "healthy"
    elif status == "timeout":
        return "slow"
    elif status == "empty":
        return "unstable"
    else:
        return "inactive"


def update_stats(
    fetch_stats,
    analyze_stats,
    dedup_stats,
    send_stats,
    sent_items
):
    """
    آپدیت کامل فایل آمار بعد از هر اجرا
    """
    date_str, time_str, today_key, hour_key = get_jalali_now()

    # بارگذاری آمار قبلی
    stats = load_stats()

    # ریست آمار روزانه اگر روز جدید باشد
    if stats.get("today_key") != today_key:
        stats["today_key"] = today_key
        stats["today"] = {
            "sent": 0,
            "checked": 0,
            "filtered_irrelevant": 0,
            "filtered_duplicate": 0,
        }

    # آپدیت آمار کلی
    total_filtered_irrelevant = (
        analyze_stats.get("filtered_blacklist", 0) +
        analyze_stats.get("filtered_low_title", 0) +
        analyze_stats.get("filtered_low_total", 0) +
        analyze_stats.get("filtered_other", 0)
    )

    stats["total_sent"] += send_stats.get("total_sent", 0)
    stats["total_checked"] += analyze_stats.get("total_checked", 0)
    stats["filtered_irrelevant"] += total_filtered_irrelevant
    stats["filtered_duplicate"] += dedup_stats.get("filtered_duplicate", 0)
    stats["total_sources_ok"] = fetch_stats.get("total_sources_ok", 0)
    stats["total_sources_fail"] = fetch_stats.get("total_sources_fail", 0)
    stats["run_count"] = stats.get("run_count", 0) + 1
    stats["last_run"] = f"{date_str} {time_str}"

    # آپدیت آمار امروز
    stats["today"]["sent"] += send_stats.get("total_sent", 0)
    stats["today"]["checked"] += analyze_stats.get("total_checked", 0)
    stats["today"]["filtered_irrelevant"] += total_filtered_irrelevant
    stats["today"]["filtered_duplicate"] += dedup_stats.get("filtered_duplicate", 0)

    # آپدیت آمار ساعتی
    if hour_key not in stats["hourly"]:
        stats["hourly"][hour_key] = 0
    stats["hourly"][hour_key] += send_stats.get("total_sent", 0)

    # آپدیت آمار بر اساس منبع، دسته و گروه
    for item in sent_items:
        source = item.get("source", "نامشخص")
        cat_key = item.get("cat_key", "pollution")
        group = item.get("group", "عمومی")

        # آمار منبع
        if source not in stats["by_source"]:
            stats["by_source"][source] = 0
        stats["by_source"][source] += 1

        # آمار دسته
        if cat_key not in stats["by_category"]:
            stats["by_category"][cat_key] = 0
        stats["by_category"][cat_key] += 1

        # آمار گروه
        if group not in stats["by_group"]:
            stats["by_group"][group] = 0
        stats["by_group"][group] += 1

    # آپدیت اطلاعات سلامت منابع
    health_raw = load_health()
    health_summary = {}

    for source_name, info in health_raw.items():
        status = info.get("status", "error")
        health_summary[source_name] = {
            "status": classify_source_status(status),
            "raw_status": status,
            "count": info.get("count", 0),
            "group": info.get("group", "عمومی"),
            "last_check": info.get("last_check", ""),
        }

    stats["health"] = health_summary

    # ذخیره
    save_stats(stats)

    print(f"\n[Health] آمار آپدیت شد: {date_str} {time_str}")
    print(f"  📊 کل اجراها: {stats['run_count']}")
    print(f"  📤 کل ارسالی: {stats['total_sent']}")
    print(f"  📰 کل بررسی شده: {stats['total_checked']}")

    return stats
