import sys
import traceback

try:
    import feedparser
    import json
    import datetime
    
    def get_high_impact_events():
        feed_url = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
        feed = feedparser.parse(feed_url)
        events = []
        for entry in feed.entries:
            # Example: checking for high impact by matching the icon or keyword
            if '<span class="sprite sprite-common sprite-high-impact">' in entry.summary:
                try:
                    dt = datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
                except ValueError:
                    dt = datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M %Z")
                events.append({
                    "title": entry.title,
                    "date": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "impact": "high"
                })
        return events
    
    events = get_high_impact_events()
    
    with open("high_impact_news.json", "w") as f:
        json.dump(events, f, indent=2)

except Exception as e:
    print("Error occurred:", e)
    traceback.print_exc()
    sys.exit(1)
