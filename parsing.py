class Hub:
    name:str
    x:int
    y:int
    metadata:dict
    start:bool = False
    end:bool = False
    # metadata

class Connection:
    name1:str
    name2:str
    # metadata

class Parsing:
    nb_drones:int
    start_hub:Hub
    hubs:list[Hub]
    end_hub:Hub
    def read_file(path:str):
        with open(path, "r") as file:
            for line in file:
                if line.startswith("nb_drones:"):
                    print("nb_drones line ->", line.strip())
                elif line.startswith("start_hub:"):
                    print("start_hub line ->", line.strip())
                elif line.startswith("hub:"):
                    print("hub line ->", line.strip())
                elif line.startswith("connection:"):
                    print("connection line ->", line.strip())
                elif line.startswith("end_hub:"):
                    print("end_hub line ->", line.strip())
                # if empty -> skip
                # if comment -> skip
                else:
                    print("error line ->", line.strip())
                print(line)

    def nb_drones(self):
        pass
        # extract nb of drones and define nb_drones
        # self:nb_drone = nb exctracted
    def start_hub(self):
        pass
        # extract name x and y
        # class Hub
        # Hub.name = name
        # do this for x and y also
        # Hub.start = True
        # extract metadata
    def hub(self):
        pass
        # extract name x and y
        # class Hub
        # Hub.name = name
        # do this for x and y also
        # extract metadata
    def end_hub(self):
        pass
        # extract name x and y
        # class Hub
        # Hub.name = name
        # do this for x and y also
        # Hub.end = True
        # extract metadata
    def connection(self):
        pass
        # extract name1 and name2
        # extract metadata

    def check_data(self):
        pass
        # conditions:
        #   start && end?
        #   can you go from start to end?
        #   is there a number of drones?
        #   do the names of the hubs exist?
        #   2 hubs with the same name or coordinates?
        #   check if special type hub isn't start or end.