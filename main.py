import sys

from parsing import Parsing


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

    print("nb_drones:", parsing.nb_drones)
    for hub in parsing.hubs:
        print(hub.name, hub.x, hub.y, hub.zone, hub.color, hub.max_drones)
    for connection in parsing.connections:
        print(connection.name1, connection.name2,
              connection.max_link_capacity)


if __name__ == "__main__":
    main()