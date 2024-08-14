from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Literal


@dataclass
class MetaFields:
    """Meta fields"""
    title: Optional[str]
    image: Optional[str]
    description: Optional[str]
    url: Optional[str]
    twitter_handle: Optional[str]


@dataclass
class Matcher:
    """Matcher rules for injecting meta fields"""
    file: str
    action: Literal['TAKE_FROM_CONTENT', 'STATIC', 'USE_DEFAULT']
    meta_fields: Optional[MetaFields]


@dataclass
class Meta:
    """Meta class"""
    default: MetaFields
    matchers: [Matcher]


@dataclass
class Frame:
    file: str
    frame: Path


@dataclass
class Config:
    """
    Data class for holding data from config.json file.
    """
    source: Path
    destination: Path
    base_href: str
    hostname: str
    exclude: [str]
    meta: Optional[Meta]
    frames: List[Frame]

    @staticmethod
    def from_json(json_config: dict) -> Config:
        """
        Build a Config object from a dictionary containing the input from config.json.
        :param json_config: config.json content as a dictionary
        :return: Config object
        """
        required_fields = ['source', 'destination', 'baseHref']
        if not all(map(lambda field: field in json_config, required_fields)):
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
                                 twitter_handle=default_meta_dict.get('twitter_handle', ''),)
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
                                             twitter_handle=fields.get('twitter_handle', None))
                    matchers.append(Matcher(file=m['file'], action=m['action'], meta_fields=meta_fields))
                elif m['action'] == 'TAKE_FROM_CONTENT' or m['action'] == 'USE_DEFAULT':
                    matchers.append(Matcher(file=m['file'], action=m['action'], meta_fields=None))
                else:
                    raise Exception(f"Invalid action type {m['action']}")
            meta = Meta(default=default, matchers=matchers)

        frames = [Frame(frame['file'], Path(frame['frame'])) for frame in json_config['frames']]

        return Config(source=Path(json_config['source']),
                      destination=Path(json_config['destination']),
                      hostname=json_config['hostname'],
                      base_href=json_config['baseHref'],
                      exclude=json_config.get('exclude', ['.git', 'ignore', 'README.md']),
                      meta=meta,
                      frames=frames)


def read_config(path: Path) -> Config:
    """
    Read the configuration JSON file and transform it into a Config object.
    :param path: path of the config file
    :return: a Config object with all the properties from the config file.
    """
    with open(path, 'r') as file:
        config = json.load(file)
        return Config.from_json(config)
