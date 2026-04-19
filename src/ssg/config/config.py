from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal


@dataclass
class MetaFields:
    title: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    twitter_handle: Optional[str] = None


@dataclass
class Matcher:
    """Matcher rules for injecting meta fields"""
    file: str
    action: Literal['TAKE_FROM_CONTENT', 'STATIC', 'USE_DEFAULT']
    meta_fields: Optional[MetaFields] = None


@dataclass
class Meta:
    default: MetaFields
    matchers: list[Matcher]


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
    meta: Optional[Meta]
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

        meta = None
        if 'meta' in json_config:
            meta_dict = json_config['meta']
            if 'default' not in meta_dict:
                raise Exception("Required 'default' for `meta` is missing from config.json!")
            default_meta_dict = meta_dict['default']
            default = MetaFields(title=default_meta_dict.get('og:title', ''),
                                 image=default_meta_dict.get('og:image', ''),
                                 description=default_meta_dict.get('og:description', ''),
                                 url=default_meta_dict.get('og:url', ''),
                                 author_name=default_meta_dict.get('og:author', ''),
                                 author_email=default_meta_dict.get('author_email', ''),
                                 twitter_handle=default_meta_dict.get('twitter_handle', ''))
            matchers = []
            for m in meta_dict.get('matchers', []):
                if m['action'] == 'STATIC':
                    if 'meta' not in m:
                        raise Exception('Meta fields are required for STATIC matcher!')
                    fields = m['meta']
                    meta_fields = MetaFields(title=fields.get('og:title', None),
                                             image=fields.get('og:image', None),
                                             description=fields.get('og:description', None),
                                             url=fields.get('og:url', None),
                                             author_name=fields.get('og:author', None),
                                             author_email=fields.get('author_email', None),
                                             twitter_handle=fields.get('twitter_handle', None))
                    matchers.append(Matcher(file=m['file'], action=m['action'], meta_fields=meta_fields))
                elif m['action'] == 'TAKE_FROM_CONTENT' or m['action'] == 'USE_DEFAULT':
                    matchers.append(Matcher(file=m['file'], action=m['action'], meta_fields=None))
                else:
                    raise Exception(f"Invalid action type {m['action']}")
            meta = Meta(default=default, matchers=matchers)

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
                      meta=meta,
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
