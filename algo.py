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

    def shortest_path(self) -> list[str]:
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
                if self.get_hub(next_name).zone == "blocked":
                    continue
                new_dist = dist[current] + self.cost(next_name)
                if next_name not in dist or new_dist < dist[next_name]:
                    dist[next_name] = new_dist
                    prev[next_name] = current

        # walk back from end to start
        path = [end]
        while path[0] != start:
            path.insert(0, prev[path[0]])
        return path