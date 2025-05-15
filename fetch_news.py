import feedparser
import json
import datetime

def get_high_impact_events():
    feed_url = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
    feed = feedparser.parse(feed_url)
    timestamps = []
    for entry in feed.entries:
        if '<span class="sprite sprite-common sprite-high-impact">' in entry.summary:
            try:
                dt = datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M %Z")
            except ValueError:
                dt = datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
            unix_ts = int(dt.timestamp())
            timestamps.append(unix_ts)
    return timestamps

timestamps = get_high_impact_events()

with open("high_impact_news.json", "w") as f:
    json.dump(timestamps, f, indent=2)

