import json
import os
import hashlib
from config import (
    HISTORY_FILE, DATA_DIR,
    MAX_HISTORY, SIMILARITY_THRESHOLD, FUZZY_WINDOW
)


def load_history():
    """بارگذاری تاریخچه اخبار قبلی"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"hashes": [], "titles": []}


def save_history(history):
    """ذخیره تاریخچه اخبار"""
    os.makedirs(DATA_DIR, exist_ok=True)

    # محدود کردن تعداد تاریخچه
    if len(history["hashes"]) > MAX_HISTORY:
        history["hashes"] = history["hashes"][-MAX_HISTORY:]
    if len(history["titles"]) > MAX_HISTORY:
        history["titles"] = history["titles"][-MAX_HISTORY:]

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Dedup] Save error: {e}")


def make_hash(title, link):
    """ساخت هش SHA-256 از عنوان + لینک"""
    content = f"{title.strip()}|{link.strip()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def similarity(a, b):
    """
    محاسبه شباهت دو رشته با روش ساده Jaccard
    بدون نیاز به کتابخانه خارجی
    """
    if not a or not b:
        return 0.0

    # تبدیل به مجموعه کلمات
    words_a = set(a.split())
    words_b = set(b.split())

    if not words_a or not words_b:
        return 0.0

    intersection = len(words_a & words_b)
    union = len(words_a | words_b)

    if union == 0:
        return 0.0

    return intersection / union


def is_duplicate(item, history):
    """
    بررسی تکراری بودن یک خبر
    روش ۱: هش SHA-256
    روش ۲: شباهت عنوان (Jaccard)
    """
    title = item.get("title", "")
    link = item.get("link", "")

    # روش ۱: بررسی هش
    item_hash = make_hash(title, link)
    if item_hash in history["hashes"]:
        return True, "hash"

    # روش ۲: بررسی شباهت عنوان
    # فقط در پنجره آخرین FUZZY_WINDOW عنوان چک می‌کند
    recent_titles = history["titles"][-FUZZY_WINDOW:]
    for prev_title in recent_titles:
        sim = similarity(title, prev_title)
        if sim >= SIMILARITY_THRESHOLD:
            return True, f"fuzzy({sim:.2f})"

    return False, None


def add_to_history(item, history):
    """اضافه کردن خبر جدید به تاریخچه"""
    title = item.get("title", "")
    link = item.get("link", "")

    item_hash = make_hash(title, link)
    history["hashes"].append(item_hash)
    history["titles"].append(title)

    return history


def deduplicate(items):
    """
    حذف اخبار تکراری از لیست
    خروجی: لیست اخبار غیرتکراری + آمار
    """
    history = load_history()
    unique_items = []
    duplicate_count = 0

    print(f"\n[Dedup] بررسی تکرار {len(items)} خبر...")

    for item in items:
        is_dup, reason = is_duplicate(item, history)

        if is_dup:
            duplicate_count += 1
        else:
            unique_items.append(item)
            history = add_to_history(item, history)

    # ذخیره تاریخچه آپدیت شده
    save_history(history)

    print(f"[Dedup] نتیجه:")
    print(f"  ✅ خبر جدید: {len(unique_items)}")
    print(f"  🔁 تکراری حذف شده: {duplicate_count}")

    stats = {
        "filtered_duplicate": duplicate_count,
        "unique_count": len(unique_items),
    }

    return unique_items, stats
