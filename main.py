import sys

from parsing import Parsing
from algo import Algo


def main() -> None:
    """Read the map given as argument and run the drone simulation.

    Prints an error and exits with code 1 if the arguments or
    the map are invalid.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <map_file>")
        sys.exit(1)
    parsing = Parsing()
    try:
        parsing.read_file(sys.argv[1])
        algo = Algo(parsing)
        paths = algo.find_paths()
        algo.simulate(algo.assign_paths(paths))
    except (OSError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
