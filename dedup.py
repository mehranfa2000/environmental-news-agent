# ================================================================
#  dedup.py — حذف تکراری هوشمند
# ================================================================
import hashlib, json, logging, os
from difflib import SequenceMatcher
from config import (HISTORY_FILE, MAX_HISTORY,
                    SIMILARITY_THRESHOLD, FUZZY_WINDOW, DATA_DIR)

logger = logging.getLogger(__name__)


def _hash(title, link):
    raw = (title.strip().lower()+"|"+link.strip().lower()).encode()
    return hashlib.sha256(raw).hexdigest()


def _sim(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class DedupManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._d = self._load()
        self._titles = self._d.get("recent_titles",[])[-FUZZY_WINDOW:]

    def _load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE,"r",encoding="utf-8") as f:
                    return json.load(f)
            except Exception: pass
        return {"hashes":[],"recent_titles":[]}

    def save(self):
        try:
            with open(HISTORY_FILE,"w",encoding="utf-8") as f:
                json.dump(self._d,f,ensure_ascii=False,indent=2)
        except Exception as e:
            logger.error("❌ history save: %s",e)

    def is_dup(self, title, link):
        h = _hash(title, link)
        if h in self._d["hashes"]:
            return True, "hash"
        for pt in self._titles[-FUZZY_WINDOW:]:
            if _sim(title, pt) >= SIMILARITY_THRESHOLD:
                return True, "fuzzy"
        return False, ""

    def add(self, title, link):
        h = _hash(title, link)
        hashes = self._d["hashes"]
        hashes.append(h)
        if len(hashes) > MAX_HISTORY:
            hashes = hashes[-MAX_HISTORY:]
        self._d["hashes"] = hashes
        self._titles.append(title.strip())
        if len(self._titles) > FUZZY_WINDOW:
            self._titles = self._titles[-FUZZY_WINDOW:]
        self._d["recent_titles"] = self._titles

    def filter_new(self, items):
        new, dups = [], 0
        for item in items:
            is_d, _ = self.is_dup(item["title_clean"], item["link"])
            if is_d: dups += 1
            else:    new.append(item)
        return new, dups
