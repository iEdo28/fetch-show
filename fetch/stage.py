"""Turning drawings into a frame: the sky, the weather, the ground, the seasonal props,
and whatever the characters are doing on top."""

import math
import random

from .config import (
    CASTLE_COLOR, PARASOL_COLOR, SAND_COLOR, SEA_COLOR, SKY_HEART_COLOR,
    ANTLER_COLOR, BAT_COLOR, BOLT_COLOR, FLASH_COLOR, GLOW_COLORS, PRESENT_COLORS, SANTA_COLOR, STORM_CLOUD_COLOR,
    THUNDER_COLOR, TREE_COLOR, TREE_LIGHT_COLORS, TRUNK_COLOR, WITCH_HAT_COLOR,
    RIVALS, ALERT_COLOR, BALL_COLOR, BANDAGE_COLOR, BEANIE_COLOR, BOOTS_COLOR, FLOWER_HAT_COLOR, NOSE_COLOR,
    SCARF_COLOR, BIRD_COLOR, CAT_COLOR, CLOUD_COLORS, CLOUD_NIGHT, CROW_COLOR, DOG_COLOR,
    EGG_COLORS, FEET_ROW, FLOWER_COLORS, FOOTPRINT_COLOR, GRASS_DAY, GRASS_NIGHT, GROUND_ROW, HAT_COLOR,
    LEAF_COLORS, MOON_COLOR, PERSON_COLOR, PUDDLE_COLOR, PUMPKIN_COLOR, RAIN_COLOR, ROWS, SAM_X,
    SEASON_GROUND, SKY, SNORE_COLOR, SNOW_COLOR, SNOW_GROUND, SNOWMAN_COLOR, SQUIRREL_COLOR, STAR_COLOR,
    STEM_COLOR, SUN_COLORS, SUN_ROW, UMBRELLA_COLOR,
)
from .sprites import (
    PARASOL, PARASOL_WIDTH, SANDCASTLE, SANDCASTLE_FALLEN, SEA_WAVES,
    ANTLERS, BAT_FRAMES, BOLT, MOON_WIDTH, PRESENTS, TREE, TREE_WIDTH, WITCH_HAT,
    BALL, BIRD_FRAMES, CAT_FACE, CAT_WIDTH, CLOUDS, CROW_FRAMES, DOG_SCARF, DOG_WIDTH, EGG, FLOCK, FOOT_CHARS,
    MOON, PUMPKIN, PUMPKIN_STEM, PUMPKIN_WIDTH, SAM_HEIGHT, SAM_WIDTH, SNOWMAN_HAT, SNOWMAN_WIDTH, SQUIRREL_FRAMES,
    STORM_CLOUDS, SUN_FRAMES, UMBRELLA, ball_pile, cat_loaf, merge, mirror, sam_sprite, snowman, width_of,
    snowman_fallen, snowman_tilted,
)
from .world import World

RESET = "\033[0m"


def fg(code):
    """Terminal code to switch the text color (256-color palette)."""
    return f"\033[38;5;{code}m"


def stamp(grid, sprite, x, bottom, color=None):
    """Draw a sprite with its bottom row on `bottom`. Spaces are see-through."""
    for i, line in enumerate(reversed(sprite)):
        row = bottom - i
        for j, ch in enumerate(line):
            col = x + j
            if ch != " " and 0 <= row < len(grid) and 0 <= col < len(grid[0]):
                grid[row][col] = (ch, color)


def to_text(row):
    """Turn a row of (character, color) cells into a printable line."""
    last = max((i for i, (ch, _) in enumerate(row) if ch != " "), default=-1)
    out, current = [], None
    for ch, color in row[:last + 1]:
        if ch != " " and color != current:
            out.append(fg(color) if color is not None else RESET)
            current = color
        out.append(ch)
    out.append(RESET)
    return "".join(out)


def new_sky():
    return {"sun": (SUN_ROW, SUN_COLORS[0]), "moon": False, "stars": 0, "birds": True, "night": False}


def star_field(width):
    """The same scattered stars every night, for a given screen width."""
    rng = random.Random(width)
    stars = []
    while len(stars) < width // 4:
        x, row = rng.randrange(width - 1), rng.randrange(SKY + 3)
        if not (x >= width - MOON_WIDTH - 4 and row < 6):  # leave room for the moon
            stars.append((x, row))
    return stars


def snores(x, bottom, tick):
    """z's drifting up and to the right from a sleeper."""
    return [(["zzZ"[k - 1]], x + k, bottom - k, SNORE_COLOR) for k in range(1, (tick // 3) % 4 + 1)]


def sky_layers(width, tick, sky, weather, storm=False, holiday=None):
    layers = []
    for i, (x, row) in enumerate(star_field(width)[:sky["stars"]]):
        layers.append(([".+*."[(tick // 3 + i) % 4]], x, row, STAR_COLOR))
    if sky["moon"]:
        layers.append((MOON, width - MOON_WIDTH - 2, 4, MOON_COLOR))
    clear = weather in ("sunny", "leaves")
    if sky["sun"] is not None and clear:
        bottom, color = sky["sun"]
        layers.append((SUN_FRAMES[(tick // 4) % 2], width - 8, bottom, color))
    cloud_color = CLOUD_NIGHT if sky["night"] else STORM_CLOUD_COLOR if storm else CLOUD_COLORS[weather]
    for sprite, start in CLOUDS + ([] if clear else STORM_CLOUDS):
        span = width + 8
        x = (int(start * span) - tick // 3) % span - 6  # drift slowly left
        layers.append((sprite, x, 1, cloud_color))
    if holiday == "valentine":
        for i in range(width // 14):
            span = width + 6
            x = (i * 17 - tick // 4) % span - 3
            layers.append((["<3"], x, 1 + (i * 3) % 5, SKY_HEART_COLOR))
    if sky["birds"] and clear:
        span = width + 30
        flock_x = (tick // 2) % span - 15
        frames, color = (BAT_FRAMES, BAT_COLOR) if holiday == "halloween" else (BIRD_FRAMES, BIRD_COLOR)
        for i, (dx, row) in enumerate(FLOCK):
            layers.append(([frames[(tick + i) % 2]], flock_x + dx * 2, row, color))
    return layers


def weather_layers(width, tick, weather, storm=False):
    """Falling rain, drifting snow, or autumn leaves. Each one has its own column and head start."""
    if weather == "sunny":
        return []
    rng = random.Random(width + 1)
    fall_rows = GROUND_ROW
    umbrella_top = FEET_ROW - SAM_HEIGHT - len(UMBRELLA) + 1
    layers = []
    for i in range(width // 2 if storm else width // 3):
        x, start = rng.randrange(width), rng.randrange(fall_rows)
        if weather == "rain":
            row = (tick + start) % fall_rows
            if storm:
                x -= row // 2  # driven sideways by the wind
            if SAM_X <= x < SAM_X + width_of(UMBRELLA) and row >= umbrella_top:
                continue  # Sam stays dry under the umbrella
            layers.append((["/" if storm else "|"], x, row, RAIN_COLOR))
        elif weather == "leaves":
            if i % 3:
                continue  # leaves are sparser than snowflakes
            row = (tick // 2 + start) % fall_rows
            drift = round(2 * math.sin((tick + i * 7) / 6)) + row // 3  # blown sideways as they fall
            layers.append(([",`'~"[i % 4]], x + drift, row, LEAF_COLORS[i % len(LEAF_COLORS)]))
        else:
            row = (tick // 2 + start) % fall_rows
            drift = round(math.sin((tick + i * 7) / 5))
            layers.append((["*."[i % 2]], x + drift, row, SNOW_COLOR))
    return layers


class Scene:
    """Everything one episode shares: the screen size, the sky, the season and weather,
    the show's memory, and how to draw a frame."""

    def __init__(self, width, ticks, sky, weather="sunny", season=None, slip=False, trip=False, twist=False,
                 world=None, storm=False, holiday=None):
        self.width = width
        self.ticks = ticks
        self.sky = sky
        self.weather = weather
        self.season = season
        self.slip = slip  # Sam slips in the puddle after throwing
        self.trip = trip  # Sam trips over the cat after a plain fetch
        self.twist = twist  # the revenge goes wrong: the dog trips and the cat gets the ball back
        self.world = world or World()
        self.stash = self.world.stash  # balls in Mochi's pile right now
        self.storm = storm and weather == "rain"
        self.holiday = holiday   # "halloween", "christmas", or None
        self.lightning = random.Random(width + 9)
        self.next_flash = self.lightning.randrange(25, 60)
        self.flashed_at = None
        self.bolt_x = 0
        self.tick = 0
        self.frames_drawn = 0
        self.events = set()  # things that happened this episode, for the show's memory
        self.cat_x = (width - CAT_WIDTH) // 2
        self.footprints = set()

        rng = random.Random(width + 2)
        # One puddle right where Sam stands, the rest scattered
        self.puddles = [SAM_X + 4] + [rng.randrange(14, width - 6) for _ in range(max(2, width // 25))]

        # Flowers and Easter eggs stay clear of Sam and the cat
        near_cat = set(range(self.cat_x - 3, self.cat_x + CAT_WIDTH + 2))
        rng = random.Random(width + 3)
        self.flowers = [x for x in (rng.randrange(SAM_X + SAM_WIDTH + 1, width - 1) for _ in range(width // 5))
                        if x not in near_cat]
        self.eggs = [x for x in (rng.randrange(SAM_X + SAM_WIDTH + 1, width - 3) for _ in range(width // 18))
                     if x not in near_cat and x + 2 not in near_cat]

        rng = random.Random(width + 4)
        self.leaf_pile = [rng.randrange(width - 1) for _ in range(width // 3)]

        self.pumpkin_x = (SAM_X + SAM_WIDTH + self.cat_x - PUMPKIN_WIDTH) // 2
        self.tree_x = self.cat_x + CAT_WIDTH + 8   # clear of where the dog waits, and of Mochi's pile
        self.snowman_x = self.cat_x + CAT_WIDTH + 14
        if season == "winter":
            self.snowman_x = self.tree_x + TREE_WIDTH + 2
        if holiday == "beach":
            self.snowman_x = self.tree_x + PARASOL_WIDTH + 2
        self.found_eggs = set()  # eggs already sniffed out on the Easter egg hunt
        # For clips: what happens when (sound cues), and where the dog is (for the camera)
        self.cues = []
        self.dog_x = None
        self.dog_height = 0
        self.cat_pos = None   # where the cat and the ball were last drawn, for the clip camera
        self.ball_pos = None
        self.said_before, self.said_now = set(), set()
        self.snowman_damage = self.world.snowman_damage
        self.snowman_down = None  # the frame Biscuit knocked it over

    def cue(self, name):
        """Note a moment for the soundtrack: name happens on the frame being drawn next."""
        self.cues.append((self.frames_drawn, name))

    def frame(self, *layers):
        """Draw one frame: background first, then each layer in order, so later ones sit on top.
        A layer is (sprite, x, bottom_row, color), or a list of layers."""
        self.tick = next(self.ticks)
        self.frames_drawn += 1
        grid = [[(" ", None)] * self.width for _ in range(ROWS)]

        def draw(items):
            for item in items:
                if isinstance(item, list):
                    draw(item)
                else:
                    stamp(grid, *item)

        self.said_before, self.said_now = self.said_now, set()
        if self.storm and self.frames_drawn >= self.next_flash:
            self.cue("thunder")
            self.flashed_at = self.frames_drawn
            self.bolt_x = self.lightning.randrange(10, self.width - 10)
            self.next_flash = self.frames_drawn + self.lightning.randrange(40, 90)

        draw(sky_layers(self.width, self.tick, self.sky, self.weather, self.storm, self.holiday))
        draw(weather_layers(self.width, self.tick, self.weather, self.storm))
        draw(self.ground())
        draw(self.props())
        draw(layers)

        since = None if self.flashed_at is None else self.frames_drawn - self.flashed_at
        if since is not None and since < 2:  # FLASH: everything lights up, and there's the bolt
            grid[:] = [[(ch, FLASH_COLOR if ch != " " else None) for ch, _ in row] for row in grid]
            stamp(grid, BOLT, self.bolt_x, len(BOLT) - 1, BOLT_COLOR)
        elif since is not None and 3 <= since < 9:  # ...and the thunder a moment later
            boom = "KRAKA-BOOM!"
            stamp(grid, [boom], (self.width - len(boom)) // 2, 2, THUNDER_COLOR)
        return [to_text(row) for row in grid]

    @property
    def spooked(self):
        """Mochi's fur stands on end for a little while after each thunderclap."""
        return self.flashed_at is not None and self.frames_drawn - self.flashed_at < 14

    def ground(self):
        width = self.width
        if self.weather == "snow":
            layers = [(["_" * (width - 1)], 0, GROUND_ROW, SNOW_GROUND)]
            layers += [(["."], x, GROUND_ROW, FOOTPRINT_COLOR) for x in self.footprints]
        else:
            color = GRASS_NIGHT if self.sky["night"] else SEASON_GROUND.get(self.season, GRASS_DAY)
            if self.holiday == "beach":
                color = SAND_COLOR
            layers = [(["_" * (width - 1)], 0, GROUND_ROW, color)]
        if self.weather == "leaves":
            fallen = min(len(self.leaf_pile), self.frames_drawn // 4)  # leaves pile up over time
            for i, x in enumerate(self.leaf_pile[:fallen]):
                layers.append(([",`"[i % 2]], x, GROUND_ROW, LEAF_COLORS[i % len(LEAF_COLORS)]))
        if self.weather == "rain":
            size = min(3, self.frames_drawn // 25)  # puddles grow as the rain keeps coming
            for i, x in enumerate(self.puddles):
                grown = max(2, size) if i == 0 else size
                if grown:
                    layers.append((["~" * (grown * 2 + 1)], x - grown, GROUND_ROW, PUDDLE_COLOR))
        return layers

    def props(self):
        """Seasonal decorations: spring flowers and Easter eggs, a pumpkin, a snowman."""
        layers = []
        if self.season == "spring":
            for i, x in enumerate(self.flowers):
                layers.append((["*"], x, FEET_ROW, FLOWER_COLORS[i % len(FLOWER_COLORS)]))
            for i, x in enumerate(self.eggs):
                if x not in self.found_eggs:
                    layers.append((EGG, x, FEET_ROW, EGG_COLORS[i % len(EGG_COLORS)]))
        elif self.season == "autumn":
            spots = [self.pumpkin_x]
            if self.holiday == "halloween":  # lit up, and two more besides
                spots += [self.pumpkin_x - PUMPKIN_WIDTH - 1, self.snowman_x]
            for i, x in enumerate(spots):
                glow = GLOW_COLORS[(self.tick // 2 + i) % len(GLOW_COLORS)] if self.holiday else PUMPKIN_COLOR
                layers += [(PUMPKIN, x, FEET_ROW, glow), (PUMPKIN_STEM, x + 4, FEET_ROW - 1, STEM_COLOR)]
        elif self.season == "winter":
            layers += self.tree_layers()
            layers += self.snowman_layers()
        if self.holiday == "beach":
            shift = self.tick // 3  # the sea rolling in at the horizon
            start = SAM_X + SAM_WIDTH + 1  # the sea starts past Sam, so it doesn't show through
            for row in range(2):
                waves = "".join(SEA_WAVES[(i + shift + row * 3) % len(SEA_WAVES)] for i in range(start, self.width - 1))
                layers.append(([waves], start, FEET_ROW - 7 + row, SEA_COLOR))
            layers += [(PARASOL, self.tree_x, FEET_ROW, PARASOL_COLOR)]
            layers += self.snowman_layers()
        return layers

    def sandcastle_layers(self):
        x = self.snowman_x
        since = None if self.snowman_down is None else self.frames_drawn - self.snowman_down
        if since is None:
            return [(SANDCASTLE, x, FEET_ROW, CASTLE_COLOR)]
        if since < 3:
            return [(SANDCASTLE, x + 1, FEET_ROW, CASTLE_COLOR), (["!"], x + 3, FEET_ROW - 6, ALERT_COLOR)]
        layers = [(SANDCASTLE_FALLEN, x - 1, FEET_ROW, CASTLE_COLOR)]
        if since < 8:
            layers.append(([". : ."], x + 1, FEET_ROW - 1, SAND_COLOR))  # a puff of sand
        return layers

    def tree_layers(self):
        """A Christmas tree with twinkling lights (up all winter), and presents on Christmas."""
        x = self.tree_x
        layers = [(TREE, x, FEET_ROW, TREE_COLOR), (["|_|"], x + 3, FEET_ROW, TRUNK_COLOR),
                  (["*"], x + 4, FEET_ROW - 5, BOLT_COLOR)]
        lights = [(r, c) for r, line in enumerate(TREE[1:-2], start=1) for c, ch in enumerate(line) if ch in "*."]
        for i, (r, c) in enumerate(lights):
            color = TREE_LIGHT_COLORS[(i + self.tick // 3) % len(TREE_LIGHT_COLORS)]
            layers.append(([TREE[r][c]], x + c, FEET_ROW - (len(TREE) - 1 - r), color))
        if self.holiday == "christmas":  # presents either side of the trunk, under the branches
            for i, (gift, dx) in enumerate(zip(PRESENTS[0].split(), (-1, 6))):
                layers.append(([gift], x + dx, FEET_ROW, PRESENT_COLORS[i % len(PRESENT_COLORS)]))
        return layers

    @property
    def knockable(self):
        """Something for the dog to bump into: the snowman in winter, the sandcastle on the beach."""
        return self.season == "winter" or self.holiday == "beach"

    def snowman_layers(self):
        if self.holiday == "beach":
            return self.sandcastle_layers()
        x, damage = self.snowman_x, self.snowman_damage
        has_hat = damage == 0
        since = None if self.snowman_down is None else self.frames_drawn - self.snowman_down
        if since is None:
            body = snowman(damage)
            layers = [(body, x, FEET_ROW, SNOWMAN_COLOR)]
            if has_hat:
                layers.append((SNOWMAN_HAT, x + 2, FEET_ROW - len(body), HAT_COLOR))
        elif since < 3:
            body = snowman_tilted(damage)
            layers = [(body, x, FEET_ROW, SNOWMAN_COLOR), (["!"], x + 3, FEET_ROW - len(body) - 2, ALERT_COLOR)]
            if has_hat:
                layers.append((SNOWMAN_HAT, x + 4, FEET_ROW - len(body), HAT_COLOR))
        else:
            fallen = snowman_fallen(damage)
            layers = [(fallen, x, FEET_ROW, SNOWMAN_COLOR)]
            if has_hat:
                layers.append((SNOWMAN_HAT, x + len(fallen[0]) + 1, FEET_ROW, HAT_COLOR))
            if since < 8:
                layers.append((["* . *"], x + 3, FEET_ROW - 1, SNOW_COLOR))  # a puff of snow
        return layers

    # --- What sits in the middle of the yard ------------------------------------------

    # --- Moods show up in faces and tails ----------------------------------------------

    def dog_tail(self, step=0):
        mood = self.world.dog_mood
        if mood == "grumpy":
            return "down"
        if mood == "happy":
            return "wag" if (step // 2) % 2 else "up"
        return "wag" if (step // 6) % 3 == 0 else "up"

    @property
    def blinking(self):
        """Everyone blinks now and then: one frame in every few seconds."""
        return self.tick % 41 == 40

    def dog_eye(self):
        if self.blinking:
            return "-"
        return {"happy": "^", "grumpy": "."}.get(self.world.dog_mood, "'")

    def cat_sleep_face(self):
        if self.world.friendship <= RIVALS:
            return "-.O"  # only pretending: one eye on the dog
        return {"smug": "-w-", "annoyed": "=.="}.get(self.world.cat_mood, "-.-")

    @property
    def pile_x(self):
        return self.cat_x + CAT_WIDTH

    def obstacle(self, face=None):
        """The sleeping cat and its pile of balls, as one sprite, for working out jumps over them."""
        face = face or self.cat_sleep_face()
        if not self.stash:
            return cat_loaf(face)
        return merge(cat_loaf(face), ball_pile(self.stash), CAT_WIDTH)

    def pile(self):
        return (ball_pile(self.stash), self.pile_x, FEET_ROW, BALL_COLOR) if self.stash else []

    # --- Helpers that place each character on the stage -------------------------------

    def dog(self, sprite, x, height=0):
        if height == 0 and self.weather == "snow" and x % 3 == 0:
            feet = [j for j, ch in enumerate(sprite[-1]) if ch in FOOT_CHARS]
            if feet:
                self.footprints.add(x + feet[0])  # a paw print every few steps
        if (self.knockable and self.snowman_down is None and height < 4
                and x <= self.snowman_x + SNOWMAN_WIDTH - 1 and x + DOG_WIDTH - 1 >= self.snowman_x):
            self.snowman_down = self.frames_drawn  # bumped into it!
            self.cue("thud")
            self.events.add("sandcastle" if self.holiday == "beach" else "snowman")
        if height and not self.dog_height:
            self.cue("jump")
        elif self.dog_height and not height:
            self.cue("land")
        self.dog_x, self.dog_height = x, height
        bottom = FEET_ROW - height
        top = bottom - len(sprite) + 1
        layers = [(sprite, x, bottom, DOG_COLOR)]
        accents = [("@", NOSE_COLOR)]
        if self.holiday == "christmas" and len(sprite) == 6:
            facing_right = sprite[2].find("@") > DOG_WIDTH // 2
            layers.append((ANTLERS, x + (11 if facing_right else DOG_WIDTH - 15), top - 1, ANTLER_COLOR))
        if self.season == "winter" and len(sprite) == 6:  # a red scarf, standing poses only
            facing_right = sprite[2].find("@") > DOG_WIDTH // 2
            layers.append((["="], x + (DOG_SCARF if facing_right else DOG_WIDTH - 1 - DOG_SCARF), top + 3, SCARF_COLOR))
        for text, color in accents:
            for r, line in enumerate(sprite):
                col = line.find(text)
                if col >= 0:
                    layers.append(([text], x + col, top + r, color))
        return layers

    def sam_outfit(self):
        """Sam's hat, scarf and boots for today: by season, plus any running gags."""
        hat, hat_color, neck = "___", None, "  "
        if self.season == "spring":
            hat, hat_color = "_*_", FLOWER_HAT_COLOR
        elif self.season == "winter":
            hat, hat_color = "/*\\", BEANIE_COLOR
        if self.season in ("autumn", "winter"):
            neck = "~~"
        if self.holiday == "christmas":
            hat, hat_color = "/\\o", SANTA_COLOR
        if self.world.bandage:
            hat, hat_color = hat[0] + "+" + hat[2], BANDAGE_COLOR
        boots = self.world.boots and self.weather == "rain"
        return hat, hat_color, neck, boots

    def sam(self, pose="idle", x=SAM_X, height=0):
        hat, hat_color, neck, boots = self.sam_outfit()
        face = "-_-" if self.blinking else "^_^"
        sprite = sam_sprite(pose, face=face, hat=hat, neck=neck, boots=boots)
        bottom = FEET_ROW - height
        top = bottom - len(sprite) + 1
        layers = [(sprite, x, bottom, PERSON_COLOR)]
        # Color the outfit: hat, scarf, boots
        accents = [(0, hat, hat_color), (2, "~~", SCARF_COLOR), (len(sprite) - 1, "[|  |]", BOOTS_COLOR)]
        for row, text, color in accents:
            col = sprite[row].find(text) if color and row < len(sprite) else -1
            if col >= 0:
                layers.append(([text], x + col, top + row, color))
        if self.weather == "rain" and pose != "fallen" and height == 0:
            layers.append((UMBRELLA, x, top - 1, UMBRELLA_COLOR))
        return layers

    def ball(self, x, height=0):
        self.ball_pos = x
        return ([BALL], x, FEET_ROW - height, BALL_COLOR)

    def cat(self, sprite, x, height=0):
        self.cat_pos = (x, width_of(sprite))
        return (sprite, x, FEET_ROW - height, CAT_COLOR)

    def sleeping_cat(self, face=None):
        if self.spooked:
            layers = [self.cat(cat_loaf("O.O", spiky=True), self.cat_x), self.pile()]
        else:
            layers = [self.cat(cat_loaf(face or self.cat_sleep_face()), self.cat_x), self.pile(),
                      *snores(self.cat_x + CAT_FACE + 2, FEET_ROW - 2, self.tick + 1)]
        if self.holiday == "halloween":
            layers.append((WITCH_HAT, self.cat_x + 2, FEET_ROW - 3, WITCH_HAT_COLOR))
        return layers

    def squirrel(self, x, step, height=0, facing="left"):
        sprite = SQUIRREL_FRAMES[step % 2]
        return (sprite if facing == "left" else mirror(sprite), x, FEET_ROW - height, SQUIRREL_COLOR)

    def crow(self, x, bottom_row, step):
        return (CROW_FRAMES[step % 2], x, bottom_row, CROW_COLOR)

    SOUNDS_FOR_WORDS = {"!": "pop", "!!": "pop", "?": "huh", "woof!": "bark", "hss": "hiss", "hss!": "hiss",
                        "OW!": "ouch", "grr": "growl", "SHARE!": "pop", "hey!": "pop", "whoooo": "whoosh",
                        "eek!": "pop", "*": "crash", "ha!": "laugh", "hmph!": "hiss", "sniff": "sniff"}

    def say(self, text, x, height):
        """A little "!" or "?" (or any short word) floating `height` rows above the ground."""
        if text and text not in self.said_before and text not in self.said_now and text in self.SOUNDS_FOR_WORDS:
            self.cue(self.SOUNDS_FOR_WORDS[text])
        self.said_now.add(text)
        return ([text], x, FEET_ROW - height, ALERT_COLOR)
