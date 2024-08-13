import argparse
from pathlib import Path

from runner import runner
from config import read_config


def main():
    """
    Entry point.
    :return: None
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path of the config.json file", type=Path)
    args = parser.parse_args()
    config = read_config(args.config)
    ssg = runner.SSG(config)
    ssg.run()


if __name__ == '__main__':
    main()
