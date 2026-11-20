# ============================================================
#  digest.py  —  خلاصه روزانه خودکار
#  هر شب ساعت ۲۲ تهران ارسال می‌شود
# ============================================================

import json
import logging
import os
from datetime import datetime
import pytz
import jdatetime
from config import STATS_FILE, DIGEST_HOUR_TEHRAN, DIGEST_MIN_NEWS, TIMEZONE
from keywords import CATEGORIES

logger = logging.getLogger(__name__)

TEHRAN_TZ = pytz.timezone(TIMEZONE)

WEEKDAYS_FA = {
    0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه",
    3: "پنج‌شنبه", 4: "جمعه", 5: "شنبه", 6: "یکشنبه",
}
MONTHS_FA = [
    "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]


def _jalali_today() -> str:
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TEHRAN_TZ)
    jd  = jdatetime.datetime.fromgregorian(datetime=now)
    return f"{WEEKDAYS_FA[jd.weekday()]} {jd.day} {MONTHS_FA[jd.month]} {jd.year}"


def _bar(count: int, max_count: int, width: int = 10) -> str:
    """نوار پیشرفت یونیکدی."""
    if max_count == 0:
        return "░" * width
    filled = round(count / max_count * width)
    return "█" * filled + "░" * (width - filled)


def should_send_digest() -> bool:
    """آیا الان وقت ارسال خلاصه روزانه است؟"""
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TEHRAN_TZ)
    return now.hour == DIGEST_HOUR_TEHRAN


def build_digest_telegram() -> str | None:
    """
    متن خلاصه روزانه را برای تلگرام می‌سازد.
    اگر داده‌ای نباشد یا تعداد کافی نباشد، None برمی‌گردد.
    """
    if not os.path.exists(STATS_FILE):
        return None

    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            stats = json.load(f)
    except Exception as e:
        logger.error("❌ خطا در خواندن stats.json: %s", e)
        return None

    today_stats = stats.get("today", {})
    today_sent  = today_stats.get("sent", 0)
    by_cat      = today_stats.get("by_category", {})

    if today_sent < DIGEST_MIN_NEWS:
        logger.info("📊 تعداد اخبار امروز (%d) کمتر از حداقل — خلاصه ارسال نمی‌شود", today_sent)
        return None

    # محاسبه بیشترین دسته
    best_cat_key = max(by_cat, key=by_cat.get) if by_cat else None
    best_cat_label = ""
    best_cat_emoji = ""
    if best_cat_key and best_cat_key in CATEGORIES:
        best_cat_emoji = CATEGORIES[best_cat_key]["emoji"]
        best_cat_label = CATEGORIES[best_cat_key]["label"]

    max_cat_count = max(by_cat.values()) if by_cat else 1

    # ساخت نوارها
    bars = ""
    for cat_key, cat_data in CATEGORIES.items():
        count = by_cat.get(cat_key, 0)
        bar   = _bar(count, max_cat_count)
        bars += f"{cat_data['emoji']} {cat_data['label']}: {bar} {count}\n"

    jalali = _jalali_today()

    text = (
        f"📊 <b>خلاصه اخبار محیط زیست</b>\n"
        f"📅 {jalali}\n"
        f"{'─' * 30}\n\n"
        f"📰 <b>اخبار امروز:</b> {today_sent} خبر\n"
        f"✅ <b>منابع بررسی‌شده:</b> {today_stats.get('sources_checked', 0)}\n\n"
    )

    if best_cat_key:
        text += f"🏆 <b>بیشترین دسته:</b> {best_cat_emoji} {best_cat_label}\n\n"

    text += f"<b>آمار دسته‌بندی:</b>\n{bars}\n"
    text += f"<i>این پیام هر شب به‌طور خودکار ارسال می‌شود.</i>"

    return text


def build_digest_bale() -> str | None:
    """نسخه متن ساده خلاصه روزانه برای بله."""
    tg_text = build_digest_telegram()
    if not tg_text:
        return None

    # حذف HTML tags
    import re
    return re.sub(r"<[^>]+>", "", tg_text).strip()
