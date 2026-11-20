# ================================================================
#  bot.py — موتور اصلی
# ================================================================
import json, logging, os, sys, time
from datetime import datetime
import pytz, jdatetime

from config   import (STATS_FILE, NEWS_FILE, DATA_DIR,
                       TIMEZONE, MAX_NEWS_STORED)
from sources  import SOURCES
from keywords import CATEGORIES
from fetcher  import fetch_all
from analyzer import analyze_batch
from dedup    import DedupManager
from formatter import format_telegram, format_bale, jalali_parts
from messenger import send_telegram, send_bale, MsgQueue
from health   import HealthMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("bot")

TZ = pytz.timezone(TIMEZONE)

WEEKDAYS = {0:"دوشنبه",1:"سه‌شنبه",2:"چهارشنبه",
            3:"پنج‌شنبه",4:"جمعه",5:"شنبه",6:"یکشنبه"}
MONTHS   = ["","فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
            "مهر","آبان","آذر","دی","بهمن","اسفند"]


def _now():
    n  = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
    jd = jdatetime.datetime.fromgregorian(datetime=n)
    return jd.strftime("%Y-%m-%d %H:%M")


def _today_key():
    n  = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ)
    jd = jdatetime.datetime.fromgregorian(datetime=n)
    return jd.strftime("%Y-%m-%d")


def _load(path, default):
    if os.path.exists(path):
        try:
            with open(path,"r",encoding="utf-8") as f: return json.load(f)
        except Exception: pass
    return default


def _save(path, data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
    except Exception as e: logger.error("save %s: %s",path,e)


def _empty_stats():
    return {
        "total_sent":0,"total_checked":0,
        "filtered_irrelevant":0,"filtered_duplicate":0,
        "total_sources_ok":0,"total_sources_fail":0,
        "run_count":0,"last_run":None,
        "by_source":{},"by_category":{},"by_group":{},
        "hourly":{},"today_key":None,
        "today":{"sent":0,"by_category":{},"sources_ok":0},
        "daily_top":{},"health":{},
    }


def main():
    logger.info("="*60)
    logger.info("🌿 بات اخبار محیط زیست — %s", _now())
    logger.info("="*60)

    TGT = os.environ.get("TELEGRAM_BOT_TOKEN","")
    TGC = os.environ.get("TELEGRAM_CHANNEL_ID","")
    BAT = os.environ.get("BALE_BOT_TOKEN","")
    BAC = os.environ.get("BALE_CHANNEL_ID","")

    if not TGT or not TGC:
        logger.error("❌ توکن تلگرام تنظیم نشده"); sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)

    stats  = _load(STATS_FILE, _empty_stats())
    news   = _load(NEWS_FILE,  [])
    dedup  = DedupManager()
    health = HealthMonitor()
    queue  = MsgQueue()

    # ریست روزانه
    tk = _today_key()
    if stats.get("today_key") != tk:
        stats["today"]     = {"sent":0,"by_category":{},"sources_ok":0}
        stats["today_key"] = tk

    # صف retry
    if TGT and BAT:
        retried = queue.retry_all(TGT,TGC,BAT,BAC)
        if retried: logger.info("✅ %d پیام از صف ارسال شد",retried)

    # منابع فعال
    active = health.get_active(SOURCES)
    logger.info("📡 منابع فعال: %d/%d", len(active), len(SOURCES))

    # دریافت موازی
    t0      = time.monotonic()
    results = fetch_all(active)
    logger.info("⚡ %.1f ثانیه", time.monotonic()-t0)

    health.update_batch(results)

    all_items = [i for r in results for i in r["items"]]
    logger.info("📰 کل آیتم: %d", len(all_items))

    analyzed = analyze_batch(all_items)
    irrelevant = len(all_items)-len(analyzed)

    new_items, dups = dedup.filter_new(analyzed)
    logger.info("🆕 جدید:%d تکراری:%d", len(new_items), dups)

    sent = 0
    hour = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(TZ).hour
    jdate = jalali_parts()

    for item in new_items:
        tg  = format_telegram(item)
        bal = format_bale(item)

        ok_tg = send_telegram(TGT, TGC, tg)
        if not ok_tg: queue.add("telegram", tg)

        if BAT and BAC:
            ok_ba = send_bale(BAT, BAC, bal)
            if not ok_ba: queue.add("bale", bal)

        if ok_tg:
            dedup.add(item["title_clean"], item["link"])
            sent += 1
            cat  = item["category_key"]
            src  = item["source"]
            grp  = item["group"]

            # آمار
            stats["by_source"][src]  = stats["by_source"].get(src,0)+1
            stats["by_category"][cat]= stats["by_category"].get(cat,0)+1
            stats["by_group"][grp]   = stats["by_group"].get(grp,0)+1
            stats["hourly"][str(hour)]= stats["hourly"].get(str(hour),0)+1
            stats["today"]["sent"]   += 1
            stats["today"]["by_category"][cat]=\
                stats["today"]["by_category"].get(cat,0)+1

            # ذخیره خبر برای داشبورد
            news.append({
                "id":       f"{hash(item['link'])&0xffffffff:08x}",
                "title":    item["title_clean"],
                "link":     item["link"],
                "source":   src,
                "group":    grp,
                "cat_key":  cat,
                "cat_emoji":item["category_emoji"],
                "cat_label":item["category_label"],
                "cat_color":item["category_color"],
                "urgency":  item.get("urgency",""),
                "date":     jdate["date"],
                "weekday":  jdate["weekday"],
                "time":     jdate["time"],
                "full":     jdate["full"],
                "score":    item["total_score"],
            })

        time.sleep(1.5)

    ok_src  = sum(1 for r in results if r["success"])
    fail_src= len(results)-ok_src

    stats["total_sent"]           += sent
    stats["total_checked"]        += len(all_items)
    stats["filtered_irrelevant"]  += irrelevant
    stats["filtered_duplicate"]   += dups
    stats["total_sources_ok"]     += ok_src
    stats["total_sources_fail"]   += fail_src
    stats["run_count"]            += 1
    stats["last_run"]              = _now()
    stats["today"]["sources_ok"]   = ok_src

    # بهترین دسته امروز
    tc = stats["today"].get("by_category",{})
    if tc:
        top = max(tc,key=tc.get)
        c   = CATEGORIES.get(top,{})
        stats["daily_top"] = {
            "key":top,"emoji":c.get("emoji",""),
            "label":c.get("label",""),"count":tc[top]}

    stats["health"] = health.summary()

    dedup.save()
    _save(STATS_FILE, stats)
    # جدیدترین MAX_NEWS_STORED خبر را نگه دار
    _save(NEWS_FILE, news[-MAX_NEWS_STORED:])

    logger.info("="*60)
    logger.info("✅ منابع:%d/%d | آیتم:%d | ارسال:%d | رد:%d | تکراری:%d",
                ok_src,len(results),len(all_items),sent,irrelevant,dups)
    logger.info("="*60)


if __name__ == "__main__":
    main()
