class Hub:
    name: str
    x: int
    y: int
    zone: str = "normal"
    color: str = "none"
    max_drones: int = 1
    start: bool = False
    end: bool = False


class Connection:
    name1: str
    name2: str
    max_link_capacity: int = 1


class Parsing:
    nb_drones: int
    start_hub: Hub | None
    end_hub: Hub | None
    hubs: list[Hub]
    connections: list[Connection]

    def read_file(self, path: str) -> None:
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.hubs = []
        self.connections = []

        with open(path, "r") as file:
            lines = file.readlines()

        line_nb = 0
        for line in lines:
            line_nb += 1
            line = line.strip()
            # if empty -> skip, if comment -> skip
            if line == "" or line.startswith("#"):
                continue
            try:
                if self.nb_drones == 0:
                    if not line.startswith("nb_drones:"):
                        raise ValueError("first line must be nb_drones")
                    self.parse_nb_drones(line[len("nb_drones:"):])
                elif line.startswith("start_hub:"):
                    self.parse_start_hub(line[len("start_hub:"):])
                elif line.startswith("hub:"):
                    self.parse_hub(line[len("hub:"):])
                elif line.startswith("end_hub:"):
                    self.parse_end_hub(line[len("end_hub:"):])
                elif line.startswith("connection:"):
                    self.parse_connection(line[len("connection:"):])
                else:
                    raise ValueError(f"invalid line '{line}'")
            except ValueError as e:
                raise ValueError(f"line {line_nb}: {e}")

        self.check_data()

    def parse_nb_drones(self, text: str) -> None:
        self.nb_drones = int(text)
        if self.nb_drones <= 0:
            raise ValueError("nb_drones must be positive")

    def parse_start_hub(self, text: str) -> None:
        if self.start_hub is not None:
            raise ValueError("there is already a start_hub")
        hub = self.parse_hub(text)
        hub.start = True
        self.start_hub = hub

    def parse_hub(self, text: str) -> Hub:
        metadata = ""
        if "[" in text:
            text, metadata = text.split("[", 1)
            if not metadata.endswith("]"):
                raise ValueError("metadata must end with ']'")
            metadata = metadata[:-1]

        parts = text.split()
        if len(parts) != 3:
            raise ValueError("expected '<name> <x> <y> [metadata]'")
        hub = Hub()
        hub.name = parts[0]
        hub.x = int(parts[1])
        hub.y = int(parts[2])

        if "-" in hub.name:
            raise ValueError(f"'{hub.name}': no '-' allowed in names")
        for other in self.hubs:
            if other.name == hub.name:
                raise ValueError(f"'{hub.name}' already exists")

        for item in metadata.split():
            key, _, value = item.partition("=")
            if key == "" or value == "":
                raise ValueError(f"invalid metadata '{item}'")
            if key == "zone":
                if value not in ["normal", "blocked", "restricted",
                                 "priority"]:
                    raise ValueError(f"invalid zone type '{value}'")
                hub.zone = value
            elif key == "color":
                hub.color = value
            elif key == "max_drones":
                hub.max_drones = int(value)
                if hub.max_drones <= 0:
                    raise ValueError("max_drones must be positive")
            else:
                raise ValueError(f"unknown metadata '{key}'")

        self.hubs.append(hub)
        return hub

    def parse_end_hub(self, text: str) -> None:
        if self.end_hub is not None:
            raise ValueError("there is already an end_hub")
        hub = self.parse_hub(text)
        hub.end = True
        self.end_hub = hub

    def parse_connection(self, text: str) -> None:
        metadata = ""
        if "[" in text:
            text, metadata = text.split("[", 1)
            if not metadata.endswith("]"):
                raise ValueError("metadata must end with ']'")
            metadata = metadata[:-1]

        parts = text.split()
        if len(parts) != 1:
            raise ValueError("expected '<name1>-<name2> [metadata]'")
        names = parts[0].split("-")
        if len(names) != 2:
            raise ValueError(f"invalid connection '{parts[0]}'")
        connection = Connection()
        connection.name1 = names[0]
        connection.name2 = names[1]

        hub_names = [hub.name for hub in self.hubs]
        for name in names:
            if name not in hub_names:
                raise ValueError(f"unknown hub '{name}'")
        if connection.name1 == connection.name2:
            raise ValueError("a hub can't be connected to itself")
        for other in self.connections:
            if ({other.name1, other.name2}
                    == {connection.name1, connection.name2}):
                raise ValueError(f"duplicate connection '{parts[0]}'")

        for item in metadata.split():
            key, _, value = item.partition("=")
            if key == "max_link_capacity" and value != "":
                connection.max_link_capacity = int(value)
                if connection.max_link_capacity <= 0:
                    raise ValueError("max_link_capacity must be positive")
            else:
                raise ValueError(f"invalid metadata '{item}'")

        self.connections.append(connection)

    def check_data(self) -> None:
        if self.nb_drones == 0:
            raise ValueError("missing nb_drones")
        if self.start_hub is None:
            raise ValueError("missing start_hub")
        if self.end_hub is None:
            raise ValueError("missing end_hub")
        if self.start_hub.zone == "blocked" or self.end_hub.zone == "blocked":
            raise ValueError("start_hub and end_hub can't be blocked")

        # start and end have no capacity limit
        self.start_hub.max_drones = self.nb_drones
        self.end_hub.max_drones = self.nb_drones

        # can you go from start to end? (without blocked hubs)
        visited = [self.start_hub.name]
        to_visit = [self.start_hub.name]
        while to_visit:
            current = to_visit.pop()
            for connection in self.connections:
                if connection.name1 == current:
                    next_name = connection.name2
                elif connection.name2 == current:
                    next_name = connection.name1
                else:
                    continue
                for hub in self.hubs:
                    if (hub.name == next_name and hub.zone != "blocked"
                            and next_name not in visited):
                        visited.append(next_name)
                        to_visit.append(next_name)
        if self.end_hub.name not in visited:
            raise ValueError("no path from start_hub to end_hub")