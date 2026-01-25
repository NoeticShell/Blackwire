#!/usr/bin/env python3
import feedparser
from datetime import datetime, timezone
import html
import re

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
COLORS = ["#00ff66", "#66ccff", "#ffcc66", "#ff66cc", "#ccccff", "#66ffcc", "#ff6666"]

def esc(s: str) -> str:
    return html.escape(s or "")

def entry_link(e):
    return getattr(e, "link", None) or (e.get("links",[{}])[0].get("href") if e.get("links") else "")

def icon_for(title: str):
    """
    w3m-safe markers. We use ASCII-first, with optional Unicode fallback.
    """
    t = (title or "").lower()

    # severe / urgent
    severe = [
        "warning", "tornado", "hurricane", "extreme", "life-threatening", "flash flood",
        "winter storm warning", "blizzard", "severe thunderstorm warning"
    ]
    watch = ["watch", "severe thunderstorm watch", "tornado watch", "hurricane watch"]
    advisory = ["advisory", "statement", "outlook", "special weather statement"]

    heat = ["heat", "excessive heat"]
    flood = ["flood", "flash flood"]
    winter = ["winter", "snow", "ice", "freeze", "blizzard"]
    wind = ["wind", "gale"]
    fire = ["fire", "red flag"]

    # Priority order:
    if any(k in t for k in severe):
        return "(!)"   # or "⚠" if you want riskier Unicode
    if any(k in t for k in watch):
        return "(*)"
    if any(k in t for k in advisory):
        return "(i)"
    if any(k in t for k in fire):
        return "(fire)"
    if any(k in t for k in heat):
        return "(heat)"
    if any(k in t for k in flood):
        return "(flood)"
    if any(k in t for k in winter):
        return "(cold)"
    if any(k in t for k in wind):
        return "(wind)"
    return "(>)"

def write_section(parts, title, feeds):
    parts.append(f"<h2>{esc(title)}</h2>")
    parts.append("<hr>")
    for i, (name, url) in enumerate(feeds):
        color = COLORS[i % len(COLORS)]
        d = feedparser.parse(url)

        # Source header (colored)
        parts.append(f"<p><b><font color='{color}'>{esc(name)}</font></b><br><small>{esc(url)}</small></p>")

        if getattr(d, "bozo", False):
            parts.append("<p><i>Feed parse issue (may still partially work).</i></p>")

        parts.append("<ul>")
        for e in (d.entries or [])[:MAX_PER_FEED]:
            title_txt = getattr(e, "title", "Untitled")
            mark = icon_for(title_txt)
            link = esc(entry_link(e))
            title_html = esc(title_txt)

            # Light cleanup (optional): collapse repeated whitespace
            title_html = re.sub(r"\s+", " ", title_html).strip()

            if link:
                parts.append(f"<li>{esc(mark)} <a href='{link}'>{title_html}</a></li>")
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
    parts.append("<title>Text Wire</title></head><body>")
    parts.append("<h1>Text Wire</h1>")
    parts.append(f"<p><small>Updated: {esc(now)}</small></p>")

    # Weather on top
    write_section(parts, "Weather", WEATHER_FEEDS)

    # News below
    write_section(parts, "News", NEWS_FEEDS)

    parts.append("</body></html>")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

if __name__ == "__main__":
    main("index.html")
