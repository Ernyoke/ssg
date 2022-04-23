import os
from urllib.parse import urlparse, urljoin

import bs4
import markdown
from bs4 import BeautifulSoup


def generate(source: str, destination: str, base_path: str) -> None:
    frame_name = 'frame.html'
    traverse_directory(source_directory=source,
                       destination_directory=destination,
                       frame=set_base_path(read_frame(source, frame_name), base_path),
                       exclude=[frame_name, '.git', 'ignore', 'README.md'],
                       base_href=base_path)


def read_frame(path: str, file_name: str = 'frame.html') -> str:
    if file_name in os.listdir(path):
        with open(os.path.join(path, file_name)) as file:
            return file.read()
    else:
        raise Exception('Frame not found in the root folder!')


def set_base_path(page: str, base_path: str) -> str:
    soup = BeautifulSoup(page, 'html.parser')
    set_base_path_for_elements(soup.find_all('a'),
                               attribute='href',
                               base_path=base_path)
    set_base_path_for_elements(soup.find_all('link'),
                               attribute='href',
                               base_path=base_path)
    set_base_path_for_elements(soup.find_all('script'),
                               attribute='src',
                               base_path=base_path)
    set_base_path_for_elements(soup.find_all('img'),
                               attribute='src',
                               base_path=base_path)
    return str(soup)


def set_base_path_for_elements(elements: bs4.element.ResultSet, attribute: str, base_path: str) -> None:
    for element in elements:
        if element.has_attr(attribute):
            url = element[attribute]
            if not is_absolute(url):
                element[attribute] = urljoin(base_path, url)


def is_absolute(url) -> bool:
    return bool(urlparse(url).netloc)


def traverse_directory(source_directory: str,
                       destination_directory: str,
                       frame: str,
                       exclude: list,
                       base_href: str) -> None:
    if not os.path.exists(destination_directory):
        os.mkdir(destination_directory)

    for current_directory, sub_directories, file_list in os.walk(source_directory):

        # Exclude directories from the excluded list
        sub_directories[:] = [sub_dir for sub_dir in sub_directories if sub_dir not in exclude]

        # Create the destination directories
        directory_to_create = destination_directory
        if current_directory != source_directory:
            rel_path = os.path.relpath(current_directory, source_directory)
            directory_to_create = create_destination_directory(rel_path, destination_directory)

        for file_name in file_list:
            print(f'\t{file_name}')
            if file_name not in exclude:
                if file_name.endswith('.md'):
                    page = render_markdown_page(os.path.join(current_directory, file_name), frame, base_href)
                    name = [*os.path.splitext(file_name)]
                    name[-1] = '.html'
                    write_file(page, os.path.join(directory_to_create, ''.join(name)))
                else:
                    copy_file(os.path.join(current_directory, file_name), os.path.join(directory_to_create, file_name))


def create_destination_directory(rel_path: str, destination_directory: str) -> str:
    directory_to_create = os.path.join(*[destination_directory, rel_path])
    if not os.path.exists(directory_to_create):
        os.mkdir(directory_to_create)
    return directory_to_create


def render_markdown_page(path: str, frame: str, base_href: str) -> str:
    with open(path) as file:
        content = file.read()
        md = markdown.markdown(content, extensions=['fenced_code', 'tables', 'sane_lists'])
        page = []
        for line in frame.split('\n'):
            if '{{ content }}' in line:
                md_lines = [f'{x}\n' for x in
                            add_target_blank_to_external_urls(replace_md_with_html(md),
                                                              base_href).split('\n')]
                page.extend(md_lines)
            else:
                page.append(line)
        return BeautifulSoup(''.join(page), 'html.parser').prettify()


def replace_md_with_html(html_doc: str) -> str:
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


def write_file(page: str, path: str) -> None:
    with open(path, 'w') as file:
        file.write(page)


def copy_file(source_path: str, destination_path: str) -> None:
    with open(source_path, 'rb') as source:
        with open(destination_path, 'wb') as destination:
            destination.write(source.read())
