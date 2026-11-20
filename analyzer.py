# ============================================================
#  analyzer.py  —  تحلیل هوشمند، امتیازدهی، دسته‌بندی
#  سه‌لایه فیلتر + ریشه‌یابی + امتیاز اهمیت
# ============================================================

import re
import logging
from html import unescape
from keywords import (
    BLACKLIST_TITLE, PERSIAN_KEYWORDS, ENGLISH_KEYWORDS,
    CATEGORIES, FA_ROOTS
)
from config import (
    MIN_TITLE_SCORE, MIN_TOTAL_SCORE,
    TITLE_WEIGHT, SUMMARY_WEIGHT,
    IMPORTANCE_URGENT_THRESHOLD,
    IMPORTANCE_HIGH_THRESHOLD,
    IMPORTANCE_MED_THRESHOLD,
)

logger = logging.getLogger(__name__)


# ── پاک‌سازی متن ─────────────────────────────────────────────
def _clean(text: str) -> str:
    """HTML را حذف، فاصله‌های اضافه را پاک می‌کند."""
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


# ── تطبیق کلیدواژه ───────────────────────────────────────────
def _score_text(text: str, keyword_dict: dict[str, int]) -> int:
    """
    امتیاز متن را بر اساس کلیدواژه‌های وزن‌دار حساب می‌کند.
    هر کلیدواژه فقط یک بار شمرده می‌شود.
    """
    score = 0
    for kw, weight in keyword_dict.items():
        if kw.lower() in text:
            score += weight
    return score


def _root_score(text: str) -> int:
    """ریشه‌یابی فارسی — امتیاز اضافه برای کلماتی که ریشه محیط‌زیستی دارند."""
    score = 0
    for root in FA_ROOTS:
        if root in text:
            score += 1
    return min(score, 3)   # حداکثر ۳ امتیاز از ریشه‌یابی


# ── لایه ۱: سیاه‌لیست ────────────────────────────────────────
def _is_blacklisted(title: str) -> bool:
    t = title.lower()
    for word in BLACKLIST_TITLE:
        if word.lower() in t:
            return True
    return False


# ── دسته‌بندی ─────────────────────────────────────────────────
def _categorize(title: str, summary: str) -> tuple[str, str, str]:
    """
    دسته‌بندی خبر.
    خروجی: (category_key, emoji, label)
    """
    combined = title + " " + summary

    best_cat   = "اقلیم"   # پیش‌فرض
    best_score = 0

    for cat_key, cat_data in CATEGORIES.items():
        score = 0
        for kw in cat_data["fa_keys"]:
            if kw.lower() in combined:
                score += 1
        for kw in cat_data["en_keys"]:
            if kw.lower() in combined:
                score += 1
        if score > best_score:
            best_score = score
            best_cat   = cat_key

    cat = CATEGORIES[best_cat]
    return best_cat, cat["emoji"], cat["label"]


# ── امتیاز اهمیت ─────────────────────────────────────────────
def _importance(total_score: int) -> str:
    """برچسب فوریت بر اساس امتیاز کل."""
    if total_score >= IMPORTANCE_URGENT_THRESHOLD:
        return "🔴"   # فوری
    if total_score >= IMPORTANCE_HIGH_THRESHOLD:
        return "🟠"   # مهم
    if total_score >= IMPORTANCE_MED_THRESHOLD:
        return "🟡"   # متوسط
    return ""         # عادی


# ── تحلیل اصلی ───────────────────────────────────────────────
def analyze(item: dict) -> dict | None:
    """
    یک آیتم RSS را تحلیل می‌کند.
    در صورت موفقیت، دیکشنری غنی‌شده برمی‌گردد.
    در صورت رد شدن، None برمی‌گردد.
    """
    raw_title   = item.get("title", "") or ""
    raw_summary = item.get("summary", "") or ""

    title_clean   = _clean(raw_title)
    summary_clean = _clean(raw_summary)

    # ── لایه ۱: سیاه‌لیست ──────────────────────────────────
    if _is_blacklisted(raw_title):
        logger.debug("🚫 blacklist: %s", raw_title[:60])
        return None

    # ── لایه ۲: امتیاز عنوان ───────────────────────────────
    title_score = (
        _score_text(title_clean, PERSIAN_KEYWORDS)
        + _score_text(title_clean, ENGLISH_KEYWORDS)
        + _root_score(title_clean)
    )
    if title_score < MIN_TITLE_SCORE:
        logger.debug("❌ title_score=%d (min=%d): %s", title_score, MIN_TITLE_SCORE, raw_title[:60])
        return None

    # ── لایه ۳: امتیاز کل ──────────────────────────────────
    summary_score = (
        _score_text(summary_clean, PERSIAN_KEYWORDS)
        + _score_text(summary_clean, ENGLISH_KEYWORDS)
        + _root_score(summary_clean)
    )
    total_score = title_score * TITLE_WEIGHT + summary_score * SUMMARY_WEIGHT

    if total_score < MIN_TOTAL_SCORE:
        logger.debug("❌ total_score=%d (min=%d): %s", total_score, MIN_TOTAL_SCORE, raw_title[:60])
        return None

    # ── دسته‌بندی و اهمیت ──────────────────────────────────
    cat_key, emoji, label = _categorize(title_clean, summary_clean)
    urgency = _importance(total_score)

    return {
        **item,
        "title_clean":   raw_title.strip(),
        "summary_clean": raw_summary,
        "title_score":   title_score,
        "summary_score": summary_score,
        "total_score":   total_score,
        "category_key":  cat_key,
        "category_emoji": emoji,
        "category_label": label,
        "urgency":       urgency,
    }


def analyze_batch(items: list[dict]) -> list[dict]:
    """
    یک دسته آیتم را تحلیل می‌کند.
    خروجی: فقط آیتم‌های تأییدشده، مرتب‌شده بر اساس امتیاز (نزولی).
    """
    passed = []
    for item in items:
        result = analyze(item)
        if result:
            passed.append(result)

    # مرتب‌سازی: مهم‌ترین اخبار اول
    passed.sort(key=lambda x: x["total_score"], reverse=True)
    return passed
