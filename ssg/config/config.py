from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Meta:
    """Meta class"""
    title: str
    image: str
    description: str
    url: str


@dataclass
class Config:
    """
    Data class for holding data from config.json file.
    """
    source: Path
    destination: Path
    base_href: str
    frame_name: str
    exclude: [str]
    meta: Optional[Meta]

    @staticmethod
    def from_json(json: dict):
        """
        Build a Config object from a dictionary containing the input from config.json.
        """
        required_fields = ['source', 'destination', 'baseHref']
        if not all(map(lambda field: field in json, required_fields)):
            raise Exception("Required field is missing from config.json!")

        default_frame_name = 'frame.html'

        meta = None
        if 'meta' in json:
            meta_dict = json['meta']
            meta = Meta(title=meta_dict.get('og:title', ''),
                        image=meta_dict.get('og:image', ''),
                        description=meta_dict.get('og:description', ''),
                        url=meta_dict.get('og:url', ''))

        return Config(source=Path(json['source']),
                      destination=Path(json['destination']),
                      base_href=json['baseHref'],
                      frame_name=json.get('frameName', default_frame_name),
                      exclude=json.get('exclude', [default_frame_name, '.git', 'ignore', 'README.md']),
                      meta=meta)
