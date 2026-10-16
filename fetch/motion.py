"""The math for how things move: throws, slides, and leaps over each other.

Leaps are worked out from the drawings themselves: for every column, how high does
one sprite have to be lifted so none of its characters land on the other's? That
means a redrawn character still jumps cleanly without retuning any numbers."""

import math
from functools import lru_cache

from .config import THROW_PEAK
from .sprites import width_of


def slide(start, end, step):
    """Positions from start to end in jumps of `step`, landing exactly on end."""
    direction = 1 if end >= start else -1
    xs = list(range(start, end, step * direction))
    return xs + [end]


@lru_cache(maxsize=None)
def _cells(sprite):
    """Filled cells of a sprite as (height above its bottom row, column)."""
    rows = len(sprite)
    return frozenset((rows - 1 - r, c) for r, line in enumerate(sprite) for c, ch in enumerate(line) if ch != " ")


def clearance(mover, obstacle, dx):
    """How high `mover` must be lifted to pass over `obstacle` when it sits dx columns
    to the right of it (both standing on the ground). 0 means it already clears."""
    tops, bottoms = {}, {}
    for h, c in _cells(tuple(obstacle)):
        tops[c] = max(tops.get(c, -1), h)
    for h, c in _cells(tuple(mover)):
        bottoms[c] = min(bottoms.get(c, 99), h)
    need = 0
    for c, bottom in bottoms.items():
        top = tops.get(c + dx)
        if top is not None:
            need = max(need, top - bottom + 1)
    return need


class Leap:
    """A smooth arc that carries `mover` over `obstacle` (sitting at obstacle_x).
    height(x) gives the height for the mover's left edge at column x, in either direction."""

    def __init__(self, mover, obstacle, obstacle_x, extra=1, hug=False):
        """hug=True keeps the arc low and follows the obstacle's outline instead, like
        a cat bounding across the dog's back rather than sailing clean over it."""
        xs = range(obstacle_x - width_of(mover) - 4, obstacle_x + width_of(obstacle) + 5)
        self.need = {x: clearance(mover, obstacle, x - obstacle_x) for x in xs}
        if hug:  # ramp up to the outline and back down, one row per column
            self.need = {x: max(self.need.get(x + k, 0) - abs(k) for k in range(-3, 4)) for x in xs}
        blocked = [x for x, n in self.need.items() if n > 0] or [obstacle_x]  # nothing in the way: no leap
        self.peak = max(self.need.values()) + extra
        self.center = (blocked[0] + blocked[-1]) / 2
        if hug:
            reach = (blocked[-1] - blocked[0]) / 2 * 0.6
        else:
            reach = (blocked[-1] - blocked[0]) / 2 + 1
            while any(self._arc(x, self.center, reach) < n for x, n in self.need.items()):
                reach += 0.5
        self.reach = reach
        # A short leap takes off at the same spot but comes down too soon
        self.short_reach = reach * 0.75
        self.short_center = self.center - reach + self.short_reach
        clipped = [x for x in xs if self._arc(x, self.short_center, self.short_reach) < self.need[x]]
        self.first_clip = clipped[0] if clipped else None

    def _arc(self, x, center, reach):
        d = abs(x - center)
        if d >= reach:
            return 0
        return math.floor(self.peak * (1 - (d / reach) ** 2) + 0.5)

    def height(self, x):
        return max(self._arc(x, self.center, self.reach), self.need.get(x, 0))

    def short_height(self, x):
        """The short leap: bumps into the obstacle for a moment, then scrambles over it."""
        arc = self._arc(x, self.short_center, self.short_reach)
        need = self.need.get(x, 0)
        if arc >= need:
            return arc
        return need - 1 if x - self.first_clip < 2 else need

    def clips(self, x):
        """True where the short leap bumps into the obstacle."""
        return self.first_clip is not None and 0 <= x - self.first_clip < 2

    @property
    def start(self):
        return math.floor(self.center - self.reach)

    @property
    def end(self):
        return math.ceil(self.center + self.reach)


def ball_path(width, start_x, start_h, obstacle_end):
    """Every (column, height) of the ball: thrown in an arc, a couple of bounces, then rolling to a stop."""
    stop = width - 3
    land = obstacle_end + (stop - obstacle_end) // 3
    flight = max(1, round((land - start_x) / 3))
    path = []
    for f in range(flight + 1):
        u = f / flight
        height = start_h * (1 - u) + THROW_PEAK * 4 * u * (1 - u)
        path.append((round(start_x + (land - start_x) * u), round(height)))

    rest = stop - land
    for i in range(1, rest + 1):
        u = i / rest
        x = land + rest * (1 - (1 - u) ** 2)
        travel = (x - land) / rest
        if travel < 0.4:
            height = 2 * math.sin(math.pi * travel / 0.4)
        elif travel < 0.65:
            height = math.sin(math.pi * (travel - 0.4) / 0.25)
        else:
            height = 0
        path.append((round(x), round(height)))
    return path
