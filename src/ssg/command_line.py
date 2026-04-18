import argparse
from pathlib import Path

from ssg.config import read_config
from ssg.engine.engine import Engine


def main():
    """
    Entry point.
    :return: None
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path of the config.json file", type=Path)
    args = parser.parse_args()
    config = read_config(args.config)
    ssg_engine = Engine()
    ssg_engine.run(config)


if __name__ == '__main__':
    main()
