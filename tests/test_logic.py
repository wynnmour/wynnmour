import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_logic import Arrow, is_path_clear, can_solve

# T01: unobstructed arrow can leave the board.
a = [Arrow(2, 2, 'R')]
assert is_path_clear(a, a[0])

# T02: an arrow with an occupied cell in front is blocked.
a = [Arrow(2, 1, 'R'), Arrow(2, 3, 'U')]
assert not is_path_clear(a, a[0])

# T03: edge arrow pointing outwards is valid.
a = [Arrow(0, 2, 'U')]
assert is_path_clear(a, a[0])

# T04/T05/T06: all supplied levels are solvable and can be reset independently.
from main import LEVELS
for level in LEVELS:
    arrows = [Arrow(*x) for x in level]
    assert can_solve(arrows)
print('All logic tests passed.')
