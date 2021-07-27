import argparse

from ssg import generate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="Source folder from which the files has to be parsed.", type=str)
    parser.add_argument("destination", help="Destination folder where the results will be stored.", type=str)
    parser.add_argument("base_path", help="Base path of the page.", type=str)
    args = parser.parse_args()
    generate(args.source, args.destination, args.base_path)
    generate(args.source, args.destination, args.base_path)


if __name__ == '__main__':
    main()
