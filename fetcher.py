# ============================================================
#  fetcher.py  —  دریافت موازی RSS با aiohttp + asyncio
#  همه منابع همزمان (۲۰ تایی) دریافت می‌شوند
# ============================================================

import asyncio
import logging
import time
from typing import Optional
import aiohttp
import feedparser
from config import MAX_CONCURRENT_FETCHES, FETCH_TIMEOUT_SEC, MAX_FEED_ITEMS

logger = logging.getLogger(__name__)

# ── هدر HTTP برای شبیه‌سازی مرورگر ──────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "fa,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}


async def _fetch_one(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    name: str,
    url: str,
    group: str,
) -> dict:
    """
    یک منبع RSS را دریافت و parse می‌کند.
    خروجی: دیکشنری با نام، گروه، آیتم‌ها، زمان پاسخ و وضعیت.
    """
    result = {
        "name": name,
        "url": url,
        "group": group,
        "items": [],
        "success": False,
        "response_ms": 0,
        "error": None,
    }

    async with semaphore:
        t_start = time.monotonic()
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT_SEC),
                headers=HEADERS,
                ssl=False,          # برخی سایت‌های ایرانی گواهی SSL معتبر ندارند
                allow_redirects=True,
                max_redirects=5,
            ) as resp:
                result["response_ms"] = int((time.monotonic() - t_start) * 1000)

                if resp.status != 200:
                    result["error"] = f"HTTP {resp.status}"
                    logger.warning("❌ %s → HTTP %s", name, resp.status)
                    return result

                raw = await resp.read()

        except asyncio.TimeoutError:
            result["error"] = "timeout"
            result["response_ms"] = FETCH_TIMEOUT_SEC * 1000
            logger.warning("⏱️ timeout: %s", name)
            return result
        except aiohttp.ClientConnectorError as e:
            result["error"] = f"connection: {e}"
            logger.warning("🔌 connection error: %s — %s", name, e)
            return result
        except Exception as e:
            result["error"] = str(e)
            logger.warning("⚠️ fetch error: %s — %s", name, e)
            return result

    # ── parse با feedparser (CPU-bound → در thread pool) ─────
    try:
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, raw)

        entries = feed.entries[:MAX_FEED_ITEMS]
        items = []
        for entry in entries:
            title   = getattr(entry, "title",   "") or ""
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            link    = getattr(entry, "link",    "") or ""
            pub     = getattr(entry, "published", "") or getattr(entry, "updated", "") or ""

            if not title or not link:
                continue

            # تصویر شاخص از media:content یا enclosure
            image_url: Optional[str] = None
            if hasattr(entry, "media_content") and entry.media_content:
                image_url = entry.media_content[0].get("url")
            elif hasattr(entry, "enclosures") and entry.enclosures:
                enc = entry.enclosures[0]
                if enc.get("type", "").startswith("image"):
                    image_url = enc.get("href") or enc.get("url")

            items.append({
                "title":     title.strip(),
                "summary":   summary,
                "link":      link.strip(),
                "published": pub,
                "image_url": image_url,
                "source":    name,
                "group":     group,
            })

        result["items"]   = items
        result["success"] = True
        logger.debug("✅ %s — %d items (%.0f ms)", name, len(items), result["response_ms"])

    except Exception as e:
        result["error"] = f"parse error: {e}"
        logger.warning("🔍 parse error: %s — %s", name, e)

    return result


async def fetch_all_async(sources: list[tuple]) -> list[dict]:
    """
    همه منابع RSS را به‌صورت موازی دریافت می‌کند.
    ورودی: لیست تاپل‌های (name, url, group)
    خروجی: لیست دیکشنری نتایج
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_FETCHES)
    connector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT_FETCHES,
        limit_per_host=3,         # حداکثر ۳ اتصال همزمان به یک هاست
        ttl_dns_cache=300,        # کش DNS برای ۵ دقیقه
        force_close=True,
    )

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            _fetch_one(session, semaphore, name, url, group)
            for name, url, group in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    success_count = sum(1 for r in results if r["success"])
    fail_count    = len(results) - success_count
    total_items   = sum(len(r["items"]) for r in results)

    logger.info(
        "📡 دریافت تمام شد: %d موفق / %d ناموفق / %d آیتم کل",
        success_count, fail_count, total_items
    )
    return results


def fetch_all(sources: list[tuple]) -> list[dict]:
    """
    رابط همزمان (synchronous wrapper) برای fetch_all_async.
    از bot.py صدا زده می‌شود.
    """
    return asyncio.run(fetch_all_async(sources))
