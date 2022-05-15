import os
from urllib.parse import urlparse, urljoin
from pathlib import Path

import markdown
import bs4
from bs4 import BeautifulSoup
from slugify import slugify


def generate(source: Path, destination: Path, base_path: str) -> None:
    """
    Entry point. Generate a new static site project by traversing the source directory and transforming Markdown files
    into HTML.
    """
    frame_name = 'frame.html'
    traverse_directory(source_directory=source,
                       destination_directory=destination,
                       frame=set_base_path(read_frame(source, frame_name), base_path),
                       exclude=[frame_name, '.git', 'ignore', 'README.md'],
                       base_href=base_path)


def read_frame(path: Path, file_name: str = 'frame.html') -> str:
    if file_name in os.listdir(path):
        with open(path / Path(file_name)) as file:
            return file.read()
    else:
        raise Exception('Frame not found in the root folder!')


def set_base_path(page: str, base_path: str) -> str:
    soup = BeautifulSoup(page, 'html.parser')
    element_to_attribute = {
        'a': 'href',
        'link': 'href',
        'script': 'src',
        'img': 'src'
    }
    for element, attribute in element_to_attribute.items():
        set_base_path_for_elements(soup.find_all(element), attribute, base_path)
    return str(soup)


def set_base_path_for_elements(elements: bs4.element.ResultSet, attribute: str, base_path: str) -> None:
    for element in filter(lambda elem: elem.has_attr(attribute), elements):
        url = element[attribute]
        if not is_absolute(url):
            element[attribute] = urljoin(base_path, url)


def is_absolute(url) -> bool:
    return bool(urlparse(url).netloc)


def traverse_directory(source_directory: Path,
                       destination_directory: Path,
                       frame: str,
                       exclude: list,
                       base_href: str) -> None:
    """
    Traverse source directory. Transform markdown (.md) files into HTML files. Render this files into the source
    directory. Copy other non-excluded files into source_directory.
    """
    if not destination_directory.exists():
        destination_directory.mkdir()

    for current_directory, sub_directories, file_list in os.walk(source_directory):
        current_directory = Path(current_directory)

        # Filter excluded directories
        if current_directory.name in exclude:
            print(f'Excluded directory: {current_directory}')
            continue

        # Create the destination directories
        directory_to_create = destination_directory
        if current_directory != source_directory:
            directory_to_create = destination_directory / current_directory.relative_to(source_directory)
            if not directory_to_create.exists():
                directory_to_create.mkdir()

        for file_name in filter(lambda name: name not in exclude, file_list):
            if file_name.endswith('.md'):
                page = render_markdown_page(current_directory / file_name, frame, base_href)
                html_file = f'{Path(file_name).stem}.html'
                write_file(page, directory_to_create / html_file)
                print(f'Rendered {directory_to_create / html_file}')
            else:
                copy_file(current_directory / file_name, directory_to_create / file_name)
                print(f'Copied {directory_to_create / file_name}')


def render_markdown_page(path: Path, frame: str, base_href: str) -> str:
    """
    Open markdown file and render it as HTML file. Prepend a header to this HTML file and append a footer to it (frame).
    """
    with open(path) as file:
        lines = []
        md = markdown.markdown(file.read(), extensions=['fenced_code', 'tables', 'sane_lists'])
        for line in frame.split('\n'):
            if '{{ content }}' in line:
                md_lines = [f'{md_line}\n' for md_line in
                            add_target_blank_to_external_urls(replace_md_with_html(md),
                                                              base_href).split('\n')]
                lines.extend(md_lines)
            else:
                lines.append(line)
        page = add_anchor_links(''.join(lines))
        return BeautifulSoup(page, 'html.parser').prettify()


def replace_md_with_html(html_doc: str) -> str:
    """
    Replace href attributes which end with .md (Markdown) with attributes which end with .html.
    """
    soup = BeautifulSoup(html_doc, 'html.parser')
    for a in soup.find_all('a'):
        url = a['href']
        if url.endswith('.md'):
            a['href'] = url.replace('.md', '.html')
    return str(soup)


def add_target_blank_to_external_urls(html_doc: str, base_href: str) -> str:
    soup = BeautifulSoup(html_doc, 'html.parser')
    for a in soup.find_all('a'):
        url = a['href']
        # Check if url is absolute and does not start with a base path
        if bool(urlparse(url).netloc) and not url.startswith(base_href):
            a['target'] = '_blank'
    return str(soup)


def add_anchor_links(html_doc: str) -> str:
    """
    Add anchor links to headings
    """
    soup = BeautifulSoup(html_doc, 'html.parser')
    for title in soup.find_all('h2'):
        anchor_tag = soup.new_tag('a', attrs={'class': 'anchor-link',
                                              'href': f'#{slugify(title.text)}',
                                              'id': f'{slugify(title.text)}'})
        anchor_tag.string = '<<'
        title.append(anchor_tag)
    return str(soup)


def write_file(page: str, path: Path) -> None:
    with open(path, 'w') as file:
        file.write(page)


def copy_file(source_path: Path, destination_path: Path) -> None:
    with open(source_path, 'rb') as source:
        with open(destination_path, 'wb') as destination:
            destination.write(source.read())
