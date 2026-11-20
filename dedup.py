# ============================================================
#  dedup.py  —  حذف تکراری هوشمند
#  لایه ۱: هش SHA-256 (تطابق دقیق)
#  لایه ۲: شباهت عنوان SequenceMatcher (تطابق فازی)
# ============================================================

import hashlib
import json
import logging
import os
from difflib import SequenceMatcher
from datetime import datetime
from config import (
    HISTORY_FILE, MAX_HISTORY,
    SIMILARITY_THRESHOLD, FUZZY_WINDOW, DATA_DIR
)

logger = logging.getLogger(__name__)


def _make_hash(title: str, link: str) -> str:
    """SHA-256 از ترکیب عنوان + لینک."""
    raw = (title.strip().lower() + "|" + link.strip().lower()).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _similarity(a: str, b: str) -> float:
    """نسبت شباهت دو رشته (۰ تا ۱)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class DedupManager:
    """مدیریت حذف تکراری با persistence."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._data = self._load()
        # لیست عناوین اخیر برای fuzzy check (سریع‌تر)
        self._recent_titles: list[str] = self._data.get("recent_titles", [])[-FUZZY_WINDOW:]

    def _load(self) -> dict:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("⚠️ خطا در خواندن history.json: %s", e)
        return {"hashes": [], "recent_titles": []}

    def save(self):
        """ذخیره تاریخچه روی دیسک."""
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("❌ خطا در ذخیره history.json: %s", e)

    def is_duplicate(self, title: str, link: str) -> tuple[bool, str]:
        """
        بررسی تکراری بودن.
        خروجی: (is_dup, reason)
        """
        # لایه ۱: هش دقیق
        h = _make_hash(title, link)
        if h in self._data["hashes"]:
            return True, "hash"

        # لایه ۲: شباهت فازی روی عناوین اخیر
        for prev_title in self._recent_titles[-FUZZY_WINDOW:]:
            sim = _similarity(title, prev_title)
            if sim >= SIMILARITY_THRESHOLD:
                logger.debug("🔁 fuzzy dup (%.0f%%): %s", sim * 100, title[:50])
                return True, f"fuzzy({sim:.0%})"

        return False, ""

    def add(self, title: str, link: str):
        """خبر جدید را به تاریخچه اضافه می‌کند."""
        h = _make_hash(title, link)

        hashes = self._data["hashes"]
        hashes.append(h)
        if len(hashes) > MAX_HISTORY:
            hashes = hashes[-MAX_HISTORY:]
        self._data["hashes"] = hashes

        self._recent_titles.append(title.strip())
        if len(self._recent_titles) > FUZZY_WINDOW:
            self._recent_titles = self._recent_titles[-FUZZY_WINDOW:]
        self._data["recent_titles"] = self._recent_titles

    def filter_new(self, items: list[dict]) -> tuple[list[dict], int]:
        """
        از یک لیست آیتم، فقط موارد جدید را برمی‌گردد.
        خروجی: (new_items, dup_count)
        """
        new_items  = []
        dup_count  = 0

        for item in items:
            is_dup, reason = self.is_duplicate(item["title_clean"], item["link"])
            if is_dup:
                dup_count += 1
                logger.debug("⏭️ skip (%s): %s", reason, item["title_clean"][:50])
            else:
                new_items.append(item)

        return new_items, dup_count
