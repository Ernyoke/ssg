from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class Meta:
    """Meta class"""
    title: str
    image: str
    description: str
    url: str


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
            meta = Meta(title=meta_dict.get('og:title', ''),
                        image=meta_dict.get('og:image', ''),
                        description=meta_dict.get('og:description', ''),
                        url=meta_dict.get('og:url', ''))

        frames = [Frame(frame['file'], Path(frame['frame'])) for frame in json['frames']]

        return Config(source=Path(json['source']),
                      destination=Path(json['destination']),
                      base_href=json['baseHref'],
                      exclude=json.get('exclude', ['.git', 'ignore', 'README.md']),
                      meta=meta,
                      frames=frames)
