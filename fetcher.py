# ================================================================
#  fetcher.py — دریافت موازی async
# ================================================================
import asyncio, logging, time
from typing import Optional
import aiohttp, feedparser
from config import MAX_CONCURRENT, FETCH_TIMEOUT, MAX_FEED_ITEMS

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml,application/xml,text/xml,*/*",
}


async def _fetch_one(session, sem, name, url, group):
    res = {"name":name,"url":url,"group":group,
           "items":[],"success":False,"ms":0,"error":None}
    async with sem:
        t = time.monotonic()
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT),
                headers=HEADERS, ssl=False,
                allow_redirects=True, max_redirects=5,
            ) as r:
                res["ms"] = int((time.monotonic()-t)*1000)
                if r.status != 200:
                    res["error"] = f"HTTP {r.status}"
                    return res
                raw = await r.read()
        except asyncio.TimeoutError:
            res["error"]="timeout"; res["ms"]=FETCH_TIMEOUT*1000; return res
        except Exception as e:
            res["error"]=str(e); return res

    try:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, raw)
        items = []
        for e in feed.entries[:MAX_FEED_ITEMS]:
            title   = (getattr(e,"title","") or "").strip()
            summary = (getattr(e,"summary","") or
                       getattr(e,"description","") or "").strip()
            link    = (getattr(e,"link","") or "").strip()
            pub     = (getattr(e,"published","") or
                       getattr(e,"updated","") or "")
            if not title or not link:
                continue
            img: Optional[str] = None
            if hasattr(e,"media_content") and e.media_content:
                img = e.media_content[0].get("url")
            elif hasattr(e,"enclosures") and e.enclosures:
                enc = e.enclosures[0]
                if enc.get("type","").startswith("image"):
                    img = enc.get("href") or enc.get("url")
            items.append({"title":title,"summary":summary,
                          "link":link,"published":pub,
                          "image_url":img,"source":name,"group":group})
        res["items"]  = items
        res["success"]= True
    except Exception as e:
        res["error"] = f"parse:{e}"
    return res


async def _fetch_all_async(sources):
    sem  = asyncio.Semaphore(MAX_CONCURRENT)
    conn = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT, limit_per_host=3,
        ttl_dns_cache=300, force_close=True)
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = [_fetch_one(session,sem,n,u,g) for n,u,g in sources]
        return await asyncio.gather(*tasks)


def fetch_all(sources):
    results = asyncio.run(_fetch_all_async(sources))
    ok  = sum(1 for r in results if r["success"])
    tot = sum(len(r["items"]) for r in results)
    logger.info("📡 %d/%d موفق — %d آیتم", ok, len(results), tot)
    return results
