# ================================================================
#  analyzer.py — سه‌لایه فیلتر + دسته‌بندی
# ================================================================
import re, logging
from html import unescape
from keywords import BLACKLIST, FA_KEYWORDS, FA_ROOTS, CATEGORIES
from config import (MIN_TITLE_SCORE, MIN_TOTAL_SCORE,
                    TITLE_WEIGHT, SUMMARY_WEIGHT,
                    URGENT_THRESHOLD, HIGH_THRESHOLD, MED_THRESHOLD)

logger = logging.getLogger(__name__)


def _clean(text):
    text = unescape(text or "")
    text = re.sub(r"<[^>]+>"," ",text)
    return re.sub(r"\s+"," ",text).strip().lower()


def _score(text, kw_dict):
    return sum(w for kw,w in kw_dict.items() if kw.lower() in text)


def _root_bonus(text):
    return min(sum(1 for r in FA_ROOTS if r in text), 3)


def _blacklisted(title):
    t = title.lower()
    return any(b.lower() in t for b in BLACKLIST)


def _categorize(text):
    best, best_s = "اقلیم", 0
    for key, data in CATEGORIES.items():
        s = sum(1 for k in data["keys"] if k.lower() in text)
        if s > best_s:
            best_s, best = s, key
    d = CATEGORIES[best]
    return best, d["emoji"], d["label"], d["color"]


def _urgency(total):
    if total >= URGENT_THRESHOLD: return "🔴"
    if total >= HIGH_THRESHOLD:   return "🟠"
    if total >= MED_THRESHOLD:    return "🟡"
    return ""


def analyze(item):
    raw_t = item.get("title","") or ""
    raw_s = item.get("summary","") or ""
    tc = _clean(raw_t)
    sc = _clean(raw_s)

    if _blacklisted(raw_t):
        return None

    ts = _score(tc, FA_KEYWORDS) + _root_bonus(tc)
    if ts < MIN_TITLE_SCORE:
        return None

    ss  = _score(sc, FA_KEYWORDS) + _root_bonus(sc)
    tot = ts * TITLE_WEIGHT + ss * SUMMARY_WEIGHT
    if tot < MIN_TOTAL_SCORE:
        return None

    cat, emoji, label, color = _categorize(tc + " " + sc)
    return {**item,
            "title_clean":    raw_t.strip(),
            "summary_clean":  raw_s,
            "title_score":    ts,
            "total_score":    tot,
            "category_key":   cat,
            "category_emoji": emoji,
            "category_label": label,
            "category_color": color,
            "urgency":        _urgency(tot)}


def analyze_batch(items):
    out = [r for r in (analyze(i) for i in items) if r]
    out.sort(key=lambda x: x["total_score"], reverse=True)
    return out
