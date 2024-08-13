import fnmatch
import glob
from pathlib import Path
from typing import Optional

from config import Config, MetaFields
from fileprocessor.frame import Frame
from fileprocessor.html_file import HTMLFile
from fileprocessor.markdown_file import MarkDownFile


class MarkdownFileProcessor:
    """
    Used to transform markdown files into html files.
    """

    def __init__(self, directory: Path, file_name: str, destination_dir: Path, config: Config, frames_cache: [Frame]):
        self.file_name = file_name
        self.destination_dir = destination_dir
        self.path = directory / Path(file_name)
        self.config = config
        self.frames_cache = frames_cache

    def render_html(self, relative_dir: Path):
        """
        Open markdown file and render it as HTML file. Prepend a header to this HTML file and append a footer to it.
        """
        frame = self._get_frame_for_file()
        md_file = MarkDownFile.read_from_file(self.path)
        html_file = HTMLFile(frame.embed_content(md_file.convert_to_html()))
        html_file.add_target_blank_to_external_urls(self.config.base_href)
        html_file.add_anchor_links()

        meta = None
        for matcher in self.config.meta.matchers:
            if fnmatch.fnmatch(self.path.as_posix(), matcher.file):
                if matcher.action == 'TAKE_FROM_CONTENT':
                    title = md_file.get_title()
                    cover_image = self._get_cover_image(relative_dir)

                    if cover_image is not None:
                        cover_image = str(cover_image.as_posix())

                    meta = MetaFields(title=title, image=cover_image, description=None, url=None)
                elif matcher.action == 'STATIC':
                    title = matcher.meta_fields.title
                    cover_image = matcher.meta_fields.image
                    meta = MetaFields(title=title, image=cover_image, description=None, url=None)
                break

        if meta is not None and meta.title is not None:
            html_file.set_title(meta.title, self.config.hostname)

        html_file.insert_og_meta(self.config.meta.default, self.config.base_href, meta)

        destination_path = self.destination_dir / Path(f'{Path(self.file_name).stem}.html')
        html_file.write(destination_path)
        print(f'Rendered {destination_path.as_posix()}')

    def _get_frame_for_file(self) -> Frame:
        """
        Return the frame for a markdown file as a string.
        """
        frame_path = None
        for f in self.config.frames:
            if fnmatch.fnmatch(self.path.as_posix(), f.file):
                frame_path = f.frame
                break

        if not frame_path:
            raise AssertionError(f'No frame found for {self.path}')

        if frame_path in self.frames_cache:
            return self.frames_cache[frame_path]

        frame = Frame.read_from_file(frame_path)
        frame.set_base_path(self.config.base_href)
        self.frames_cache[frame_path] = frame
        return self.frames_cache[frame_path]

    def _get_cover_image(self, destination_dir: Path) -> Optional[Path]:
        """
        Returns the path of the cover image if it exists.
        :return: relative path to the cover image if it exists
        """
        accepted_image_extensions = ('.tif', '.tiff', '.jpg', '.jpeg', '.gif', '.png', '.eps', ".bmp", '.ppm', '.heif',
                                     '.avif')
        img_folder_path = self.path.parent.absolute() / Path(f'img-{self.path.stem}')
        pattern = img_folder_path / Path('cover.*')
        files = glob.glob(pattern.as_posix())
        covers = []
        for file in files:
            for extension in accepted_image_extensions:
                if file.endswith(extension):
                    covers.append(Path(file).name)

        if len(covers) == 0:
            return None

        if len(covers) > 1:
            print(f'Warning! Multiple cover images found for {self.path}! Choosing {covers[0]}')

        return destination_dir / Path(f'img-{self.path.stem}') / Path(covers[0])
