from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

import json


@dataclass
class MetaFields:
    """Meta fields"""
    title: str
    image: str
    description: str
    url: str


@dataclass
class Matcher:
    """Matcher rules for injecting meta fields"""
    file: str
    compute_from_content: bool = False,


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
    def from_json(json: dict) -> Config:
        """
        Build a Config object from a dictionary containing the input from config.json.
        :param json: config.json content as a dictionary
        :return: Config object
        """
        required_fields = ['source', 'destination', 'baseHref']
        if not all(map(lambda field: field in json, required_fields)):
            raise Exception("Required field is missing from config.json!")

        meta = None
        if 'meta' in json:
            meta_dict = json['meta']
            if 'default' not in meta_dict:
                raise Exception("Required 'default' for `meta` is missing from config.json!")
            default_meta_dict = meta_dict['default']
            default = MetaFields(title=default_meta_dict.get('og:title', ''),
                                 image=default_meta_dict.get('og:image', ''),
                                 description=default_meta_dict.get('og:description', ''),
                                 url=default_meta_dict.get('og:url', ''))
            matchers = []
            for m in meta_dict.get('matchers', []):
                matchers.append(Matcher(file=m['file'], compute_from_content=m['computeFromContent']))
            meta = Meta(default=default, matchers=matchers)

        frames = [Frame(frame['file'], Path(frame['frame'])) for frame in json['frames']]

        return Config(source=Path(json['source']),
                      destination=Path(json['destination']),
                      hostname=json['hostname'],
                      base_href=json['baseHref'],
                      exclude=json.get('exclude', ['.git', 'ignore', 'README.md']),
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
