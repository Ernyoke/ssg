from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal


@dataclass
class Frame:
    file: str
    frame: Path


@dataclass
class RssFeed:
    title: str
    description: str
    link: str
    feed_url: str
    language: str
    matcher: str
    limit: Optional[int]
    outputLocation: Path


@dataclass
class Config:
    """
    Data class for holding data from config.json file.
    """
    source: Path
    destination: Path
    baseHref: str
    hostname: str
    exclude: list[str]
    frames: list[Frame]
    rssFeeds: list[RssFeed] = field(default_factory=list)

    @staticmethod
    def from_json(json_config: dict) -> Config:
        """
        Build a Config object from a dictionary containing the input from config.json.
        :param json_config: config.json content as a dictionary
        :return: Config object
        """
        required_fields = ['source', 'destination', 'baseHref', 'hostname']
        if not all(map(lambda conf: conf in json_config, required_fields)):
            raise Exception("Required field is missing from config.json!")

        frames = [Frame(frame['file'], Path(frame['frame'])) for frame in json_config['frames']]

        rss_feeds = [
            RssFeed(
                title=feed['title'],
                description=feed['description'],
                link=feed['link'],
                feed_url=feed['feed_url'],
                language=feed['language'],
                matcher=feed['matcher'],
                limit=feed.get('limit'),
                outputLocation=Path(feed['outputLocation']),
            )
            for feed in json_config.get('rssFeeds', [])
        ]

        return Config(source=Path(json_config['source']),
                      destination=Path(json_config['destination']),
                      hostname=json_config['hostname'],
                      baseHref=json_config['baseHref'],
                      exclude=json_config.get('exclude', ['.git', 'ignore', 'README.md']),
                      frames=frames,
                      rssFeeds=rss_feeds)


def read_config(path: Path) -> Config:
    """
    Read the configuration JSON file and transform it into a Config object.
    :param path: path of the config file
    :return: a Config object with all the properties from the config file.
    """
    with open(path, 'r', encoding='utf-8') as file:
        config = json.load(file)
        return Config.from_json(config)
