import sys

from parsing import Parsing
from algo import Algo


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)
    parsing = Parsing()
    try:
        parsing.read_file(sys.argv[1])
    except (OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    algo = Algo(parsing)
    paths = algo.find_paths()
    algo.simulate(algo.assign_paths(paths))


if __name__ == "__main__":
    main()
