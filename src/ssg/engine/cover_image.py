import fnmatch
from pathlib import Path

from ssg.dirtree.file_node import FileNode


def get_cover_image(file: FileNode) -> Path|None:
    """
    Find the cover image associated with the given file.

    Looks inside a sibling directory whose name ends with ``img-<file.name>``
    for an image file named ``cover.*`` whose extension is one of the
    accepted image extensions (e.g. ``.jpg``, ``.png``, ``.gif``, ``.tif``,
    ``.tiff``, ``.jpeg``, ``.eps``, ``.bmp``, ``.ppm``, ``.heif``, ``.avif``).

    :param file: The :class:`FileNode` to find the cover image for.
    :return: The :class:`~pathlib.Path` to the cover image if found,
             otherwise ``None``.
    """
    accepted_image_extensions = ('.tif', '.tiff', '.jpg', '.jpeg', '.gif', '.png', '.eps', ".bmp", '.ppm',
                                 '.heif',
                                 '.avif')
    img_folder_path = f'img-{file.name}'

    covers = []
    for directory in file.parent.directories if file.parent else []:
        if directory.path.name.endswith(img_folder_path):
            for file in directory.files:
                if fnmatch.fnmatch(file.name_with_extension, 'cover.*') and file.path.suffix in accepted_image_extensions:
                    covers.append(file.path)

    if len(covers) == 0:
        return None

    if len(covers) > 1:
        print(f'Warning! Multiple cover images found for {file.path}! Choosing {covers[0]}')

    return Path(covers[0])