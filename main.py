import argparse
import os

import markdown


def read_frame(path: str, file_name: str = 'frame.html') -> list:
    files = os.listdir(path)
    if file_name in files:
        with open(os.path.join(path, file_name)) as file:
            return file.readlines()
    else:
        raise Exception("Frame not found in the root folder!")


def add_base_path(page: list, base_path: str):
    for index, line in enumerate(page):
        if 'base href=""' in line:
            page[index] = line.replace('base href=""', 'base href="%s"' % base_path)


def traverse_directory(source_directory: str,
                       destination_directory: str,
                       frame: list,
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


def render_markdown_page(path: str, frame: list) -> list:
    with open(path) as file:
        content = file.read()
        md = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        page = []
        for line in frame:
            if '{{ content }}' in line:
                md_lines = [x + "\n" for x in md.split("\n")]
                page.extend(md_lines)
            else:
                page.append(line)
        return page


def write_file(page: list, path: str):
    with open(path, 'w') as file:
        for line in page:
            file.write(line)


def copy_file(source_path: str, destination_path: str):
    with open(source_path, 'rb') as source:
        with open(destination_path, 'wb') as destination:
            destination.write(source.read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source folder from which the files has to be parsed.", type=str)
    parser.add_argument("destination", help="Destination folder where the results will be stored.", type=str)
    parser.add_argument("base_path", help="Base path for html", type=str)
    args = parser.parse_args()
    frame_name = 'frame.html'
    frame = read_frame(args.source, frame_name)
    add_base_path(frame, args.base_path)
    traverse_directory(args.source,
                       args.destination,
                       frame,
                       [frame_name, '.git'])
