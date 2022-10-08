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
    folder: Path
    frame: str


@dataclass
class Config:
    """
    Data class for holding data from config.json file.
    """
    source: Path
    destination: Path
    base_href: str
    default_frame: str
    exclude: [str]
    meta: Optional[Meta]
    frames: List[Frame]

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

        frames = [Frame(Path(json['source']) / Path(frame['folder']), frame['frame']) for frame in json['frames']]

        return Config(source=Path(json['source']),
                      destination=Path(json['destination']),
                      base_href=json['baseHref'],
                      default_frame=json.get('frameName', default_frame_name),
                      exclude=json.get('exclude', ['.git', 'ignore', 'README.md']),
                      meta=meta,
                      frames=frames)
