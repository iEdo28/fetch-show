"""The opening titles: the show's name, then a roll call of the cast."""

import math
import random

from .config import (
    ALERT_COLOR, BALL_CARD, CARD_COLOR, CAT_CARD, CROW_CARD, DELAY, DOG_CARD, FEET_ROW, SQUIRREL_CARD,
    TEXT_COLOR, THROWER_CARD, TITLE_COLORS,
)
from .motion import slide
from .sprites import (
    CAT_FACE, CAT_RUN_WIDTH, CAT_WIDTH, DOG_STAND, DOG_WALK, DOG_WIDTH, SAM_WIDTH, SQUIRREL_WIDTH, SUBTITLE,
    TITLE, TITLE_FONT, cat_loaf, cat_running, dog_sprite,
)
from .stage import snores

TITLE_DROP = [-1, 1, 3, 5, 7, 6, 7]  # each letter falls in and bounces once
READING_TIME = 2.5  # seconds each name card stays up once it has finished typing
HOLD = round(READING_TIME / DELAY)


def typed(lines, count, x, top):
    """The first `count` characters of a block of text, as if being typed out."""
    layers = []
    for row, (text, color) in enumerate(lines):
        shown = text[:max(0, count)]
        if shown:
            layers.append(([shown], x, top + row, color))
        count -= len(text)
    return layers


def title_card(s):
    """The show's name drops in letter by letter, then the subtitle types out."""
    letters = [TITLE_FONT[ch] for ch in TITLE]
    widths = [len(letter[0]) + 1 for letter in letters]
    total = sum(widths) - 1
    xs = [(s.width - total) // 2 + sum(widths[:i]) for i in range(len(letters))]
    title_bottom = TITLE_DROP[-1]

    for t in range(3 * (len(letters) - 1) + len(TITLE_DROP)):
        layers = []
        for i, letter in enumerate(letters):
            k = t - 3 * i
            if k >= 0:
                bottom = TITLE_DROP[min(k, len(TITLE_DROP) - 1)]
                layers.append((letter, xs[i], bottom, TITLE_COLORS[i % len(TITLE_COLORS)]))
        yield s.frame(*layers)

    title = [(letter, xs[i], title_bottom, TITLE_COLORS[i % len(TITLE_COLORS)]) for i, letter in enumerate(letters)]
    sub_x = (s.width - len(SUBTITLE)) // 2
    for k in range(0, len(SUBTITLE) + 3, 3):
        yield s.frame(*title, ([SUBTITLE[:k]], sub_x, title_bottom + 2, TEXT_COLOR))

    # Twinkle on either side of the title
    rng = random.Random(3)
    left, right = xs[0], xs[-1] + widths[-1]
    spots = []
    for _ in range(10):
        x = rng.choice([rng.randrange(max(0, left - 10), max(1, left - 1)),
                        rng.randrange(min(s.width - 2, right + 1), min(s.width - 1, right + 10))])
        spots.append((x, rng.randrange(2, title_bottom + 1)))
    for i in range(8):
        sparkles = [(["*+."[(i + j) % 3]], x, row, ALERT_COLOR) for j, (x, row) in enumerate(spots) if (i + j) % 4]
        yield s.frame(*sparkles, *title, ([SUBTITLE], sub_x, title_bottom + 2, TEXT_COLOR))


def cast_roll(s):
    """Each character comes on, gets a name card, and leaves."""
    header = (["S T A R R I N G"], (s.width - 15) // 2, 3, CARD_COLOR)
    text_x = s.width // 2 + 1

    def spot(width):
        """Where a character of this width stands: just left of its name card."""
        return s.width // 2 - 2 - width

    def card(info, entering, pose, leaving):
        name, role, loves = info
        lines = [(name, CARD_COLOR), (role, TEXT_COLOR), ("loves: " + loves, TEXT_COLOR)]
        for layers in entering:
            yield s.frame(header, layers)
        typing_frames = sum(len(text) for text, _ in lines) // 5 + 1
        for i in range(typing_frames + HOLD):
            yield s.frame(header, pose(i), typed(lines, i * 5, text_x, FEET_ROW - 3))
        for layers in leaving:
            yield s.frame(header, layers)

    # Biscuit trots in, wags, and runs off
    x = spot(DOG_WIDTH)
    yield from card(
        DOG_CARD,
        [s.dog(dog_sprite(DOG_WALK[i % 4]), sx) for i, sx in enumerate(slide(-DOG_WIDTH, x, 3))],
        lambda i: s.dog(dog_sprite(DOG_STAND, tail="wag" if (i // 2) % 2 else "up"), x),
        [s.dog(dog_sprite(DOG_WALK[i % 4], tail="wag", ear="up"), sx) for i, sx in enumerate(slide(x, s.width, 6))],
    )

    # Mochi strolls in, curls up for a nap, then bolts
    x = spot(CAT_RUN_WIDTH)
    loaf_x = x + CAT_RUN_WIDTH - CAT_WIDTH

    def cat_pose(i):
        if i < 3:
            return s.cat(cat_running("^.^"), x)
        return [s.cat(cat_loaf(), loaf_x), *snores(loaf_x + CAT_FACE + 2, FEET_ROW - 2, s.tick + 1)]

    yield from card(
        CAT_CARD,
        [s.cat(cat_running("^.^"), sx) for sx in slide(-CAT_RUN_WIDTH, x, 3)],
        cat_pose,
        [s.cat(cat_running(">.<"), sx) for sx in slide(x, s.width, 6)],
    )

    # Sam walks in and waves
    x = spot(SAM_WIDTH)
    yield from card(
        THROWER_CARD,
        [s.sam("step" if i % 2 else "idle", sx) for i, sx in enumerate(slide(-SAM_WIDTH, x, 3))],
        lambda i: s.sam("cheer" if (i // 2) % 2 == 0 else "idle", x),
        [s.sam("step" if i % 2 else "idle", sx) for i, sx in enumerate(slide(x, s.width, 5))],
    )

    # Nutmeg scampers in, flicks that tail, and dashes off
    x = spot(SQUIRREL_WIDTH)
    yield from card(
        SQUIRREL_CARD,
        [s.squirrel(sx, i, facing="right") for i, sx in enumerate(slide(-SQUIRREL_WIDTH, x, 4))],
        lambda i: s.squirrel(x, i // 2, facing="right"),
        [s.squirrel(sx, i, facing="right") for i, sx in enumerate(slide(x, s.width, 6))],
    )

    # Pip swoops down from the sky, flaps, and flies away
    x = spot(9)
    entry = slide(-9, x, 4)
    yield from card(
        CROW_CARD,
        [s.crow(sx, round(FEET_ROW * (i + 1) / len(entry)), i) for i, sx in enumerate(entry)],
        lambda i: s.crow(x, FEET_ROW, i // 2),
        [s.crow(sx, max(1, FEET_ROW - 2 * i), i) for i, sx in enumerate(slide(x, s.width, 6))],
    )

    # The ball bounces in, settles, and rolls away
    x = spot(1)
    entry = slide(-1, x, 3)
    yield from card(
        BALL_CARD,
        [s.ball(sx, round(3 * abs(math.sin(i * math.pi / 4)) * (1 - i / len(entry))))
         for i, sx in enumerate(entry)],
        lambda i: s.ball(x, 1 if i % 12 == 0 else 0),
        [s.ball(sx) for sx in slide(x, s.width, 5)],
    )

    # Roll the show
    line = "and now... the show!"
    x = (s.width - len(line)) // 2
    for k in range(0, len(line) + 3, 3):
        yield s.frame(([line[:k]], x, 7, CARD_COLOR))
    for _ in range(8):
        yield s.frame(([line], x, 7, CARD_COLOR))


def intro(s):
    yield from title_card(s)
    yield from cast_roll(s)
