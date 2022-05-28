import argparse
from pathlib import Path

from ssg.runner import generate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Path of the config.json file", type=Path)
    args = parser.parse_args()
    generate(args.input)


if __name__ == '__main__':
    main()
