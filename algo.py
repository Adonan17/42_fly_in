from parsing import Parsing, Hub


class Algo:
    """Find paths for the drones and simulate their moves."""
    COLORS = {
        "black": "30", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "magenta": "35", "cyan": "36", "white": "37",
        "gray": "90", "orange": "38;5;208", "purple": "38;5;129",
        "darkred": "38;5;88", "gold": "38;5;220", "brown": "38;5;94",
        "maroon": "38;5;52", "crimson": "38;5;161", "lime": "38;5;118",
        "violet": "38;5;177",
    }

    def __init__(self, parsing: Parsing) -> None:
        """Keep the parsed map to work on."""

    def colored(self, text: str, color: str) -> str:
        """Returns the text in the right color."""
        if color not in self.COLORS:
            return text
        return f"\033[{self.COLORS[color]}m{text}\033[0m"

    def get_hub(self, name: str) -> Hub:
        """Returns the right hub or raises ValueError."""
        for hub in self.parsing.hubs:
            if hub.name == name:
                return hub
        raise ValueError(f"unknown hub '{name}'")

    def neighbors(self, name: str) -> list[str]:
        """Return the names of the hubs connected to this one."""
        result = []
        for connection in self.parsing.connections:
            if connection.name1 == name:
                result.append(connection.name2)
            elif connection.name2 == name:
                result.append(connection.name1)
        return result

    def cost(self, name: str) -> int:
        """Return how many turns it takes to enter this hub."""
        if self.get_hub(name).zone == "restricted":
            return 2
        return 1

    def shortest_path(self, avoid: list[str]) -> list[str]:
        """Returns the shortest path from the start_hub to the end_hub."""
        if self.parsing.start_hub is None or self.parsing.end_hub is None:
            raise ValueError("missing start_hub or end_hub")
        start = self.parsing.start_hub.name
        end = self.parsing.end_hub.name
        dist = {start: 0}
        prio = {start: 0}
        prev: dict[str, str] = {}
        done: list[str] = []

        while True:
            # pick the closest hub not done yet
            current = ""
            for name in dist:
                if name not in done and (current == ""
                                         or dist[name] < dist[current]):
                    current = name
            if current == "" or current == end:
                break
            done.append(current)
            for next_name in self.neighbors(current):
                if (self.get_hub(next_name).zone == "blocked"
                        or next_name in avoid):
                    continue
                new_dist = dist[current] + self.cost(next_name)
                new_prio = prio[current]
                if self.get_hub(next_name).zone == "priority":
                    new_prio += 1
                if (next_name not in dist or new_dist < dist[next_name]
                        or (new_dist == dist[next_name]
                            and new_prio > prio[next_name])):
                    dist[next_name] = new_dist
                    prio[next_name] = new_prio
                    prev[next_name] = current
        if end not in dist:
            return []

        # walk back from end to start
        path = [end]
        while path[0] != start:
            path.insert(0, prev[path[0]])
        return path

    def find_paths(self) -> list[list[str]]:
        """Find paths that share no hubs except start and end."""
        paths = []
        avoid: list[str] = []
        while True:
            path = self.shortest_path(avoid)
            if path == [] or path in paths:
                break
            paths.append(path)
            # next paths can't reuse the hubs in the middle of this one
            avoid += path[1:-1]
        return paths

    def link_capacity(self, name1: str, name2: str) -> int:
        """Returns the max link capacity of a connexion
         or raises ValueError."""
        for connection in self.parsing.connections:
            if {connection.name1, connection.name2} == {name1, name2}:
                return connection.max_link_capacity
        raise ValueError(f"unknown connection '{name1}-{name2}'")

    def path_turns(self, path: list[str]) -> int:
        """Return how many turns one drone alone needs on this path."""
        turns = 0
        for name in path[1:]:
            turns += self.cost(name)
        return turns

    def assign_paths(self, paths: list[list[str]]) -> list[list[str]]:
        """Give each drone the path where it would arrive soonest."""
        drone_paths: list[list[str]] = []
        for _ in range(self.parsing.nb_drones):
            # pick the path where this drone would arrive the soonest
            best = paths[0]
            for path in paths:
                if (self.path_turns(path) + drone_paths.count(path)
                        < self.path_turns(best) + drone_paths.count(best)):
                    best = path
            drone_paths.append(best)
        return drone_paths

    def count_at(self, name: str, drone_paths: list[list[str]],
                 positions: list[int], flying: list[bool]) -> int:
        """Count the drones in a hub or flying toward it."""
        count = 0
        for i in range(len(positions)):
            path = drone_paths[i]
            if not flying[i] and path[positions[i]] == name:
                count += 1
            elif flying[i] and path[positions[i] + 1] == name:
                count += 1
        return count

    def simulate(self, drone_paths: list[list[str]]) -> None:
        """Does the simulation and prints every move."""
        nb = self.parsing.nb_drones
        positions = [0] * nb
        flying = [False] * nb
        delivered = 0
        while delivered < nb:
            moves = []
            used_links: list[str] = []
            for i in range(nb):
                path = drone_paths[i]
                if positions[i] == len(path) - 1:
                    continue
                next_hub = self.get_hub(path[positions[i] + 1])
                link = path[positions[i]] + "-" + next_hub.name
                link_full = (used_links.count(link) >= self.link_capacity(
                    path[positions[i]], next_hub.name))
                if flying[i]:
                    # must land this turn
                    flying[i] = False
                    used_links.append(link)
                    positions[i] += 1
                    moves.append(self.colored(
                        f"D{i + 1}-{next_hub.name}", next_hub.color))
                elif (not link_full
                      and self.count_at(next_hub.name, drone_paths,
                                        positions, flying)
                      < next_hub.max_drones):
                    used_links.append(link)
                    if next_hub.zone == "restricted":
                        flying[i] = True
                        moves.append(self.colored(
                            f"D{i + 1}-{link}", next_hub.color))
                    else:
                        positions[i] += 1
                        moves.append(self.colored(
                            f"D{i + 1}-{next_hub.name}", next_hub.color))
                if positions[i] == len(path) - 1:
                    delivered += 1
            if moves == []:
                raise ValueError("deadlock: no drone can move")
            print(" ".join(moves))
