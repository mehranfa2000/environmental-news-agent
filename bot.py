# ============================================================
#  bot.py  —  موتور اصلی و هماهنگ‌کننده
#  تمام ماژول‌ها را با هم اجرا می‌کند
# ============================================================

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
import pytz
import jdatetime

from config import (
    STATS_FILE, DATA_DIR, TIMEZONE,
    SEND_RETRY_BASE_DELAY
)
from sources       import SOURCES, GROUP_LABELS
from keywords      import CATEGORIES
from fetcher       import fetch_all
from analyzer      import analyze_batch
from dedup         import DedupManager
from formatter     import format_telegram, format_bale
from messenger     import send_telegram, send_bale, MessageQueue
from digest        import should_send_digest, build_digest_telegram, build_digest_bale
from health        import HealthMonitor

# ── لاگ ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("bot")

TEHRAN_TZ = pytz.timezone(TIMEZONE)


def _jalali_stamp() -> str:
    now = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TEHRAN_TZ)
    jd  = jdatetime.datetime.fromgregorian(datetime=now)
    return jd.strftime("%Y-%m-%d %H:%M")


def _load_stats() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "total_sent":           0,
        "total_checked":        0,
        "filtered_irrelevant":  0,
        "filtered_duplicate":   0,
        "filtered_blacklist":   0,
        "total_sources_checked":0,
        "total_sources_failed": 0,
        "run_count":            0,
        "last_run":             None,
        "by_source":            {},
        "by_category":          {},
        "by_source_group":      {},
        "hourly_activity":      {},
        "daily_top_category":   {},
        "today":                {"sent": 0, "by_category": {}, "sources_checked": 0},
        "health_summary":       {},
    }


def _save_stats(stats: dict):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("❌ خطا در ذخیره stats.json: %s", e)


def _reset_today_if_needed(stats: dict) -> dict:
    """اگر روز جدید است، آمار روزانه را ریست می‌کند."""
    now  = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TEHRAN_TZ)
    jd   = jdatetime.datetime.fromgregorian(datetime=now)
    today_key = jd.strftime("%Y-%m-%d")

    if stats.get("today_key") != today_key:
        logger.info("🌅 روز جدید — ریست آمار روزانه")
        stats["today"]     = {"sent": 0, "by_category": {}, "sources_checked": 0}
        stats["today_key"] = today_key
    return stats


def main():
    logger.info("=" * 60)
    logger.info("🌿 بات اخبار محیط زیست — شروع اجرا")
    logger.info("⏰ %s", _jalali_stamp())
    logger.info("=" * 60)

    # ── خواندن توکن‌ها از محیط ───────────────────────────────
    TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TG_CHANNEL = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    BA_TOKEN   = os.environ.get("BALE_BOT_TOKEN", "")
    BA_CHANNEL = os.environ.get("BALE_CHANNEL_ID", "")

    if not TG_TOKEN or not TG_CHANNEL:
        logger.error("❌ TELEGRAM_BOT_TOKEN یا TELEGRAM_CHANNEL_ID تنظیم نشده!")
        sys.exit(1)

    # ── بارگذاری ماژول‌ها ────────────────────────────────────
    stats   = _load_stats()
    stats   = _reset_today_if_needed(stats)
    dedup   = DedupManager()
    health  = HealthMonitor()
    queue   = MessageQueue()

    # ── ابتدا: ارسال مجدد پیام‌های صف ────────────────────────
    if TG_TOKEN and BA_TOKEN:
        retried = queue.retry_all(TG_TOKEN, TG_CHANNEL, BA_TOKEN, BA_CHANNEL)
        if retried:
            logger.info("✅ %d پیام از صف ارسال شد", retried)

    # ── خلاصه روزانه ─────────────────────────────────────────
    if should_send_digest():
        logger.info("📊 ارسال خلاصه روزانه...")
        digest_tg   = build_digest_telegram()
        digest_bale = build_digest_bale()
        if digest_tg:
            send_telegram(TG_TOKEN, TG_CHANNEL, {"text": digest_tg, "parse_mode": "HTML"})
        if digest_bale and BA_TOKEN and BA_CHANNEL:
            send_bale(BA_TOKEN, BA_CHANNEL, digest_bale)

    # ── فیلتر منابع فعال ─────────────────────────────────────
    active_sources = health.get_active_sources(SOURCES)
    logger.info("📡 منابع فعال: %d از %d", len(active_sources), len(SOURCES))

    # ── دریافت موازی ─────────────────────────────────────────
    t_fetch_start = time.monotonic()
    fetch_results = fetch_all(active_sources)
    t_fetch_end   = time.monotonic()
    logger.info("⚡ زمان دریافت: %.1f ثانیه", t_fetch_end - t_fetch_start)

    # ── به‌روزرسانی سلامت منابع ──────────────────────────────
    health.update_batch(fetch_results)

    # ── جمع‌آوری همه آیتم‌ها ─────────────────────────────────
    all_items = []
    for result in fetch_results:
        all_items.extend(result["items"])

    logger.info("📰 کل آیتم دریافت‌شده: %d", len(all_items))

    # ── تحلیل (سه‌لایه فیلتر + دسته‌بندی) ───────────────────
    analyzed = analyze_batch(all_items)
    filtered_irrelevant = len(all_items) - len(analyzed)
    logger.info("✅ بعد از فیلتر: %d | رد شده: %d", len(analyzed), filtered_irrelevant)

    # ── حذف تکراری ───────────────────────────────────────────
    new_items, dup_count = dedup.filter_new(analyzed)
    logger.info("🆕 جدید: %d | تکراری: %d", len(new_items), dup_count)

    # ── ارسال ────────────────────────────────────────────────
    sent_count = 0
    now_hour   = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TEHRAN_TZ).hour

    for item in new_items:
        source   = item["source"]
        group    = item["group"]
        cat_key  = item["category_key"]

        # قالب‌بندی
        tg_msg   = format_telegram(item)
        bale_txt = format_bale(item)

        # ارسال تلگرام
        tg_ok = send_telegram(TG_TOKEN, TG_CHANNEL, tg_msg)
        if not tg_ok:
            queue.add("telegram", tg_msg)

        # ارسال بله
        if BA_TOKEN and BA_CHANNEL:
            ba_ok = send_bale(BA_TOKEN, BA_CHANNEL, bale_txt)
            if not ba_ok:
                queue.add("bale", bale_txt)
        else:
            ba_ok = True   # اگر بله تنظیم نشده، نادیده بگیر

        if tg_ok:
            # ثبت در تاریخچه (فقط پس از ارسال موفق)
            dedup.add(item["title_clean"], item["link"])
            sent_count += 1

            # آمار
            stats["by_source"][source]      = stats["by_source"].get(source, 0) + 1
            stats["by_category"][cat_key]   = stats["by_category"].get(cat_key, 0) + 1
            stats["by_source_group"][group] = stats["by_source_group"].get(group, 0) + 1

            hour_key = str(now_hour)
            stats["hourly_activity"][hour_key] = stats["hourly_activity"].get(hour_key, 0) + 1

            # آمار روزانه
            stats["today"]["sent"] += 1
            stats["today"]["by_category"][cat_key] = \
                stats["today"]["by_category"].get(cat_key, 0) + 1

        time.sleep(1.5)   # تأخیر بین ارسال‌ها (احترام به rate limit)

    # ── به‌روزرسانی آمار کلی ─────────────────────────────────
    success_count = sum(1 for r in fetch_results if r["success"])
    fail_count    = len(fetch_results) - success_count

    stats["total_sent"]            += sent_count
    stats["total_checked"]         += len(all_items)
    stats["filtered_irrelevant"]   += filtered_irrelevant
    stats["filtered_duplicate"]    += dup_count
    stats["total_sources_checked"] += success_count
    stats["total_sources_failed"]  += fail_count
    stats["run_count"]             += 1
    stats["last_run"]               = _jalali_stamp()
    stats["today"]["sources_checked"] = success_count

    # top category today
    today_cats = stats["today"].get("by_category", {})
    if today_cats:
        top_cat = max(today_cats, key=today_cats.get)
        stats["daily_top_category"] = {
            "key":   top_cat,
            "emoji": CATEGORIES.get(top_cat, {}).get("emoji", ""),
            "label": CATEGORIES.get(top_cat, {}).get("label", ""),
            "count": today_cats[top_cat],
        }

    # خلاصه سلامت
    stats["health_summary"] = health.summary()

    # ── ذخیره ────────────────────────────────────────────────
    dedup.save()
    _save_stats(stats)

    # ── خلاصه نهایی ──────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("📊 خلاصه اجرا:")
    logger.info("   📡 منابع: %d موفق / %d ناموفق", success_count, fail_count)
    logger.info("   📰 آیتم‌های دریافتی: %d", len(all_items))
    logger.info("   ✅ بعد از فیلتر: %d", len(analyzed))
    logger.info("   🆕 جدید: %d", len(new_items))
    logger.info("   📤 ارسال‌شده: %d", sent_count)
    logger.info("   🔁 تکراری: %d", dup_count)
    logger.info("   🚫 نامرتبط: %d", filtered_irrelevant)
    logger.info("=" * 60)
    logger.info("✅ اجرا کامل شد — %s", _jalali_stamp())


if __name__ == "__main__":
    main()
