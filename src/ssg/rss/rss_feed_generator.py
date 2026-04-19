import fnmatch
import mimetypes
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from feedgen.feed import FeedGenerator

from ssg.config import RssFeed
from ssg.content.article import Article
from ssg.dirtree.file_node import FileNode


@dataclass
class FeedItem:
    """A single entry in an RSS feed."""

    title: str
    description: str
    link: str
    guid: str
    pubDate: datetime | None
    cover_image: str | None
    author_name: str | None
    author_email: str | None


class RssFeedGenerator:
    """Collects articles and generates RSS feeds based on configured matchers."""

    def __init__(self, rss_feed_configs: list[RssFeed]):
        """Initialize with a list of RSS feed configurations, keyed by title."""
        self.rss_feed_configs: dict[str, RssFeed] = dict()

        for config in rss_feed_configs:
            self.rss_feed_configs[config.title] = config

        self.feeds: dict[str, list[FeedItem]] = defaultdict(list)

    def add_to_feed(self, file: FileNode, article: Article):
        """Append the article to every feed whose matcher matches the file path."""
        for feed_id, rss_feed_config in self.rss_feed_configs.items():
            if fnmatch.fnmatch(file.path.as_posix(), rss_feed_config.matcher):
                feed = self.feeds[feed_id]
                feed.append(FeedItem(
                    title=article.title,
                    description=article.description if article.description is not None else article.title,
                    link=article.url,
                    guid=article.url,
                    cover_image=article.cover_image,
                    pubDate=article.last_edited,
                    author_name=article.author.name,
                    author_email=article.author.email,
                ))
                self.feeds[feed_id] = feed

    def generate_feeds(self, destination_base_path: Path):
        """Write each configured RSS feed (sorted by pubDate, respecting limit) to disk under the given base path."""
        for feed_id, rss_feed_config in self.rss_feed_configs.items():
            feed_generator = FeedGenerator()
            feed_generator.title(rss_feed_config.title)
            feed_generator.description(rss_feed_config.description)
            feed_generator.link(href=rss_feed_config.link, rel="alternate")
            feed_generator.link(href=rss_feed_config.feed_url, rel="self")
            feed_generator.language(rss_feed_config.language)

            feed = [f for f in self.feeds[feed_id] if f.pubDate is not None]
            feed.sort(key=lambda x: x.pubDate, reverse=True)

            limit = rss_feed_config.limit if rss_feed_config.limit is not None else len(feed)

            for feed_item in feed[:limit]:
                entry = feed_generator.add_entry(order='append')
                entry.title(feed_item.title)
                entry.description(feed_item.description)
                entry.link({'href': feed_item.link})
                entry.guid(feed_item.guid, permalink=True)
                entry.pubDate(feed_item.pubDate)
                entry.author({'name': feed_item.author_name, 'email': feed_item.author_email})

                if feed_item.cover_image is not None:
                    mime, _ = mimetypes.guess_type(feed_item.cover_image)
                    entry.enclosure(url=feed_item.cover_image, length=0, type=mime)
            rss_content = feed_generator.rss_str(pretty=True)

            destination_path = destination_base_path / rss_feed_config.outputLocation
            with open(destination_path, mode='wb') as destination_file:
                destination_file.write(rss_content)
