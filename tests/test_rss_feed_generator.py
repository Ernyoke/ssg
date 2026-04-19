import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest import TestCase
from xml.etree import ElementTree as ET

from ssg.content.article import Article, Author
from ssg.content.markdown_file import MarkDownFile
from ssg.config.config import RssFeed
from ssg.dirtree.file_node import FileNode
from ssg.rss.rss_feed_generator import FeedItem, RssFeedGenerator


def _make_rss_config(
    title: str = "All Posts",
    description: str = "All posts feed",
    link: str = "https://example.com/",
    feed_url: str = "https://example.com/rss.xml",
    language: str = "en",
    matcher: str = "*.md",
    limit: int | None = None,
    output_location: str | Path = "rss.xml",
) -> RssFeed:
    return RssFeed(
        title=title,
        description=description,
        link=link,
        feed_url=feed_url,
        language=language,
        matcher=matcher,
        limit=limit,
        outputLocation=Path(output_location),
    )


def _make_article_mock(
    title: str = "Post Title",
    description: str = "Post description",
    url: str = "https://example.com/post",
    last_edited: datetime | None = None,
    author_name: str = "Jane Doe",
    author_email: str = "jane@example.com",
    twitter_handle: str = "@johndoe",
) -> Article:
    return Article(
        markdown=MarkDownFile(""),
        title=title,
        description=description,
        url=url,
        last_edited=last_edited,
        author=Author(name=author_name, email=author_email, twitter_handle=twitter_handle),
    )


class TestRssFeedGeneratorInit(TestCase):
    def test_configs_keyed_by_title(self):
        """The generator must store rss configs in a dict keyed by their title."""
        cfg_a = _make_rss_config(title="Feed A")
        cfg_b = _make_rss_config(title="Feed B")

        gen = RssFeedGenerator([cfg_a, cfg_b])

        self.assertIn("Feed A", gen.rss_feed_configs)
        self.assertIn("Feed B", gen.rss_feed_configs)
        self.assertIs(gen.rss_feed_configs["Feed A"], cfg_a)
        self.assertIs(gen.rss_feed_configs["Feed B"], cfg_b)

    def test_feeds_starts_empty(self):
        """Feeds dict starts empty and returns an empty list for unknown ids (defaultdict)."""
        gen = RssFeedGenerator([])
        self.assertEqual(len(gen.feeds), 0)
        self.assertEqual(gen.feeds["unknown"], [])

    def test_duplicate_titles_overwrite(self):
        """When two configs share the same title, the latter overrides the former."""
        cfg_a = _make_rss_config(title="Same", description="first")
        cfg_b = _make_rss_config(title="Same", description="second")

        gen = RssFeedGenerator([cfg_a, cfg_b])

        self.assertEqual(len(gen.rss_feed_configs), 1)
        self.assertIs(gen.rss_feed_configs["Same"], cfg_b)


class TestRssFeedGeneratorAddToFeed(TestCase):
    def test_article_added_when_matcher_matches(self):
        """Articles whose file path matches the matcher must be appended to the feed."""
        cfg = _make_rss_config(title="Posts", matcher="posts/*.md")
        gen = RssFeedGenerator([cfg])

        file_node = FileNode(Path("posts/hello.md"))
        article = _make_article_mock(
            title="Hello",
            last_edited=datetime(2025, 1, 1, tzinfo=UTC),
        )

        gen.add_to_feed(file_node, article)

        self.assertEqual(len(gen.feeds["Posts"]), 1)
        item = gen.feeds["Posts"][0]
        self.assertIsInstance(item, FeedItem)
        self.assertEqual(item.title, "Hello")
        self.assertEqual(item.description, "Post description")
        self.assertEqual(item.link, "https://example.com/post")
        self.assertEqual(item.guid, "https://example.com/post")
        self.assertEqual(item.pubDate, datetime(2025, 1, 1, tzinfo=UTC))
        self.assertEqual(item.author_name, "Jane Doe")
        self.assertEqual(item.author_email, "jane@example.com")

    def test_article_not_added_when_matcher_does_not_match(self):
        """Articles whose file path does not match the matcher must be skipped."""
        cfg = _make_rss_config(title="Posts", matcher="posts/*.md")
        gen = RssFeedGenerator([cfg])

        gen.add_to_feed(FileNode(Path("pages/about.md")), _make_article_mock())

        self.assertEqual(len(gen.feeds["Posts"]), 0)

    def test_article_added_to_multiple_matching_feeds(self):
        """A single article must be added to every feed whose matcher matches."""
        cfg_all = _make_rss_config(title="All", matcher="*.md")
        cfg_posts = _make_rss_config(title="Posts", matcher="posts/*.md")
        cfg_pages = _make_rss_config(title="Pages", matcher="pages/*.md")
        gen = RssFeedGenerator([cfg_all, cfg_posts, cfg_pages])

        gen.add_to_feed(FileNode(Path("posts/hello.md")), _make_article_mock())

        self.assertEqual(len(gen.feeds["All"]), 1)
        self.assertEqual(len(gen.feeds["Posts"]), 1)
        self.assertEqual(len(gen.feeds["Pages"]), 0)

    def test_multiple_articles_accumulate_in_feed(self):
        """Successive add_to_feed calls must accumulate items in a feed."""
        cfg = _make_rss_config(title="Posts", matcher="*.md")
        gen = RssFeedGenerator([cfg])

        for i in range(3):
            gen.add_to_feed(
                FileNode(Path(f"post-{i}.md")),
                _make_article_mock(title=f"Post {i}", url=f"https://example.com/{i}"),
            )

        self.assertEqual([item.title for item in gen.feeds["Posts"]], ["Post 0", "Post 1", "Post 2"])


class TestRssFeedGeneratorGenerateFeeds(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.destination = Path(self.temp_dir.name)

    @staticmethod
    def _add_article(gen: RssFeedGenerator, path: str, *, title: str, when: datetime | None):
        gen.add_to_feed(
            FileNode(Path(path)),
            _make_article_mock(title=title, url=f"https://example.com/{title}", last_edited=when),
        )

    @staticmethod
    def _parse_titles(rss_path: Path) -> list[str]:
        root = ET.fromstring(rss_path.read_bytes())
        return [item.findtext("title") for item in root.iter("item")]

    def test_generates_rss_file_at_destination(self):
        """A valid RSS XML file must be written to destination/outputLocation."""
        cfg = _make_rss_config(title="Posts", matcher="*.md", output_location="rss.xml")
        gen = RssFeedGenerator([cfg])
        self._add_article(gen, "post.md", title="Hello", when=datetime(2025, 1, 1, tzinfo=UTC))

        gen.generate_feeds(self.destination)

        out = self.destination / "rss.xml"
        self.assertTrue(out.exists())
        root = ET.fromstring(out.read_bytes())
        self.assertEqual(root.tag, "rss")
        channel = root.find("channel")
        self.assertIsNotNone(channel)
        self.assertEqual(channel.findtext("title"), "Posts")
        self.assertEqual(channel.findtext("description"), "All posts feed")
        self.assertEqual(channel.findtext("language"), "en")

    def test_items_sorted_by_pub_date_ascending(self):
        """Items in the generated feed must be sorted by pubDate descending."""
        cfg = _make_rss_config(title="Posts", matcher="*.md")
        gen = RssFeedGenerator([cfg])
        self._add_article(gen, "b.md", title="B", when=datetime(2025, 3, 1, tzinfo=UTC))
        self._add_article(gen, "a.md", title="A", when=datetime(2025, 1, 1, tzinfo=UTC))
        self._add_article(gen, "c.md", title="C", when=datetime(2025, 2, 1, tzinfo=UTC))

        gen.generate_feeds(self.destination)

        self.assertEqual(["B", "C", "A"], self._parse_titles(self.destination / "rss.xml"))

    def test_limit_truncates_items(self):
        """When limit is set, only the first N (after sorting) items are written."""
        cfg = _make_rss_config(title="Posts", matcher="*.md", limit=2)
        gen = RssFeedGenerator([cfg])
        self._add_article(gen, "a.md", title="A", when=datetime(2025, 1, 1, tzinfo=UTC))
        self._add_article(gen, "b.md", title="B", when=datetime(2025, 2, 1, tzinfo=UTC))
        self._add_article(gen, "c.md", title="C", when=datetime(2025, 3, 1, tzinfo=UTC))

        gen.generate_feeds(self.destination)

        self.assertEqual(["C", "B"], self._parse_titles(self.destination / "rss.xml"))

    def test_no_limit_includes_all_items(self):
        """When limit is None, every item with a pubDate must be included."""
        cfg = _make_rss_config(title="Posts", matcher="*.md", limit=None)
        gen = RssFeedGenerator([cfg])
        for i in range(5):
            self._add_article(
                gen, f"post-{i}.md", title=f"P{i}",
                when=datetime(2025, 1, i + 1, tzinfo=UTC),
            )

        gen.generate_feeds(self.destination)

        self.assertEqual(len(self._parse_titles(self.destination / "rss.xml")), 5)

    def test_items_without_pub_date_are_skipped(self):
        """Items whose pubDate is None must not be written to the feed."""
        cfg = _make_rss_config(title="Posts", matcher="*.md")
        gen = RssFeedGenerator([cfg])
        self._add_article(gen, "a.md", title="A", when=datetime(2025, 1, 1, tzinfo=UTC))
        self._add_article(gen, "b.md", title="B", when=None)

        gen.generate_feeds(self.destination)

        self.assertEqual(self._parse_titles(self.destination / "rss.xml"), ["A"])

    def test_multiple_feeds_written_to_distinct_locations(self):
        """Each configured feed must be written to its own outputLocation."""
        cfg_a = _make_rss_config(title="A", matcher="a/*.md", output_location="a.xml")
        cfg_b = _make_rss_config(title="B", matcher="b/*.md", output_location="b.xml")
        gen = RssFeedGenerator([cfg_a, cfg_b])
        self._add_article(gen, "a/post.md", title="From A", when=datetime(2025, 1, 1, tzinfo=UTC))
        self._add_article(gen, "b/post.md", title="From B", when=datetime(2025, 1, 2, tzinfo=UTC))

        gen.generate_feeds(self.destination)

        self.assertEqual(self._parse_titles(self.destination / "a.xml"), ["From A"])
        self.assertEqual(self._parse_titles(self.destination / "b.xml"), ["From B"])

    def test_item_fields_written_to_xml(self):
        """Title, description, link, guid and author of an item must be present in the XML."""
        cfg = _make_rss_config(title="Posts", matcher="*.md")
        gen = RssFeedGenerator([cfg])
        gen.add_to_feed(
            FileNode(Path("post.md")),
            _make_article_mock(
                title="Hello",
                description="A greeting",
                url="https://example.com/hello",
                last_edited=datetime(2025, 5, 5, tzinfo=UTC),
                author_name="Jane Doe",
                author_email="jane@example.com",
            ),
        )

        gen.generate_feeds(self.destination)

        root = ET.fromstring((self.destination / "rss.xml").read_bytes())
        item = next(root.iter("item"))
        self.assertEqual(item.findtext("title"), "Hello")
        self.assertEqual(item.findtext("description"), "A greeting")
        self.assertEqual(item.findtext("link"), "https://example.com/hello")
        self.assertEqual(item.findtext("guid"), "https://example.com/hello")
        author_text = item.findtext("author") or ""
        self.assertIn("jane@example.com", author_text)
        self.assertIn("Jane Doe", author_text)

    def test_raises_when_destination_missing(self):
        """Writing to a non-existent destination directory must raise an OSError."""
        cfg = _make_rss_config(title="Posts", matcher="*.md", output_location="rss.xml")
        gen = RssFeedGenerator([cfg])

        missing = self.destination / "does-not-exist"
        with self.assertRaises(OSError):
            gen.generate_feeds(missing)

