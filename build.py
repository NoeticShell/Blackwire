#!/usr/bin/env python3
import feedparser
from datetime import datetime, timezone
import html
import re
import socket

# -------------------------
# GLOBAL SAFETY
# -------------------------
# Prevent hanging on flaky feeds
socket.setdefaulttimeout(20)

# -------------------------
# FEEDS (LOCKED IN)
# -------------------------
WEATHER_FEEDS = [
    ("San Antonio / Austin (NWS EWX)", "https://www.weather.gov/rss_page.php?site_name=ewx"),
    ("US Weather Headlines (NWS)", "https://www.weather.gov/rss_page.php?site_name=nws"),
    ("Global Climate Highlights (NOAA Climate.gov)", "https://www.climate.gov/feeds/news.xml"),
]

NEWS_FEEDS = [
    ("War Room", "https://listen.warroom.org/feed.xml"),
    ("InfoWars", "https://www.infowars.com/rss.xml"),
    ("The Debrief", "https://thedebrief.org/feed/"),
    ("America First (Nick Fuentes)", "https://feed.podbean.com/wanghaf/feed.xml"),
    ("The Gateway Pundit", "https://www.thegatewaypundit.com/feed/"),
    ("The Black Vault", "https://www.theblackvault.com/documentarchive/feed/"),
    ("Project Veritas", "https://projectveritas.podomatic.com/rss2.xml"),
]

MAX_PER_FEED = 10

# Simple color rotation (w3m-friendly)
COLORS = [
    "#00ff66",
    "#66ccff",
    "#ffcc66",
    "#ff66cc",
    "#ccccff",
    "#66ffcc",
    "#ff6666",
]

def esc(s: str) -> str:
    return html.escape(s or "")

def entry_link(e):
    return (
        getattr(e, "link", None)
        or (e.get("links", [{}])[0].get("href") if e.get("links") else "")
    )

def icon_for(title: str):
    """
    w3m-safe ASCII markers.
    """
    t = (title or "").lower()

    severe = [
        "warning", "tornado", "hurricane", "extreme",
        "life-threatening", "flash flood",
        "winter storm warning", "blizzard",
        "severe thunderstorm warning"
    ]
    watch = ["watch", "tornado watch", "hurricane watch"]
    advisory = ["advisory", "statement", "outlook"]

    if any(k in t for k in severe):
        return "(!)"
    if any(k in t for k in watch):
        return "(*)"
    if any(k in t for k in advisory):
        return "(i)"
    return "(>)"

def write_section(parts, title, feeds):
    parts.append(f"<h2>{esc(title)}</h2>")
    parts.append("<hr>")

    for i, (name, url) in enumerate(feeds):
        color = COLORS[i % len(COLORS)]

        # ---- FAIL-SOFT FEED PARSE ----
        try:
            d = feedparser.parse(
                url,
                request_headers={"User-Agent": "BlackwireRSS/1.0"}
            )
        except Exception as ex:
            parts.append(
                f"<p><b><font color='{color}'>{esc(name)}</font></b><br>"
                f"<small>{esc(url)}</small></p>"
            )
            parts.append(f"<p><i>Feed error: {esc(str(ex))}</i></p>")
            parts.append("<hr>")
            continue

        # Source header
        parts.append(
            f"<p><b><font color='{color}'>{esc(name)}</font></b><br>"
            f"<small>{esc(url)}</small></p>"
        )

        if getattr(d, "bozo", False):
            parts.append("<p><i>Feed parse issue (partial data).</i></p>")

        parts.append("<ul>")
        for e in (d.entries or [])[:MAX_PER_FEED]:
            title_txt = getattr(e, "title", "Untitled")
            mark = icon_for(title_txt)
            link = esc(entry_link(e))
            title_html = esc(title_txt)
            title_html = re.sub(r"\s+", " ", title_html).strip()

            if link:
                parts.append(
                    f"<li>{esc(mark)} <a href='{link}'>{title_html}</a></li>"
                )
            else:
                parts.append(f"<li>{esc(mark)} {title_html}</li>")
        parts.append("</ul>")
        parts.append("<hr>")

def main(out_path="index.html"):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    parts = []
    parts.append("<!doctype html>")
    parts.append("<html><head><meta charset='utf-8'>")
    parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    parts.append("<title>Blackwire</title></head><body>")
    parts.append("<h1>Blackwire</h1>")
    parts.append(f"<p><small>Updated: {esc(now)}</small></p>")

    # Weather first
    write_section(parts, "Weather", WEATHER_FEEDS)

        # News second
    write_section(parts, "News", NEWS_FEEDS)

    # -------------------------
    # SECURE CONTACT FOOTER
    # -------------------------
    parts.append("<h2>Secure Contact</h2>")
    parts.append("<hr>")
    parts.append("<pre>")
    parts.append("Blackwire Secure Channel\n")
    parts.append("Matrix (End-to-End Encryption Capable)")
    parts.append("Direct: @nsblackwire:matrix.org")
    parts.append("Room:   #blackwire:matrix.org\n")
    parts.append("Federated • Encrypted • Open Protocol")
    parts.append("</pre>")
    parts.append("<hr>")

    parts.append("</body></html>")


    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

if __name__ == "__main__":
    main("index.html")
