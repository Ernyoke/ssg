import fnmatch
import glob
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

import bs4
import markdown
from bs4 import BeautifulSoup
from slugify import slugify

from ssg.config import Config
from ssg.fileprocessor.file_processor import FileProcessor


class MarkdownFileProcessor(FileProcessor):
    """
    Used to transform markdown files into html files.
    """
    def __init__(self, directory: Path, file_name: str, config: Config, frames_cache: [str]):
        super().__init__(directory, file_name)
        self.config = config
        self.frames_cache = frames_cache
        self.html_file_name = f'{Path(file_name).stem}.html'

    def render_html(self):
        """
        Open markdown file and render it as HTML file. Prepend a header to this HTML file and append a footer to it.
        """
        frame = self._get_frame_for_file()
        with open(self.path) as file:
            lines = []
            md = markdown.markdown(file.read(), extensions=['fenced_code', 'tables', 'sane_lists'])
            for line in frame.split('\n'):
                if '{{ content }}' in line:
                    md_lines = [f'{md_line}\n' for md_line in
                                self._add_target_blank_to_external_urls(self._replace_md_with_html(md)).split('\n')]
                    lines.extend(md_lines)
                else:
                    lines.append(line)
            soup = BeautifulSoup(''.join(lines), 'html.parser')
            self._add_anchor_links(soup)

            title, cover_image = None, None
            for matcher in self.config.meta.matchers:
                if fnmatch.fnmatch(self.path.as_posix(), matcher.file):
                    if matcher.compute_from_content:
                        title = self._get_title_from_page(soup)
                        cover_image = self._get_cover_image(self.directory, self.file_name)

                        if cover_image is not None:
                            cover_image = str(cover_image.as_posix())

                        if title is not None:
                            for titleElement in soup.find_all('title'):
                                titleElement.string = f'{title} - {self.config.hostname}'
                    break

            self._insert_og_meta(soup, title, cover_image)
            self.content = soup.prettify()

    def _get_frame_for_file(self) -> str:
        """
        Return the frame for a markdown file as a string.
        :return: HTML page rendered as string
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

        self.frames_cache[frame_path] = self._set_base_path(MarkdownFileProcessor._read_frame(frame_path))
        return self.frames_cache[frame_path]

    def _set_base_path(self, page: str) -> str:
        """
        Set base path for each link (href).
        :param page: the HTML content as a string
        :return: updated HTML content as string
        """
        soup = BeautifulSoup(page, 'html.parser')
        element_to_attribute = {
            'a': 'href',
            'link': 'href',
            'script': 'src',
            'img': 'src'
        }
        for element, attribute in element_to_attribute.items():
            self._set_base_path_for_elements(soup.find_all(element), attribute)
        return str(soup)

    def _set_base_path_for_elements(self, elements: bs4.element.ResultSet, attribute: str) -> None:
        """
        Set the base path for the content of the attribute (href, src)
        :param elements: HTML element, can be <a>, <link>, <script>, <img>
        :param attribute: Attribute of the HTML element (href, src)
        :return: None
        """
        for element in filter(lambda elem: elem.has_attr(attribute), elements):
            url = element[attribute]
            if not bool(urlparse(url).netloc):
                element[attribute] = urljoin(self.config.base_href, url)

    @staticmethod
    def _read_frame(path: Path) -> str:
        """
        Read a frame file and return its content as a string.
        :param path: path of the frame file
        :return: content of the frame file as string
        """
        if path.exists():
            with open(path) as file:
                return file.read()
        else:
            raise Exception('Frame not found in the root folder!')

    def _add_target_blank_to_external_urls(self, html_doc: str) -> str:
        """
        Add target="_blank" to <a> tags.
        :param html_doc: HTML document as string
        :return: HTML document as a string
        """
        soup = BeautifulSoup(html_doc, 'html.parser')
        for a in soup.find_all('a'):
            url = a['href']
            # Check if url is absolute and does not start with a base path
            if bool(urlparse(url).netloc) and not url.startswith(self.config.base_href):
                a['target'] = '_blank'
        return str(soup)

    @staticmethod
    def _replace_md_with_html(html_doc: str) -> str:
        """
        Replace href attributes which end with .md (Markdown) with attributes which end with .html.
        :param html_doc: HTML document as a string
        :return: HTML document as a string
        """
        soup = BeautifulSoup(html_doc, 'html.parser')
        for a in soup.find_all('a'):
            url = a['href']
            if url.endswith('.md'):
                a['href'] = url.replace('.md', '.html')
        return str(soup)

    @staticmethod
    def _add_anchor_links(soup: BeautifulSoup):
        """
        Add anchor links to headings.
        :param soup: HTML document as a BeautifulSoup object
        """
        for title in soup.find_all('h2'):
            anchor_tag = soup.new_tag('a', attrs={'class': 'anchor-link',
                                                  'href': f'#{slugify(title.text)}',
                                                  'id': f'{slugify(title.text)}'})
            anchor_tag.string = '<<'
            title.append(anchor_tag)

    def _insert_og_meta(self, soup: BeautifulSoup,
                        title: Optional[str] = None,
                        cover_image: Optional[str] = None):
        """
        Add og:meta fields to the header of an HTML page.
        :param soup: HTML page as a BeautifulSoup object
        :param title: override for og:title
        :param cover_image: override for og:cover_image
        :return: updated HTML page as a string
        """
        meta = self.config.meta.default
        if meta:
            head = soup.find('head')
            if meta.title:
                meta_title = soup.new_tag('meta', attrs={
                    'property': 'og:title',
                    'content': title if title else meta.title
                })
                head.append(meta_title)
            if meta.description:
                meta_description = soup.new_tag('meta', attrs={
                    'property': 'og:description',
                    'content': meta.description
                })
                head.append(meta_description)
            if meta.url:
                meta_url = soup.new_tag('meta', attrs={
                    'property': 'og:url',
                    'content': meta.url
                })
                head.append(meta_url)
            if cover_image:
                meta_image = soup.new_tag('meta', attrs={
                    'property': 'og:image',
                    'content': urljoin(self.config.base_href, cover_image)
                })
                head.append(meta_image)
            elif meta.image:
                meta_image = soup.new_tag('meta', attrs={
                    'property': 'og:image',
                    'content': urljoin(self.config.base_href, meta.image)
                })
                head.append(meta_image)

    @staticmethod
    def _get_title_from_page(soup: BeautifulSoup) -> Optional[str]:
        """
        Attempts to infer the title from the HTML page. It will look for h1, h2...h6 tags and return the first one found
        in the page.
        :param soup: HTML page as a BeautifulSoup object
        :return: Title of the page as a string
        """
        element = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if element is not None:
            return element.text
        return None

    @staticmethod
    def _get_cover_image(current_directory: Path, file_name: str) -> Optional[Path]:
        """
        Returns the path of the cover image if it exists.
        :param current_directory: directory
        :param file_name: name of the current file
        :return: relative path to the cover image if it exists
        """
        accepted_image_extensions = (".tif", ".tiff", ".jpg", ".jpeg", ".gif", ".png", ".eps", ".bmp", ".ppm", ".heif")
        path = current_directory / file_name
        if not path.is_file():
            print(f'Error: could not get cover image for ${path}. Expected to be a file, it is a directory!')
            return None
        img_folder_path = path.parent.absolute() / Path(f'img-{path.stem}')
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
            print(f'Warning! Multiple cover images found for {path}! Choosing {covers[0]}')

        return current_directory / Path(f'img-{path.stem}') / Path(covers[0])

    def write_file(self, destination_directory: Path) -> None:
        destination_path = destination_directory / Path(self.html_file_name)
        super().write_file(destination_path)
