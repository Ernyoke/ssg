from pathlib import Path
import json
from datetime import datetime

from rfeed import Feed, Item

from config import Config


class RSSBuilder:
    def __init__(self, config: Config):
        self.config = config
        self._items = []
        self._publish_dates = self._init_publish_dates()
        self._feed = Feed(
            title = "ervinszilagyi.dev RSS Feed",
            description="Blog posts by Ervin Szilagyi",
            language='en - US',
            link='https://ervinszilagyi.dev/rss',
            items=self._items,
            lastBuildDate=datetime.today()
        )

    def _init_publish_dates(self):
        with open(self.config.rss.publish_dates, 'r') as file:
            return json.load(file)

    def create_item_if_match(self, original_path: Path, title: str, filename: str, link: str, author: str):
        if original_path.match(self.config.rss.match):
            if title not in self._publish_dates:
                print(f'Warning! No publish date found for "{filename}"!')
                return

            pub_date = datetime.strptime(self._publish_dates[title], "%Y-%m-%d")
            item = Item(
                title = title,
                link = link,
                author = author,
                pubDate=pub_date,
                guid=filename,
            )
            self._items.append(item)

    def render_rss(self, destination_path: Path):
        rss_xml = self._feed.rss()
        with open(destination_path, "w", encoding="utf-8") as file:
            file.write(rss_xml)