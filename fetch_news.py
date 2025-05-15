import sys
import traceback
import feedparser
import json
import datetime

try:
    def get_high_impact_events():
        print(">>> Running updated get_high_impact_events()")  # Debug to confirm running new code
        feed_url = "https://www.myfxbook.com/rss/forex-economic-calendar-events"
        feed = feedparser.parse(feed_url)
        events = []
        for entry in feed.entries:
            # Example: checking for high impact by matching the icon or keyword
            if '<span class="sprite sprite-common sprite-high-impact">' in entry.summary:
                published_str = entry.published
                try:
                    # Try with seconds first
                    dt = datetime.datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S %Z")
                except ValueError:
                    print(f"First parse failed for '{published_str}', trying fallback without seconds")
                    # Try without seconds fallback
                    try:
                        dt = datetime.datetime.strptime(published_str, "%a, %d %b %Y %H:%M %Z")
                    except Exception as e:
                        print(f"Failed to parse datetime '{published_str}': {e}")
                        continue  # Skip this entry if date can't be parsed

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
