*This project has been created as part of the 42 curriculum by aouassar.*

# Fly-in

## Description

Fly-in is a drone routing simulation written in Python. A map file describes a network of
**hubs** (zones) linked by **connections**, and a fleet of drones that all start on the start
hub. The goal is to bring every drone to the end hub **in as few turns as possible**, while
following the rules of the network:

- each hub holds a limited number of drones at once (`max_drones`, default 1);
- each connection can be crossed by a limited number of drones per turn
  (`max_link_capacity`, default 1);
- hubs have a zone type that changes how they can be used:

| Zone | Cost to enter | Rule |
|---|---|---|
| `normal` | 1 turn | default |
| `priority` | 1 turn | preferred by the pathfinding when two routes cost the same |
| `restricted` | 2 turns | the drone spends one turn on the connection and **must** land on the next |
| `blocked` | — | can never be entered |

The program reads and validates the map, computes the routes, then prints the simulation
turn by turn, one line per turn.

## Instructions

Requirements: Python 3.10 or later. No external library is needed to run the program;
`flake8` and `mypy` are only used for linting.

```
make install                  # install flake8 and mypy
make run MAP=<map_file>       # run the simulation on a map
make debug MAP=<map_file>     # run it inside pdb, Python's debugger
make lint                     # flake8 + mypy with the subject's flags
make lint-strict              # flake8 + mypy --strict
make clean                    # remove __pycache__ and .mypy_cache
```

Or directly:

```
python3 main.py <map_file>
```

Any error (missing file, invalid map, unreachable end hub) prints a clear message such as
`Error: line 7: unknown hub 'roof'` and exits with code 1.

## Algorithm choices and implementation strategy

The code is split into three files: `parsing.py` turns the map into objects, `algo.py`
finds the routes and runs the turns, and `main.py` connects the two and handles errors.

```
map file → Parsing.read_file → Algo.find_paths → Algo.assign_paths → Algo.simulate
```

### 1. Parsing and validation (`parsing.py`)

- `Hub` and `Connection` hold the data, with the defaults given by the subject.
- `Parsing.read_file` reads the file line by line, skips comments and empty lines, and
  sends each line to the right method by its prefix (`hub:`, `connection:`, ...). Every
  error is re-raised with its line number.
- `check_data` runs the checks that need the whole file: one start and one end hub, neither
  blocked, and a **depth-first search (DFS)** that refuses maps where the end can't be
  reached. It also gives the start and end hubs a capacity of `nb_drones`, since the subject
  says they have no limit.

### 2. Shortest path: Dijkstra (`shortest_path`)

A breadth-first search would find the path with the fewest **hubs**, but restricted hubs
cost 2 turns, so the fewest hubs is not always the fewest **turns**. Dijkstra handles costs
that differ per hub:

- `dist[hub]` keeps the cheapest known cost from the start, and `prev[hub]` the hub we came
  from;
- the cheapest hub not done yet is picked at each step, so its cost is final;
- blocked hubs and hubs in an `avoid` list are skipped;
- **priority zones** are handled as a tie-breaker: `prio[hub]` counts the priority hubs on
  the route, and when two routes cost the same, the one with more priority hubs wins. Their
  cost stays 1, so a priority hub never makes a slower route win;
- the path is rebuilt by following `prev` back from the end.

### 3. Several separate paths (`find_paths`)

With capacities of 1, drones on a single path move in single file, so only one drone
reaches the end per turn. `find_paths` repeats Dijkstra while avoiding the middle hubs of
the paths already found. This gives a list of paths that share no hub except start and end,
shortest first, so they never block each other.

### 4. Giving each drone a path (`assign_paths`)

Each drone takes the path with the smallest **estimated arrival**:
`turns needed alone on the path + drones already sent on it`. The short path fills first,
and longer paths are only used once waiting on the short one would cost more.

### 5. Turn-by-turn simulation (`simulate`)

Each drone has a position (its index in its own path) and a `flying` flag for 2-turn moves.
On each turn, drones are processed in order (D1, D2, ...); the ones in front move first, so
a drone leaving a hub frees its place for the next drone **in the same turn**. A drone:

1. that is flying **must** land: its place was reserved when it took off;
2. otherwise moves only if the connection still has capacity this turn **and** the next hub
   has room (`count_at` counts drones in the hub *and* drones flying toward it);
3. toward a restricted hub, takes off and appears on the connection (`D1-a-roof`), then
   lands on the next turn;
4. otherwise waits, and is not printed.

If a turn has no possible move, the program stops with a deadlock error instead of looping
forever. With separate paths, an unlimited end hub and reserved landing places, at least one
drone can always move, so this is a safety net.

### Complexity

- `shortest_path`: O(H²) for H hubs, since each step scans the discovered hubs to find the
  cheapest one. A heap (`heapq`) would make it faster; it isn't needed for these map sizes.
- `simulate`: O(N²) per turn for N drones, because `count_at` loops over every drone.
- Paths are computed **once** before the simulation and reused; nothing is recalculated
  during the turns.

### Limits and alternatives

- `find_paths` is greedy: taking the shortest path first can block two paths that would be
  better together. Max-flow algorithms such as Edmonds-Karp solve this; the subject maps did
  not need them, so the simpler approach was kept.
- `assign_paths` estimates one turn of waiting per drone, even on paths with capacities
  above 1.
- On the *Circular loop* map (all restricted hubs), 16 turns is the minimum under these
  rules: `start-loop_a` has a capacity of 1 and a flying drone stays on it for 2 turns, so
  drones can only take off every 2 turns (turns 1, 3, ..., 11). The sixth drone then lands
  on `loop_a` at turn 12, `loop_b` at 14, `exit_point` at 15 and `goal` at 16.

### Results on the subject maps

| Map | Drones | Target | Turns |
|---|---|---|---|
| Linear path | 2 | ≤ 6 | 4 |
| Simple fork | 4 | ≤ 8 | 5 |
| Basic capacity | 4 | ≤ 6 | 6 |
| Dead end trap | 5 | ≤ 12 | 8 |
| Circular loop | 6 | ≤ 15 | 16 |
| Priority puzzle | 5 | ≤ 12 | 7 |
| Maze nightmare | 8 | ≤ 30 | 14 |
| Capacity hell | 12 | ≤ 35 | 18 |
| Ultimate challenge | 15 | ≤ 45 | 26 |
| The Impossible Dream (challenger) | 25 | 45 | 67 |

## Visual representation

Each move is printed in the color of the hub the drone moves to, using ANSI escape codes
(`\033[31m` switches to red, `\033[0m` resets). The `COLORS` table in `Algo` maps the color
names used in the maps to terminal codes, with the 256-color palette for colors the basic 8
don't have (orange, gold, ...). An unknown color is printed without color, so it never
crashes the program.

This lets you follow the drones at a glance: you can see which zones each turn fills, spot
drones crossing a restricted connection, and see the goal fill up turn after turn. The color
codes are invisible characters inside each line, so there is still exactly one line per turn
(`make run MAP=<map_file> | wc -l` gives the turn count).

## Example

Input (*Linear path*):

```
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Output (4 turns; `waypoint` moves in blue, `goal` moves in red):

```
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal
```

Example with two paths and a restricted hub (4 drones, `c` is restricted):

```
nb_drones: 4
start_hub: s 0 0
hub: a 1 1
hub: b 1 -1
hub: c 2 -1 [zone=restricted]
end_hub: g 3 0
connection: s-a
connection: a-g
connection: s-b
connection: b-c
connection: c-g
```

```
D1-a D4-b
D1-g D2-a D4-b-c
D2-g D3-a D4-c
D3-g D4-g
```

D1 to D3 queue on the short path, while D4 takes the longer one through `c`, where it spends
one turn on the `b-c` connection before landing. This takes 4 turns, against 5 with a single
path.

## Resources

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Depth-first search — Wikipedia](https://en.wikipedia.org/wiki/Depth-first_search) and
  [Breadth-first search — Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
- [Edmonds–Karp algorithm — Wikipedia](https://en.wikipedia.org/wiki/Edmonds%E2%80%93Karp_algorithm)
  (the max-flow alternative)
- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/)
- [mypy documentation](https://mypy.readthedocs.io/) and
  [flake8 documentation](https://flake8.pycqa.org/)
- [ANSI escape code — Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [GNU Make manual](https://www.gnu.org/software/make/manual/make.html)

### How AI was used

Claude (Anthropic) was used as a tutor throughout the project:

- **Guidance:** after the parser was written, it proposed the next small step each time
  (shortest path, simulation, restricted zones, link capacity, multiple paths, priority
  zones, deadlock guard, colors, Makefile) and suggested short code snippets in the style of
  my existing code, which I applied, tested and adapted.
- **Explanations:** Dijkstra, DFS and BFS, type hints, docstrings vs. comments, and
  line-by-line explanations of the code, followed by evaluator-style questions to check my
  understanding.
- **Review and testing:** reviewing each commit (flake8 and mypy errors, a duplicated
  simulation call in `main.py`), writing small test maps, and checking the outputs on the
  subject maps against the movement rules.
- **This README:** drafted by Claude from the code and our discussions, then reviewed by me.

The parser (`parsing.py`) was written by me before using AI; Claude later suggested two
cleanups to it (an `__init__` for `Parsing` and the `to_int` helper for clearer errors).
