import re
from config import (
    MIN_TITLE_SCORE, MIN_TOTAL_SCORE,
    TITLE_WEIGHT, SUMMARY_WEIGHT,
    URGENT_THRESHOLD, HIGH_THRESHOLD, MED_THRESHOLD,
    CATEGORIES
)
from keywords import KEYWORDS, FA_ROOTS, CATEGORY_KEYWORDS, BLACKLIST


def clean_text(text):
    """پاک‌سازی و نرمال‌سازی متن فارسی"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = text.replace("ك", "ک").replace("ي", "ی")
    text = text.replace("ة", "ه").replace("أ", "ا").replace("إ", "ا")
    return text.strip()


def has_fa_root(text):
    """بررسی وجود ریشه‌های کلیدی محیط‌زیستی در متن"""
    for root in FA_ROOTS:
        if root in text:
            return True
    return False


def is_blacklisted(title):
    """بررسی بلک‌لیست روی عنوان خبر"""
    title_lower = title.lower()
    for word in BLACKLIST:
        if word in title_lower or word in title:
            return True
    return False


def score_text(text):
    """محاسبه امتیاز محیط‌زیستی یک متن"""
    if not text:
        return 0

    score = 0
    text_lower = text.lower()

    for keyword, weight in KEYWORDS.items():
        if keyword in text or keyword in text_lower:
            score += weight

    if has_fa_root(text):
        score += 3

    return score


def classify_category(title, summary):
    """تعیین دسته‌بندی خبر"""
    combined = title + " " + summary

    best_cat = "pollution"
    best_score = 0

    for cat_key, keywords in CATEGORY_KEYWORDS.items():
        cat_score = 0
        for kw in keywords:
            if kw in combined:
                cat_score += 1
        if cat_score > best_score:
            best_score = cat_score
            best_cat = cat_key

    return best_cat


def get_urgency(score):
    """تعیین سطح اهمیت خبر بر اساس امتیاز"""
    if score >= URGENT_THRESHOLD:
        return "urgent"
    elif score >= HIGH_THRESHOLD:
        return "high"
    elif score >= MED_THRESHOLD:
        return "medium"
    else:
        return "low"


def analyze_entry(entry):
    """
    تحلیل کامل یک خبر با سه لایه فیلتر:
    لایه ۱: بلک‌لیست عنوان
    لایه ۲: امتیاز عنوان >= MIN_TITLE_SCORE
    لایه ۳: امتیاز کل >= MIN_TOTAL_SCORE
    """

    title = clean_text(entry.get("title", ""))
    if not title:
        return None, "no_title"

    summary = ""
    if entry.get("summary"):
        summary = clean_text(entry.get("summary", ""))
    elif entry.get("description"):
        summary = clean_text(entry.get("description", ""))
    elif entry.get("content"):
        try:
            summary = clean_text(entry["content"][0].get("value", ""))
        except Exception:
            summary = ""

    link = entry.get("link", "").strip()
    if not link:
        return None, "no_link"

    # ===== لایه ۱: بلک‌لیست =====
    if is_blacklisted(title):
        return None, "blacklist"

    # ===== لایه ۲: امتیاز عنوان =====
    title_score = score_text(title)
    if title_score < MIN_TITLE_SCORE:
        return None, "low_title_score"

    # ===== لایه ۳: امتیاز کل =====
    summary_score = score_text(summary)
    total_score = (title_score * TITLE_WEIGHT) + (summary_score * SUMMARY_WEIGHT)

    if total_score < MIN_TOTAL_SCORE:
        return None, "low_total_score"

    # ===== دسته‌بندی =====
    cat_key = classify_category(title, summary)
    cat_info = CATEGORIES.get(cat_key, CATEGORIES["pollution"])

    # ===== سطح اهمیت =====
    urgency = get_urgency(total_score)

    result = {
        "title": title,
        "link": link,
        "summary": summary[:300] if summary else "",
        "source": entry.get("source_name", "نامشخص"),
        "group": entry.get("source_group", "عمومی"),
        "cat_key": cat_key,
        "cat_emoji": cat_info["emoji"],
        "cat_label": cat_info["label"],
        "cat_color": cat_info["color"],
        "urgency": urgency,
        "score": total_score,
        "title_score": title_score,
        "summary_score": summary_score,
    }

    return result, "ok"


def analyze_entries(entries):
    """
    تحلیل دسته‌ای از اخبار
    خروجی: لیست اخبار تایید شده + آمار فیلترها
    """
    approved = []
    stats = {
        "total_checked": len(entries),
        "passed": 0,
        "filtered_blacklist": 0,
        "filtered_low_title": 0,
        "filtered_low_total": 0,
        "filtered_other": 0,
    }

    print(f"\n[Analyzer] بررسی {len(entries)} خبر...")

    for entry in entries:
        result, reason = analyze_entry(entry)

        if reason == "ok":
            approved.append(result)
            stats["passed"] += 1
        elif reason == "blacklist":
            stats["filtered_blacklist"] += 1
        elif reason == "low_title_score":
            stats["filtered_low_title"] += 1
        elif reason == "low_total_score":
            stats["filtered_low_total"] += 1
        else:
            stats["filtered_other"] += 1

    total_filtered = (
        stats["filtered_blacklist"] +
        stats["filtered_low_title"] +
        stats["filtered_low_total"] +
        stats["filtered_other"]
    )

    print(f"[Analyzer] نتیجه:")
    print(f"  ✅ تایید شده: {stats['passed']}")
    print(f"  🚫 بلک‌لیست: {stats['filtered_blacklist']}")
    print(f"  📉 امتیاز عنوان کم: {stats['filtered_low_title']}")
    print(f"  📉 امتیاز کل کم: {stats['filtered_low_total']}")
    print(f"  🔁 سایر: {stats['filtered_other']}")
    print(f"  📊 کل فیلتر شده: {total_filtered}")

    return approved, stats
