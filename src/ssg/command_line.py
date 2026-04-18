import argparse
from pathlib import Path

from ssg.runner import runner
from ssg.config import read_config


def main():
    """
    Entry point.
    :return: None
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path of the config.json file", type=Path)
    args = parser.parse_args()
    config = read_config(args.config)
    ssg_engine = runner.Engine()
    ssg_engine.run(config)


if __name__ == '__main__':
    main()
