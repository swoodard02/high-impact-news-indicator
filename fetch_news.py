import feedparser
import datetime
import json

RSS_URL = "https://www.myfxbook.com/rss/forex-economic-calendar-events"

def get_high_impact_events():
    feed = feedparser.parse(RSS_URL)
    high_impact_events = []
    
    for entry in feed.entries:
        if 'sprite-high-impact' in entry.summary:
            # Parse datetime from entry
            dt = datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M %Z")
            iso_format = dt.isoformat() + "Z"  # Append 'Z' for UTC
            high_impact_events.append(iso_format)

    return high_impact_events

# Save the events to a JSON file
if __name__ == "__main__":
    events = get_high_impact_events()
    with open("high_impact_news.json", "w") as f:
        json.dump(events, f, indent=2)
    print(f"Saved {len(events)} events to high_impact_news.json")
