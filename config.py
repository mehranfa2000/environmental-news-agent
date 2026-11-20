import os

# ===== توکن‌ها (از GitHub Secrets خوانده می‌شوند) =====
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")
BALE_BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN", "")
BALE_CHANNEL_ID = os.environ.get("BALE_CHANNEL_ID", "")

# ===== تنظیمات فیلتر =====
MIN_TITLE_SCORE = 2
MIN_TOTAL_SCORE = 5
TITLE_WEIGHT = 3
SUMMARY_WEIGHT = 1

# ===== تنظیمات امتیازدهی اخبار =====
URGENT_THRESHOLD = 14
HIGH_THRESHOLD = 9
MED_THRESHOLD = 6

# ===== تنظیمات حافظه و تکرار =====
MAX_HISTORY = 3000
SIMILARITY_THRESHOLD = 0.80
FUZZY_WINDOW = 300
MAX_NEWS_STORED = 500

# ===== تنظیمات شبکه =====
FETCH_TIMEOUT = 25
MAX_CONCURRENT = 10

# ===== مسیر فایل‌های داده =====
DATA_DIR = "data"
HISTORY_FILE = f"{DATA_DIR}/history.json"
STATS_FILE = f"{DATA_DIR}/stats.json"
NEWS_FILE = f"{DATA_DIR}/news.json"
QUEUE_FILE = f"{DATA_DIR}/queue.json"
HEALTH_FILE = f"{DATA_DIR}/health.json"

# ===== دسته‌بندی‌ها =====
CATEGORIES = {
    "forest":    {"emoji": "🌳", "label": "جنگل و مراتع",        "color": "#22c55e"},
    "wildlife":  {"emoji": "🐾", "label": "حیات‌وحش",            "color": "#f97316"},
    "water":     {"emoji": "💧", "label": "منابع آبی",            "color": "#3b82f6"},
    "pollution": {"emoji": "🏭", "label": "آلودگی",               "color": "#94a3b8"},
    "areas":     {"emoji": "🏔️", "label": "مناطق حفاظت‌شده",    "color": "#8b5cf6"},
    "waste":     {"emoji": "♻️", "label": "پسماند و بازیافت",    "color": "#06b6d4"},
    "law":       {"emoji": "⚖️", "label": "قوانین و سیاست‌ها",   "color": "#eab308"},
    "climate":   {"emoji": "🌡️", "label": "اقلیم و انرژی",       "color": "#ef4444"},
}

# ===== هدرهای HTTP برای دریافت فیدها =====
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa,en;q=0.9",
    "Connection": "keep-alive",
}
