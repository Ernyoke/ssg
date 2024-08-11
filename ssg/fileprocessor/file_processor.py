from pathlib import Path


class FileProcessor:
    def __init__(self, directory: Path, file_name: str):
        self.directory = directory
        self.file_name = file_name
        self.path = directory / Path(file_name)
        self.content = ""

    def write_file(self, destination_path: Path) -> None:
        """
        Write the content of the `page` to the path location.
        :return: None
        """
        with open(destination_path, mode='w', newline='\n') as file:
            file.write(self.content)
