# ================================================================
#  🌿 ایجنت هوشمند اخبار محیط‌زیست ایران و جهان
#  نسخه فوق حرفه‌ای — قابل ارائه به عالی‌ترین سطوح مدیریتی
#  ----------------------------------------------------------------
#  معماری: منابع مجزا | فیلتر چندلایه | امتیازدهی وزنی
#           تاریخ شمسی | ارسال Retry | لاگ کامل | آمار جامع
# ================================================================

import feedparser
import os
import json
import hashlib
import logging
import time
import re
from datetime import datetime

import pytz

from sources   import SOURCES, SOURCE_CATEGORIES
from keywords  import (
    PERSIAN_KEYWORDS, ENGLISH_KEYWORDS,
    BLACKLIST_TITLE, CATEGORIES,
    MIN_TITLE_SCORE, MIN_TOTAL_SCORE,
    TITLE_WEIGHT, SUMMARY_WEIGHT,
)
from formatter import clean_html, smart_summary, format_telegram, format_bale
from messenger import send_telegram, send_bale

# ──────────────────────────────────────────
#  تنظیم سیستم لاگ
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(levelname)-8s │ %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)

# ──────────────────────────────────────────
#  ثابت‌های پروژه
# ──────────────────────────────────────────
MAX_HISTORY    = 2000   # حداکثر هش‌های ذخیره‌شده
MAX_ENTRIES    = 25     # تعداد خبر بررسی‌شده از هر منبع
SEND_DELAY     = 3      # تاخیر بین ارسال‌ها (ثانیه) — جلوگیری از Rate Limit
FEED_TIMEOUT   = 30     # Timeout خواندن RSS (ثانیه)
DB_FILE        = 'history.json'
STATS_FILE     = 'stats.json'

# ──────────────────────────────────────────
#  توابع امتیازدهی و فیلتر
# ──────────────────────────────────────────

def score_text(text: str, is_english: bool = False) -> int:
    """محاسبه امتیاز متن بر اساس کلیدواژه‌های وزن‌دار"""
    if not text:
        return 0
    score = 0
    if is_english:
        for kw, w in ENGLISH_KEYWORDS.items():
            if kw.lower() in text.lower():
                score += w
    else:
        for kw, w in PERSIAN_KEYWORDS.items():
            if kw in text:
                score += w
    return score

def has_blacklist(title: str) -> bool:
    """بررسی وجود کلیدواژه رد‌کننده در عنوان"""
    for bl in BLACKLIST_TITLE:
        if bl in title:
            return True
    return False

def detect_language(text: str) -> str:
    """تشخیص فارسی یا انگلیسی بودن متن"""
    fa_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    en_chars = len(re.findall(r'[a-zA-Z]', text))
    return 'fa' if fa_chars >= en_chars else 'en'

def is_environmental(title: str, summary: str) -> tuple[bool, int]:
    """
    فیلتر چندلایه:
    ۱. اگر کلیدواژه رد‌کننده در عنوان باشد → رد
    ۲. امتیاز عنوان باید >= MIN_TITLE_SCORE باشد
    ۳. امتیاز کل (عنوان×TITLE_WEIGHT + خلاصه×SUMMARY_WEIGHT) >= MIN_TOTAL_SCORE
    """
    if has_blacklist(title):
        return False, 0

    lang = detect_language(title + summary)
    is_en = (lang == 'en')

    title_score   = score_text(title,   is_english=is_en)
    summary_score = score_text(summary, is_english=is_en)
    total_score   = title_score * TITLE_WEIGHT + summary_score * SUMMARY_WEIGHT

    if title_score < MIN_TITLE_SCORE:
        return False, total_score
    if total_score < MIN_TOTAL_SCORE:
        return False, total_score

    return True, total_score

def get_category(title: str, summary: str) -> str:
    """تعیین دسته‌بندی بر اساس بیشترین تطابق وزن‌دار"""
    text = title + ' ' + summary
    lang = detect_language(text)
    key  = 'en' if lang == 'en' else 'fa'

    best_cat  = '🌍 سایر اخبار محیط زیست'
    max_score = 0

    for cat, kw_dict in CATEGORIES.items():
        kw_list = kw_dict.get(key, [])
        s = sum(
            PERSIAN_KEYWORDS.get(kw, ENGLISH_KEYWORDS.get(kw.lower(), 1))
            for kw in kw_list
            if kw in text
        )
        if s > max_score:
            max_score = s
            best_cat  = cat

    return best_cat

# ──────────────────────────────────────────
#  توابع ذخیره/بارگذاری
# ──────────────────────────────────────────

def load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"خطا در بارگذاری {path}: {e}")
    return default

def save_json(path: str, data) -> None:
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"خطا در ذخیره {path}: {e}")

def make_hash(title: str, link: str) -> str:
    return hashlib.sha256((title + link).encode('utf-8')).hexdigest()[:16]

# ──────────────────────────────────────────
#  تابع اصلی
# ──────────────────────────────────────────

def main():
    log.info("╔" + "═" * 54 + "╗")
    log.info("║   🌿 ایجنت اخبار محیط‌زیست — شروع اجرا              ║")
    log.info("╚" + "═" * 54 + "╝")

    tehran_tz  = pytz.timezone('Asia/Tehran')
    now        = datetime.now(tehran_tz)

    # ── بارگذاری داده‌ها ──
    history: list  = load_json(DB_FILE, [])
    history_set    = set(history)

    stats: dict = load_json(STATS_FILE, {
        "total_sent":               0,
        "total_checked":            0,
        "filtered_irrelevant":      0,
        "filtered_duplicate":       0,
        "filtered_blacklist":       0,
        "total_sources_checked":    0,
        "total_sources_failed":     0,
        "last_run":                 "",
        "run_count":                0,
        "by_source":                {},
        "by_category":              {},
        "by_source_group":          {},
        "hourly_activity":          {},
        "daily_top_category":       {},
    })

    stats["last_run"]   = now.strftime('%Y-%m-%d %H:%M:%S')
    stats["run_count"]  = stats.get("run_count", 0) + 1
    hour_key            = now.strftime('%H:00')

    # ── شمارنده‌های این اجرا ──
    run_sent  = 0
    run_irrel = 0
    run_dupl  = 0
    run_black = 0
    run_fail  = 0

    new_hashes = []

    # ══════════════════════════════════════════
    #  پردازش منابع خبری
    # ══════════════════════════════════════════
    for source_name, feed_url in SOURCES.items():
        stats["total_sources_checked"] = stats.get("total_sources_checked", 0) + 1
        log.info(f"📡 {source_name}")

        try:
            # تنظیم User-Agent برای جلوگیری از Block شدن
            feedparser.USER_AGENT = (
                "Mozilla/5.0 (compatible; EnvNewsAgent/3.0; "
                "+https://github.com/environmental-news-agent)"
            )
            feed = feedparser.parse(feed_url, request_headers={
                'User-Agent': feedparser.USER_AGENT,
                'Accept-Language': 'fa,en;q=0.9',
            })

            if feed.bozo and not feed.entries:
                log.warning(f"   ⚠ خطا در پارس RSS: {feed_url}")
                run_fail += 1
                stats["total_sources_failed"] = stats.get("total_sources_failed", 0) + 1
                continue

            entries = feed.entries[:MAX_ENTRIES]
            log.info(f"   ← {len(entries)} خبر دریافت شد")

        except Exception as e:
            log.error(f"   ✗ خطای شبکه: {e}")
            run_fail += 1
            stats["total_sources_failed"] = stats.get("total_sources_failed", 0) + 1
            continue

        # ── پردازش هر خبر ──
        for entry in entries:
            stats["total_checked"] = stats.get("total_checked", 0) + 1

            raw_title   = entry.get('title',   '')
            raw_summary = entry.get('summary', '') or entry.get('description', '')
            link        = entry.get('link',    '')

            if not raw_title or not link:
                continue

            title   = clean_html(raw_title).strip()
            summary = clean_html(raw_summary).strip()

            # ── بررسی تکراری ──
            content_hash = make_hash(title, link)
            if content_hash in history_set:
                run_dupl += 1
                stats["filtered_duplicate"] = stats.get("filtered_duplicate", 0) + 1
                continue

            # ── بررسی Blacklist ──
            if has_blacklist(title):
                run_black += 1
                stats["filtered_blacklist"] = stats.get("filtered_blacklist", 0) + 1
                log.info(f"   🚫 Blacklist: {title[:60]}")
                # اضافه به تاریخچه تا دوباره پردازش نشود
                history_set.add(content_hash)
                new_hashes.append(content_hash)
                continue

            # ── فیلتر محیط‌زیستی ──
            is_env, total_score = is_environmental(title, summary)
            if not is_env:
                run_irrel += 1
                stats["filtered_irrelevant"] = stats.get("filtered_irrelevant", 0) + 1
                log.info(f"   ✗ فیلتر (امتیاز={total_score}): {title[:60]}")
                continue

            # ── دسته‌بندی ──
            category      = get_category(title, summary)
            short_summary = smart_summary(summary)

            # ── قالب‌بندی پیام‌ها ──
            tg_msg   = format_telegram(
                title, short_summary, link,
                source_name, category, total_score, now
            )
            bale_msg = format_bale(
                title, short_summary, link,
                source_name, category, total_score, now
            )

            # ── ارسال ──
            tg_ok   = send_telegram(tg_msg)
            time.sleep(SEND_DELAY)
            bale_ok = send_bale(bale_msg)

            if tg_ok or bale_ok:
                history_set.add(content_hash)
                new_hashes.append(content_hash)
                run_sent += 1
                stats["total_sent"] = stats.get("total_sent", 0) + 1

                # ── به‌روزرسانی آمار ──
                # آمار بر اساس منبع
                src_stats = stats.get("by_source", {})
                src_stats[source_name] = src_stats.get(source_name, 0) + 1
                stats["by_source"] = src_stats

                # آمار بر اساس دسته‌بندی
                cat_stats = stats.get("by_category", {})
                cat_stats[category] = cat_stats.get(category, 0) + 1
                stats["by_category"] = cat_stats

                # آمار بر اساس گروه منبع
                for group, members in SOURCE_CATEGORIES.items():
                    if source_name in members:
                        grp_stats = stats.get("by_source_group", {})
                        grp_stats[group] = grp_stats.get(group, 0) + 1
                        stats["by_source_group"] = grp_stats
                        break

                # آمار ساعتی
                hourly = stats.get("hourly_activity", {})
                hourly[hour_key] = hourly.get(hour_key, 0) + 1
                stats["hourly_activity"] = hourly

                log.info(f"   ✅ ارسال شد (امتیاز={total_score} | {category[:20]}): {title[:55]}")
            else:
                log.error(f"   ❌ ارسال ناموفق: {title[:60]}")

        # تاخیر بین منابع برای جلوگیری از Rate Limit
        time.sleep(1)

    # ══════════════════════════════════════════
    #  خلاصه نهایی
    # ══════════════════════════════════════════
    log.info("╔" + "═" * 54 + "╗")
    log.info(f"║  ✅ ارسال‌شده:        {run_sent:<5}                        ║")
    log.info(f"║  🔁 تکراری:          {run_dupl:<5}                        ║")
    log.info(f"║  🚫 Blacklist:        {run_black:<5}                        ║")
    log.info(f"║  ❌ بی‌ربط:          {run_irrel:<5}                        ║")
    log.info(f"║  ⚠ منابع ناموفق:    {run_fail:<5}                        ║")
    log.info(f"║  📊 مجموع کل ارسال: {stats['total_sent']:<5}                        ║")
    log.info("╚" + "═" * 54 + "╝")

    # ── ذخیره نهایی ──
    full_history = list(history_set)
    save_json(DB_FILE,   full_history[-MAX_HISTORY:])
    save_json(STATS_FILE, stats)
    log.info("💾 تاریخچه و آمار ذخیره شدند.")

if __name__ == "__main__":
    main()
