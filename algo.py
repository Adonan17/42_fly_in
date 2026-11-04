from parsing import Parsing, Hub


class Algo:
    def __init__(self, parsing: Parsing) -> None:
        self.parsing = parsing

    def get_hub(self, name: str) -> Hub:
        for hub in self.parsing.hubs:
            if hub.name == name:
                return hub
        raise ValueError(f"unknown hub '{name}'")

    def neighbors(self, name: str) -> list[str]:
        result = []
        for connection in self.parsing.connections:
            if connection.name1 == name:
                result.append(connection.name2)
            elif connection.name2 == name:
                result.append(connection.name1)
        return result

    def cost(self, name: str) -> int:
        if self.get_hub(name).zone == "restricted":
            return 2
        return 1

    def shortest_path(self, avoid: list[str]) -> list[str]:
        if self.parsing.start_hub is None or self.parsing.end_hub is None:
            raise ValueError("missing start_hub or end_hub")
        start = self.parsing.start_hub.name
        end = self.parsing.end_hub.name
        dist = {start: 0}
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
                if next_name not in dist or new_dist < dist[next_name]:
                    dist[next_name] = new_dist
                    prev[next_name] = current
        if end not in dist:
            return []

        # walk back from end to start
        path = [end]
        while path[0] != start:
            path.insert(0, prev[path[0]])
        return path

    def find_paths(self) -> list[list[str]]:
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
        for connection in self.parsing.connections:
            if {connection.name1, connection.name2} == {name1, name2}:
                return connection.max_link_capacity
        raise ValueError(f"unknown connection '{name1}-{name2}'")

    def path_turns(self, path: list[str]) -> int:
        turns = 0
        for name in path[1:]:
            turns += self.cost(name)
        return turns

    def assign_paths(self, paths: list[list[str]]) -> list[list[str]]:
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
        count = 0
        for i in range(len(positions)):
            path = drone_paths[i]
            if not flying[i] and path[positions[i]] == name:
                count += 1
            elif flying[i] and path[positions[i] + 1] == name:
                count += 1
        return count

    def simulate(self, drone_paths: list[list[str]]) -> None:
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
                    moves.append(f"D{i + 1}-{next_hub.name}")
                elif (not link_full
                      and self.count_at(next_hub.name, drone_paths,
                                        positions, flying)
                      < next_hub.max_drones):
                    used_links.append(link)
                    if next_hub.zone == "restricted":
                        flying[i] = True
                        moves.append(f"D{i + 1}-{link}")
                    else:
                        positions[i] += 1
                        moves.append(f"D{i + 1}-{next_hub.name}")
                if positions[i] == len(path) - 1:
                    delivered += 1
            print(" ".join(moves))
