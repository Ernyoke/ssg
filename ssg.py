import argparse
import os

import markdown
from bs4 import BeautifulSoup


def start():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source folder from which the files has to be parsed.", type=str)
    parser.add_argument("destination", help="Destination folder where the results will be stored.", type=str)
    parser.add_argument("base_path", help="Base path of the page.", type=str)
    args = parser.parse_args()
    frame_name = 'frame.html'
    frame = read_frame(args.source, frame_name)
    traverse_directory(args.source,
                       args.destination,
                       add_base_path(frame, args.base_path),
                       [frame_name, '.git'])


def read_frame(path: str, file_name: str = 'frame.html') -> str:
    files = os.listdir(path)
    if file_name in files:
        with open(os.path.join(path, file_name)) as file:
            return file.read()
    else:
        raise Exception("Frame not found in the root folder!")


def add_base_path(page: str, base_path: str):
    soup = BeautifulSoup(page, 'html.parser')
    head = soup.find('head')
    base = soup.new_tag('base', href=base_path)
    head.insert(0, base)
    return soup.prettify()


def traverse_directory(source_directory: str,
                       destination_directory: str,
                       frame: str,
                       exclude: list):
    if not os.path.exists(destination_directory):
        os.mkdir(destination_directory)

    for current_directory, sub_directories, file_list in os.walk(source_directory):

        # Exclude directories from the exclude list
        sub_directories[:] = [sub_dir for sub_dir in sub_directories if sub_dir not in exclude]

        # Create the destination directories
        print('Traversing directory: %s' % current_directory)
        directory_to_create = destination_directory
        if current_directory != source_directory:
            directory_to_create = create_destination_directory(current_directory, destination_directory)

        for file_name in file_list:
            print('\t%s' % file_name)
            if file_name not in exclude:
                if file_name.endswith('.md'):
                    page = render_markdown_page(os.path.join(current_directory, file_name), frame)
                    name = [*os.path.splitext(file_name)]
                    name[len(name) - 1] = '.html'
                    write_file(page, os.path.join(directory_to_create, ''.join(name)))
                else:
                    copy_file(os.path.join(current_directory, file_name), os.path.join(directory_to_create, file_name))


def create_destination_directory(current_directory: str, destination_directory: str):
    parts = [*os.path.split(current_directory)]
    parts[0] = destination_directory
    directory_to_create = os.path.join(*parts)
    if not os.path.exists(directory_to_create):
        os.mkdir(directory_to_create)
    return directory_to_create


def render_markdown_page(path: str, frame: str) -> str:
    with open(path) as file:
        content = file.read()
        md = markdown.markdown(content, extensions=['fenced_code', 'tables', 'sane_lists'])
        page = []
        for line in frame.split('\n'):
            if '{{ content }}' in line:
                md_lines = [x + "\n" for x in replace_md_with_html(md).split("\n")]
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


def write_file(page: str, path: str):
    with open(path, 'w') as file:
        file.write(page)


def copy_file(source_path: str, destination_path: str):
    with open(source_path, 'rb') as source:
        with open(destination_path, 'wb') as destination:
            destination.write(source.read())


if __name__ == '__main__':
    start()