# ================================================================
#  config.py — تنظیمات مرکزی
# ================================================================
import os

# ── مسیرها ───────────────────────────────────────────────────────
DATA_DIR      = "data"
HISTORY_FILE  = os.path.join(DATA_DIR, "history.json")
STATS_FILE    = os.path.join(DATA_DIR, "stats.json")
NEWS_FILE     = os.path.join(DATA_DIR, "news.json")
QUEUE_FILE    = os.path.join(DATA_DIR, "queue.json")
HEALTH_FILE   = os.path.join(DATA_DIR, "health.json")

# ── فیلتر ────────────────────────────────────────────────────────
MIN_TITLE_SCORE  = 2
MIN_TOTAL_SCORE  = 5
TITLE_WEIGHT     = 3
SUMMARY_WEIGHT   = 1

# ── اهمیت خبر ────────────────────────────────────────────────────
URGENT_THRESHOLD = 14
HIGH_THRESHOLD   = 9
MED_THRESHOLD    = 6

# ── حذف تکراری ───────────────────────────────────────────────────
MAX_HISTORY          = 3000
SIMILARITY_THRESHOLD = 0.80
FUZZY_WINDOW         = 300

# ── دریافت موازی ─────────────────────────────────────────────────
MAX_CONCURRENT  = 15
FETCH_TIMEOUT   = 20
MAX_FEED_ITEMS  = 30

# ── ارسال ────────────────────────────────────────────────────────
RETRY_ATTEMPTS    = 4
RETRY_BASE_DELAY  = 2
MAX_QUEUE_HOURS   = 48
MAX_QUEUE_SIZE    = 150

# ── سلامت منابع ──────────────────────────────────────────────────
FAIL_THRESHOLD    = 24
RECOVERY_CHECKS   = 3
SLOW_THRESHOLD_MS = 10000

# ── اخبار داشبورد ────────────────────────────────────────────────
MAX_NEWS_STORED = 500

# ── زمان ─────────────────────────────────────────────────────────
TIMEZONE     = "Asia/Tehran"
DIGEST_HOUR  = 22

# ── تصویر ────────────────────────────────────────────────────────
FETCH_IMAGE      = True
IMAGE_TIMEOUT    = 8
MAX_IMAGE_MB     = 5
