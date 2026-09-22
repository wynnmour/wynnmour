from dataclasses import dataclass
from typing import List, Tuple

GRID_SIZE = 5
DIRECTIONS = {
    "U": (-1, 0),
    "D": (1, 0),
    "L": (0, -1),
    "R": (0, 1),
}

@dataclass(frozen=True)
class Arrow:
    row: int
    col: int
    direction: str


def is_path_clear(arrows: List[Arrow], target: Arrow, grid_size: int = GRID_SIZE) -> bool:
    """Check whether target can fly out of the board."""
    dr, dc = DIRECTIONS[target.direction]
    occupied = {(a.row, a.col) for a in arrows if a != target}
    r, c = target.row + dr, target.col + dc
    while 0 <= r < grid_size and 0 <= c < grid_size:
        if (r, c) in occupied:
            return False
        r += dr
        c += dc
    return True


def find_arrow(arrows: List[Arrow], row: int, col: int):
    for arrow in arrows:
        if arrow.row == row and arrow.col == col:
            return arrow
    return None


def can_solve(arrows: List[Arrow], grid_size: int = GRID_SIZE) -> bool:
    """Simple simulation used to validate level layouts."""
    remaining = list(arrows)
    while remaining:
        movable = next((a for a in remaining if is_path_clear(remaining, a, grid_size)), None)
        if movable is None:
            return False
        remaining.remove(movable)
    return True
