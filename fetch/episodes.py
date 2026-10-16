"""The stories. Each episode is a generator that yields one frame at a time and
returns who ended up with the ball ("dog", "cat", or None)."""

import math
import random

from .config import (
    ALERT_COLOR, BALL_CARD, BALL_COLOR, BEST_FRIENDS, CAKE_COLOR, CANDLE_COLOR, CARD_COLOR, CAT_CARD, CROW_CARD,
    EGG_COLORS, DOG_CARD, DOG_START, DUST_COLOR, FEET_ROW, FLAME_COLOR, FLOWER_COLORS, HEART_COLOR, OPENER_ODDS, PUDDLE_COLOR,
    REVENGE_TRIP_CHANCE, RIVALS, ROWS, SAM_X, SEASON_COLORS, SEASON_WEATHER, SEASONS, SLIP_CHANCE, SMOKE_COLOR,
    SQUIRREL_CARD, STORM_CHANCE, SUN_COLORS, SUN_ROW, TEXT_COLOR, THROWER_CARD, TITLE_COLORS, TRIP_CHANCE, WEATHER_WORDS, YEAR,
)
from .motion import Leap, ball_path, clearance, slide
from .sprites import (
    EGG, BALL, CAKE, CAKE_WIDTH, CANDLES, CAT_FACE, CAT_RUN_WIDTH, CAT_WIDTH, CROW_BEAK, DOG_HEAD, DOG_JUMP, DOG_MOUTH,
    DOG_STAND, DOG_WALK, DOG_WIDTH, LANDING_DUST, SAM_HAND, SAM_RELEASE, SAM_WIDTH, SAM_WINDUP, SQUIRREL_FRAMES,
    SQUIRREL_WIDTH, ball_pile, cat_loaf, cat_running, dog_crouch, dog_lying, dog_sprite, mirror, sam_sprite,
    width_of,
)
from .stage import new_sky, snores, star_field

# Holiday specials, by an episode's place in the year (0-11; 12 is the finale)
HOLIDAYS = {0: "easter", 2: "valentine", 3: "beach", 8: "halloween", 10: "christmas"}
HOLIDAY_NAMES = {"easter": "Easter", "valentine": "Valentine's", "beach": "Beach Day", "halloween": "Halloween",
                 "christmas": "Christmas"}
HOLIDAY_STORIES = {"easter": "egghunt", "valentine": "valentine"}  # holidays with a story all their own
HOLIDAY_SEASONS = {"easter": "spring", "valentine": "spring", "beach": "summer", "halloween": "autumn",
                   "christmas": "winter"}

DOG_NAME = DOG_CARD[0].title()
CAT_NAME = CAT_CARD[0].title()

DOG_ABOVE = 7     # how far above the dog's paws a "!" floats
SAM_ABOVE = 10    # same for Sam (three more when the umbrella is up)


# --- Planning an episode --------------------------------------------------------------

class Episode:
    """What happens in one episode: which story, which season, what weather, and any mishaps."""

    def __init__(self, number, kind, season, weather, slip=False, trip=False, twist=False, world=None,
                 label=None, storm=False, holiday=None):
        self.number = number
        self.storm = storm        # a thunderstorm instead of plain rain
        self.holiday = holiday    # "halloween", "christmas", or None
        self.label = label or f"EPISODE {number}"  # what the title card calls it
        self.kind = kind
        self.season = season
        self.weather = weather
        self.slip = slip
        self.trip = trip
        self.twist = twist
        self.world = world

    @property
    def title(self):
        world = self.world
        if self.kind == "squirrel":
            return "Squirrel!"
        if self.kind == "crow":
            return "Fowl Play"
        if self.kind == "steal":
            return "The Ball Thief"
        if self.kind == "friends":
            return "Best Friends"
        if self.kind == "ambush":
            return "Ambush!"
        if self.kind == "egghunt":
            return "The Egg Hunt"
        if self.kind == "valentine":
            return "Forced to Share"
        if self.kind == "finale":
            return "Happy Birthday, Sam!"
        if self.kind == "revenge":
            return "Sweet Revenge"
        if self.slip:
            return "The Great Puddle"
        if self.trip:
            return "Not Again, Sam!" if world and world.bandage else "Sam Takes a Tumble"
        if world and world.boots and self.weather == "rain":
            return "New Boots"
        if world and self.season == "winter" and world.snowman_damage:
            return f"Snowman, Take {world.snowman_damage + 1}"
        return {"spring": "First Day of Spring", "summer": "A Perfect Jump",
                "autumn": "Pumpkin Patch", "winter": "Snow Day"}[self.season]

    @property
    def story(self):
        return STORIES[self.kind]


def plan_episode(number, world):
    """Every season tells one three-part story: an opener, the cat's steal, and the dog's revenge.
    Once they've become good enough friends, the steal turns into something nicer instead,
    and with nothing to take revenge for, the season ends with another opener."""
    place = (number - 1) % YEAR
    if place == YEAR - 1:
        return make_episode(number, "finale", "winter", "snow", world, slip=False, trip=False, twist=False,
                            label="SEASON FINALE")
    return plan_part(number, world, SEASONS[place // 3], place % 3, HOLIDAYS.get(place))


def plan_part(number, world, season, part, holiday=None):
    """Plan episode `number` as `part` (0, 1 or 2) of a season's three-part story, in `season`.
    The posting calendar uses this directly so episodes can follow the real seasons."""
    opener = random.choices(list(OPENER_ODDS), list(OPENER_ODDS.values()))[0]
    if world.friendship <= RIVALS:
        opener = "ambush"  # Mochi's been waiting for this
    if part == 0:
        kind = opener
    elif part == 1:
        kind = "friends" if world.friendship >= BEST_FRIENDS else "steal"
    else:
        kind = "revenge" if world.last_kind == "steal" else opener
    kind = HOLIDAY_STORIES.get(holiday, kind)
    weather = "sunny" if holiday in ("easter", "valentine", "beach") else None  # nice days out
    return make_episode(number, kind, season, weather, world, holiday=holiday)


def make_episode(number, kind, season, weather, world, slip=None, trip=None, twist=None, label=None, storm=None,
                 holiday=None):
    """An episode of `kind` in `season`. Weather and mishaps left as None are rolled at random."""
    if weather is None:
        odds = SEASON_WEATHER[season]
        weather = random.choices(list(odds), list(odds.values()))[0]
    if slip is None:
        slip = weather == "rain" and not world.boots and random.random() < SLIP_CHANCE
    if trip is None:
        trip = kind == "fetch" and random.random() < TRIP_CHANCE
    if twist is None:
        twist = kind == "revenge" and random.random() < REVENGE_TRIP_CHANCE
    if storm is None:
        storm = weather == "rain" and random.random() < STORM_CHANCE
    return Episode(number, kind, season, weather, slip=slip, trip=trip, twist=twist, world=world, label=label,
                   storm=storm, holiday=holiday)


def directed_episode(world, kind=None, season=None, weather=None, slip=None, trip=None, twist=None, storm=None,
                     holiday=None):
    """Director's mode: an episode picked by hand. Anything left out is chosen at random."""
    kind = kind or HOLIDAY_STORIES.get(holiday) or random.choice(list(STORIES))
    season = season or HOLIDAY_SEASONS.get(holiday) or random.choice(SEASONS)
    if storm:
        weather = "rain"
    return make_episode(world.episodes + 1, kind, season, weather, world, slip=slip, trip=trip, twist=twist,
                        label="DIRECTOR'S CUT", storm=storm, holiday=holiday)


# --- Title and end cards ----------------------------------------------------------------

def centered_lines(s, lines, shown):
    """Lines of (text, row, color), each centered, with only the first `shown` characters typed out."""
    layers = []
    for text, row, color in lines:
        if shown > 0:
            layers.append(([text[:shown]], (s.width - len(text)) // 2, row, color))
        shown -= len(text)
    return layers


def card(s, lines, hold=14):
    total = sum(len(text) for text, _, _ in lines)
    for k in range(0, total + 3, 3):
        yield s.frame(centered_lines(s, lines, k))
    for _ in range(hold):
        yield s.frame(centered_lines(s, lines, total))


def episode_card(s, episode):
    lines = [
        (episode.label, 4, TEXT_COLOR),
        (episode.title, 6, CARD_COLOR),
        (f"{episode.season}, {'stormy' if episode.storm else WEATHER_WORDS[episode.weather]}", 8,
         SEASON_COLORS[episode.season]),
    ]
    if episode.holiday:
        lines[1] = (f"{episode.title} ~ {HOLIDAY_NAMES[episode.holiday]} special", 6, CARD_COLOR)
    if episode.world and episode.number > 1:
        w = episode.world
        cat = "has one eye on him" if w.friendship <= RIVALS else f"looks {w.cat_mood}"
        lines.append((f"{DOG_NAME} feels {w.dog_mood}. {CAT_NAME} {cat}.", 10, TEXT_COLOR))
    yield from card(s, lines)


def standings(world, top):
    """The score, the friendship meter and Mochi's pile, as card lines starting at row `top`."""
    meter = "".join("*" if level == world.friendship else "-" for level in range(-BEST_FRIENDS, BEST_FRIENDS + 1))
    lines = [
        (f"{DOG_NAME} {world.score['dog']}   {CAT_NAME} {world.score['cat']}", top, TEXT_COLOR),
        (f"rivals {meter} friends", top + 2, TEXT_COLOR),
    ]
    if world.stash:
        balls = "ball" if world.stash == 1 else "balls"
        lines.append((f"{CAT_NAME}'s pile: {world.stash} {balls}", top + 4, TEXT_COLOR))
    return lines


def end_card(s, episode, world):
    closing = {"steal": "to be continued...", "finale": "~ SEE YOU NEXT YEAR ~"}.get(episode.kind, "~ THE END ~")
    yield from card(s, [(closing, 4, CARD_COLOR)] + standings(world, 6))


def previously_card(s, world):
    """When the show picks up from a save: a quick reminder of where things stand."""
    aired = "1 episode" if world.episodes == 1 else f"{world.episodes} episodes"
    yield from card(s, [
        ("Previously on FETCH!", 3, CARD_COLOR),
        (f"{aired} so far", 5, TEXT_COLOR),
    ] + standings(world, 7), hold=20)


# --- Little helpers for placing things ---------------------------------------------------

def over_dog(s, text, x, height=0, facing="right"):
    head = DOG_HEAD if facing == "right" else DOG_WIDTH - 1 - DOG_HEAD
    return s.say(text, x + head, height + DOG_ABOVE)


def over_sam(s, text, x=SAM_X):
    return s.say(text, x + 4, SAM_ABOVE + (3 if s.weather == "rain" else 0))


def over_cat(s, text):
    return s.say(text, s.cat_x + CAT_FACE, 4)


def walking_dog(s, pos, mouth=" ", tail=None):
    """The dog mid-stride, with the tail and eyes of its current mood."""
    return dog_sprite(DOG_WALK[pos % 4], tail=tail or s.dog_tail(pos), eye=s.dog_eye(), mouth=mouth)


def standing_dog(s, step=0, mouth=" "):
    return dog_sprite(DOG_STAND, tail=s.dog_tail(step), eye=s.dog_eye(), mouth=mouth)


# --- Sam's mishaps -----------------------------------------------------------------------

def thrower_pose(s, f):
    """What Sam is doing f frames after letting go of the ball."""
    if f < 3:
        if f == 0:
            s.cue("throw")
        return s.sam("throw")
    if not s.slip or f >= 35:
        return s.sam("idle")
    if f < 5:  # whoops! feet go out from under
        if f == 3:
            s.cue("splash")
        s.events.add("slipped")
        return [s.sam("slip"), over_sam(s, "!")]
    layers = [s.sam("sitting")]  # sitting in the puddle
    if f < 9:
        layers.append((["'  .    .  '"], SAM_X - 1, FEET_ROW - 1, PUDDLE_COLOR))  # splash
    return layers


def sam_trips(s, dog_pos, dog_pose):
    """Sam jogs over to the dog, trips over the sleeping cat, and goes flying."""
    s.events.add("tripped")
    cat_x = s.cat_x
    for i, x in enumerate(slide(SAM_X, cat_x - SAM_WIDTH, 2)):
        yield s.frame(s.sam("step" if i % 2 else "idle", x), s.sleeping_cat(), s.dog(dog_pose, dog_pos))
    over = Leap(sam_sprite("cheer"), s.obstacle(), cat_x)
    for x in range(cat_x - SAM_WIDTH + 2, cat_x + CAT_WIDTH - 6, 3):  # airborne over the cat
        yield s.frame(s.sam("cheer", x, over.height(x)), s.sleeping_cat(), s.dog(dog_pose, dog_pos))

    fallen_x = cat_x + CAT_WIDTH - 1
    for i in range(16):
        dizzy = (["*  ." if i % 2 else ".  *"], fallen_x + 10, FEET_ROW - 2, ALERT_COLOR)
        cat = [s.cat(cat_loaf("O.O"), cat_x), s.pile(), over_cat(s, "!")] if i < 8 else s.sleeping_cat()
        yield s.frame(cat, s.sam("fallen", fallen_x), dizzy, s.dog(dog_pose, dog_pos))
    for _ in range(8):
        yield s.frame(s.sleeping_cat(), s.sam("idle", fallen_x + 3), over_sam(s, "OW!", fallen_x + 3),
                      s.dog(dog_pose, dog_pos))


# --- Pieces several stories share ---------------------------------------------------------

def throw_and_chase(s, short_jump=False, stop_after_landing=None, ball_layers=None):
    """Sam throws, and the dog chases the ball over the cat.

    short_jump:          the jump is too low; stop at the moment the dog crashes into the cat
    stop_after_landing:  stop this many steps after landing instead of reaching the ball
    ball_layers(f):      draw the ball differently on chase frame f (say, in a crow's beak)

    Returns (dog position, dog height, chase frames so far, ball path)."""
    path = ball_path(s.width, SAM_X + SAM_RELEASE[0], SAM_RELEASE[1], s.cat_x + CAT_WIDTH)
    ball_stop = path[-1][0]
    obstacle = s.obstacle()
    leap = Leap(dog_sprite(DOG_JUMP), obstacle, s.cat_x)
    pos = DOG_START

    # Wind up and throw while the dog waits, tail going
    for i, pose in enumerate(["idle"] * 2 + ["windup"] * 3):
        hand = SAM_HAND if pose == "idle" else SAM_WINDUP
        in_hand = (SAM_X + hand[0], hand[1])
        grr = [over_dog(s, "grr", pos)] if s.world.dog_mood == "grumpy" and i >= 2 else []
        yield s.frame(s.sam(pose), s.sleeping_cat(), s.ball(*in_hand), s.dog(standing_dog(s, i), pos), *grr)

    f = 0
    prev_height = 0
    landed_at = None
    while pos + DOG_MOUTH < ball_stop:
        if stop_after_landing is not None and landed_at is not None and pos - landed_at >= stop_after_landing:
            break
        height = max(leap.height(pos), clearance(walking_dog(s, pos), obstacle, pos - s.cat_x))
        if short_jump and height:
            height //= 2  # not enough spring...
            if height < leap.need.get(pos, 0):
                return pos, leap.need[pos] - 1, f, path  # ...and crash into the cat

        layers = [thrower_pose(s, f), s.sleeping_cat()]
        if height > 0:
            sprite = dog_sprite(DOG_JUMP, tail=s.dog_tail(pos), eye=s.dog_eye(), ear="up" if height >= 2 else "down")
            if s.world.cat_mood == "annoyed" and leap.need.get(pos, 0):
                layers.append(s.say("hss", s.cat_x - 3, 1))  # still cross about last time
        else:
            sprite = walking_dog(s, pos)
            crouch = dog_crouch(tail=s.dog_tail(pos), eye=s.dog_eye())
            if (not short_jump and leap.height(pos + 1) > 0 and prev_height == 0
                    and not clearance(crouch, obstacle, pos - s.cat_x)):
                sprite = crouch  # ready... spring!
            if pos % 4 == 0:
                layers.append((["."], pos + 1, FEET_ROW, DUST_COLOR))  # kick up a little dust
            if prev_height > 0:
                landed_at = pos
                squash = dog_crouch(tail=s.dog_tail(pos), eye=s.dog_eye())
                if not clearance(squash, obstacle, pos - s.cat_x):
                    sprite = squash  # oof
        prev_height = height

        if landed_at is not None and pos - landed_at < len(LANDING_DUST):
            left, right = LANDING_DUST[pos - landed_at]
            layers.append(([left], pos + 3 - len(left), FEET_ROW, DUST_COLOR))
            layers.append(([right], pos + 13, FEET_ROW, DUST_COLOR))

        layers.append(ball_layers(f) if ball_layers else s.ball(*path[min(f, len(path) - 1)]))
        layers.append(s.dog(sprite, pos, height))
        yield s.frame(*layers)
        pos += 1
        f += 1

    return pos, 0, f, path


def celebrate(s, pos, others=()):
    """The dog has the ball: a surprised "!", a happy hop, and hearts while Sam cheers."""
    holding = dog_sprite(DOG_STAND, tail="wag", mouth=BALL)
    s.cue("catch")
    for _ in range(4):
        yield s.frame(s.sam("cheer"), *others, s.dog(holding, pos), over_dog(s, "!", pos))

    for h in (1, 2, 2, 1):
        hop = dog_sprite(DOG_JUMP, tail="wag", mouth=BALL, ear="up" if h >= 2 else "down")
        yield s.frame(s.sam("idle"), *others, s.dog(hop, pos, h))
    yield s.frame(s.sam("cheer"), *others, s.dog(holding, pos),
                  ([".:"], pos + 1, FEET_ROW, DUST_COLOR), ([":."], pos + 13, FEET_ROW, DUST_COLOR))

    for i in range(18):
        wagging = dog_sprite(DOG_STAND, tail="wag" if i % 2 else "up", mouth=BALL)
        heart = (["<3"], pos + DOG_HEAD - 1, FEET_ROW - DOG_ABOVE - (i % 8) // 2, HEART_COLOR)
        yield s.frame(s.sam("cheer" if (i // 2) % 2 == 0 else "idle"), *others, s.dog(wagging, pos), heart)


def night_falls(s, sleepers, awake_layers):
    """The sun sets, Sam walks home, the stars come out, everyone sleeps, and the sun comes back up.
    `awake_layers` is drawn until dark; `sleepers()` gives the sleeping layers after that."""
    sky = s.sky
    sink_rows = ROWS - SUN_ROW + 1
    sunset_frames = sink_rows * 2
    for i in range(sunset_frames):
        progress = i / (sunset_frames - 1)
        color = SUN_COLORS[min(len(SUN_COLORS) - 1, int(progress * len(SUN_COLORS)))]
        sky["sun"] = (SUN_ROW + round(progress * sink_rows), color)
        layers = list(awake_layers)
        if i < SAM_WIDTH + 1:
            layers.append(s.sam("step" if i % 2 else "idle", SAM_X - i))
        yield s.frame(*layers)

    sky.update(sun=None, birds=False, night=True, moon=True)
    total_stars = len(star_field(s.width))
    for i in range(12):
        sky["stars"] = round(total_stars * (i + 1) / 12)
        yield s.frame(*awake_layers)

    for _ in range(40):
        yield s.frame(*sleepers())

    sky.update(moon=False, night=False)
    for i in range(sink_rows):
        sky["stars"] = round(total_stars * (1 - (i + 1) / sink_rows))
        color = SUN_COLORS[max(0, len(SUN_COLORS) - 1 - i * len(SUN_COLORS) // sink_rows)]
        sky["sun"] = (SUN_ROW + sink_rows - i - 1, color)
        yield s.frame(*sleepers())
    sky.update(new_sky())


# --- The stories ---------------------------------------------------------------------------

def fetch_story(s):
    """A clean jump over the sleeping cat, and the dog catches the ball."""
    pos, _, _, _ = yield from throw_and_chase(s)
    yield from celebrate(s, pos, [s.sleeping_cat()])
    if s.trip:
        yield from sam_trips(s, pos, dog_sprite(DOG_STAND, tail="wag", mouth=BALL))
    return "dog"


def squirrel_story(s):
    """The dog catches the ball, then a squirrel shows up and the ball is forgotten.
    Nutmeg vanishes behind Sam's legs, and the dog skids to a stop at Sam's feet."""
    pos, _, _, _ = yield from throw_and_chase(s)
    holding = dog_sprite(DOG_STAND, tail="wag", mouth=BALL)
    for _ in range(4):
        yield s.frame(s.sam("cheer"), s.sleeping_cat(), s.dog(holding, pos), over_dog(s, "!", pos))

    # Nutmeg pops out from behind Sam and scampers up behind the dog, hopping over the cat
    facing_right = mirror(SQUIRREL_FRAMES[0])
    hop_in = Leap(facing_right, s.obstacle(), s.cat_x)
    target = pos - SQUIRREL_WIDTH - 1
    for i, x in enumerate(slide(SAM_X, target, 3)):
        yield s.frame(s.squirrel(x, i, hop_in.height(x), facing="right"), s.sam("idle"), s.sleeping_cat(),
                      s.dog(holding, pos))

    # The dog spins round and drops the ball. Squirrel!!
    turned = mirror(dog_sprite(DOG_STAND, tail="wag"))
    dropped = s.ball(pos + DOG_MOUTH)
    for i in range(5):
        perch = hop_in.height(target)
        yield s.frame(s.sam("idle"), s.sleeping_cat(), dropped, s.squirrel(target, i, perch, facing="right"),
                      s.say("!", target + 4, perch + 4), s.dog(turned, pos), over_dog(s, "!!", pos, facing="left"))

    # Off they go, back over the cat. Nutmeg ducks behind Sam's legs and is gone;
    # the dog skids to a stop at Sam's feet.
    hop_out = Leap(SQUIRREL_FRAMES[0], s.obstacle(), s.cat_x)
    dog_over = Leap(mirror(dog_sprite(DOG_JUMP)), s.obstacle(), s.cat_x)
    stop = SAM_X + SAM_WIDTH + 1
    x, i = target, 0
    while pos > stop:
        x -= 3
        pos = max(stop, pos - 2)
        height = dog_over.height(pos)
        legs = DOG_JUMP if height else DOG_WALK[i % 4]
        running = mirror(dog_sprite(legs, tail="wag", ear="up" if height >= 2 else "down"))
        squirrel = [s.squirrel(x, i, hop_out.height(x))] if x > -SQUIRREL_WIDTH else []
        layers = [squirrel, s.sam("idle"), s.sleeping_cat(), dropped]  # Nutmeg passes behind Sam
        if height == 0 and i % 2 == 0:
            layers.append((["."], pos + DOG_WIDTH - 2, FEET_ROW, DUST_COLOR))
        layers.append(s.dog(running, pos, height))
        yield s.frame(*layers)
        i += 1

    # Woof! ...where did it go?
    looking = mirror(dog_sprite(DOG_STAND, tail="wag"))
    for i in range(14):
        bark = over_dog(s, "woof!" if i < 6 else "?", pos, facing="left")
        yield s.frame(s.sam("idle"), over_sam(s, "!" if i < 4 else "?"), s.sleeping_cat(), dropped,
                      s.dog(looking, pos), bark)

    # Nobody gets the ball. Mochi opens one eye...
    for i in range(16):
        cat = [s.cat(cat_loaf("O.-"), s.cat_x), s.pile()] if 6 <= i < 11 else s.sleeping_cat()
        yield s.frame(s.sam("idle"), cat, dropped, s.dog(looking, pos))
    return None


def crow_story(s):
    """A crow swoops down and snatches the ball mid-flight, then drops it right back on the dog."""
    path = ball_path(s.width, SAM_X + SAM_RELEASE[0], SAM_RELEASE[1], s.cat_x + CAT_WIDTH)
    heights = [h for _, h in path]
    grab = heights.index(max(heights))  # the top of the throw
    grab_x, grab_h = path[grab]
    grab_row = FEET_ROW - grab_h
    start_x = s.width - 1

    def ball_layers(f):
        if f <= grab:  # swooping in from the top right
            u = f / grab
            x = round(start_x + (grab_x - CROW_BEAK - start_x) * u)
            row = round((grab_row - 1) * u)
            return [s.crow(x, row, f), s.ball(*path[f])]
        k = f - grab  # got it! flapping away up and to the right
        x, row = grab_x - CROW_BEAK + 3 * k, max(1, grab_row - 1 - k)
        return [s.crow(x, row, f), ([BALL], x + CROW_BEAK, row + 1, BALL_COLOR)]

    pos, _, f, _ = yield from throw_and_chase(s, stop_after_landing=6, ball_layers=ball_layers)

    # The dog stops and stares at the sky
    standing = standing_dog(s)
    while grab_x - CROW_BEAK + 3 * (f - grab) < s.width:
        yield s.frame(s.sam("idle"), over_sam(s, "?"), s.sleeping_cat(), ball_layers(f),
                      s.dog(standing, pos), over_dog(s, "?", pos))
        f += 1
    for _ in range(6):
        yield s.frame(s.sam("idle"), s.sleeping_cat(), s.dog(standing, pos), over_dog(s, "?", pos))

    # Pip flies back along the top, and lets go just in front of the dog's nose
    mouth_x = pos + DOG_MOUTH + 1
    x, i = s.width, 0
    while x + CROW_BEAK > mouth_x:
        x -= 3
        yield s.frame(s.sam("idle"), s.sleeping_cat(), s.crow(x, 1, i),
                      ([BALL], max(x + CROW_BEAK, mouth_x), 2, BALL_COLOR), s.dog(standing, pos))
        i += 1
    for row in range(2, FEET_ROW - 1):
        x -= 3
        yield s.frame(s.sam("idle"), s.sleeping_cat(), s.crow(x, 1, i),
                      ([BALL], mouth_x, row, BALL_COLOR), s.dog(standing, pos))
        i += 1

    yield from celebrate(s, pos, [s.sleeping_cat()])
    return "dog"


def crash_and_dash(s, dog_follows=True, ambush=False):
    """The jump falls short: the dog crashes into the cat and tumbles back seeing stars,
    the cat wakes and dashes for the ball. If dog_follows, the dog gets up and trails after it.
    Returns (dog position, cat position, where the dog has to stop)."""
    s.events.add("bonked")
    pos, height, f, path = yield from throw_and_chase(s, short_jump=True)
    cat_x = s.cat_x
    awake = [s.cat(cat_loaf("O.O"), cat_x), s.pile(), over_cat(s, "!")]

    def ball_now():
        return s.ball(*path[min(f, len(path) - 1)])

    # Bonk! The dog bounces off and lands in a heap
    s.cue("crash")
    crash = dog_sprite(DOG_JUMP, ear="up")
    for _ in range(2):
        if ambush:  # Mochi was never asleep: up she springs
            cat = [s.cat(cat_running(">.<"), cat_x - 2, 1), s.pile(), s.say("hss!", cat_x + 4, 6)]
        else:
            cat = s.sleeping_cat()
        yield s.frame(s.sam("idle"), cat, ball_now(), s.dog(crash, pos, height), s.say("*", pos + 13, height + 1))
        f += 1
    for dx, h in ((-2, 2), (-4, 1), (-6, 0)):
        yield s.frame(s.sam("idle"), awake, ball_now(), s.dog(dog_lying("@"), pos + dx, h))
        f += 1
    pos -= 6

    # The cat watches the ball land, then bolts for it while the dog sees stars
    dizzy_until = 6 if dog_follows else 10 ** 6
    stop_at = s.pile_x if s.stash else s.width  # the dog won't walk over Mochi's pile
    running = False
    over_pile = Leap(cat_running(), ball_pile(s.stash), s.pile_x) if s.stash else None
    i = 0
    while True:
        ball_x, ball_h = path[min(f, len(path) - 1)]
        if running and cat_x + CAT_RUN_WIDTH >= ball_x:
            break
        if not running and ball_x > cat_x + CAT_RUN_WIDTH + 1:
            running = True  # the ball's clear: go!
        if running:
            cat_x = min(cat_x + 2, ball_x - CAT_RUN_WIDTH)
            cat = s.cat(cat_running(">.<"), cat_x, over_pile.height(cat_x) if over_pile else 0)
        else:
            cat = awake
        if i < dizzy_until:
            dog = [s.dog(dog_lying("@"), pos), s.say("* . *" if i % 2 else ". * .", pos + 10, 5)]
        else:
            if pos + DOG_WIDTH < min(cat_x, stop_at) - 2:
                pos += 1
            dog = [s.dog(walking_dog(s, pos), pos), over_dog(s, "?", pos)]
        yield s.frame(s.sam("idle"), s.pile(), s.ball(ball_x, ball_h), cat, dog)
        f += 1
        i += 1
    return pos, ball_x - CAT_RUN_WIDTH, stop_at


def steal_story(s):
    """The dog crashes into the cat, the cat beats it to the ball,
    and then they fall asleep together as night comes."""
    pos, cat_x, stop_at = yield from crash_and_dash(s)

    # Got it! The dog plods up behind, wondering what just happened
    holding = cat_running("^.^", ball=True)
    while pos + DOG_WIDTH < min(cat_x, stop_at) - 2:
        pos += 1
        yield s.frame(s.sam("idle"), s.pile(), s.cat(holding, cat_x), s.dog(walking_dog(s, pos), pos))
    sad = dog_sprite(DOG_STAND, tail="down", eye=".")
    for i in range(14):
        layers = [s.sam("idle"), s.pile(), s.cat(holding, cat_x), s.dog(sad, pos)]
        if i < 8:
            layers.append(over_dog(s, "?", pos))
        else:
            layers.append((["<3"], cat_x + 10, FEET_ROW - 5 - (i - 8) // 2, HEART_COLOR))
        yield s.frame(*layers)

    # Night: the cat curls up around the ball, facing away from the dog
    loaf_x = cat_x + 3
    hugging = mirror(cat_loaf(ball=True))

    def sleepers():
        return [s.pile(), s.dog(dog_lying(), pos), s.cat(hugging, loaf_x),
                *snores(pos + 15, FEET_ROW - 3, s.tick + 1), *snores(loaf_x + 7, FEET_ROW - 2, s.tick + 6)]

    yield from night_falls(s, sleepers, [s.pile(), s.cat(holding, cat_x), s.dog(sad, pos)])
    for _ in range(6):
        yield s.frame(s.pile(), s.dog(dog_sprite(DOG_STAND), pos), over_dog(s, "!", pos), s.cat(hugging, loaf_x))
    return "cat"


def friends_story(s):
    """Best friends: the same crash, the same dash for the ball... but this time
    Mochi thinks it over, brings the ball back, and they spend the night together."""
    pos, cat_x, _ = yield from crash_and_dash(s, dog_follows=False)
    holding = cat_running("^.^", ball=True)
    seeing_stars = dog_lying("@")

    # Mochi has the ball... and looks back at the poor dizzy dog
    for i in range(10):
        yield s.frame(s.sam("idle"), s.pile(), s.cat(holding, cat_x), s.dog(seeing_stars, pos),
                      s.say("..." if i < 6 else "!", cat_x + 10, 5))

    # Trots all the way back, hopping the pile, and sets the ball down by the dog's nose
    carrying = mirror(holding)  # facing left now, ball held out front
    ball_spot = pos + DOG_WIDTH
    hop = Leap(carrying, ball_pile(s.stash), s.pile_x) if s.stash else None
    for x in slide(cat_x, ball_spot, 2):
        yield s.frame(s.sam("idle"), over_sam(s, "?"), s.pile(), s.cat(carrying, x, hop.height(x) if hop else 0),
                      s.dog(seeing_stars, pos))
    loaf_x = ball_spot + 1
    for i in range(6):
        yield s.frame(s.sam("idle"), s.pile(), s.ball(ball_spot), s.cat(cat_loaf("^.^"), loaf_x),
                      s.dog(dog_lying("O"), pos), s.say("!", pos + 13, 5))

    # The dog gets up, can't believe it, and takes the ball. Hearts all round.
    for i in range(18):
        heart_row = FEET_ROW - 5 - (i % 6) // 2
        layers = [s.sam("cheer" if (i // 2) % 2 else "idle"), s.pile(), s.cat(cat_loaf("^.^"), loaf_x)]
        if i < 4:
            layers += [s.ball(ball_spot), s.dog(dog_sprite(DOG_STAND, eye="O"), pos)]
        else:
            layers += [s.dog(dog_sprite(DOG_STAND, tail="wag" if i % 2 else "up", eye="^", mouth=BALL), pos),
                       (["<3"], pos + DOG_HEAD - 1, heart_row - 2, HEART_COLOR),
                       (["<3"], loaf_x + CAT_FACE, heart_row, HEART_COLOR)]
        if i >= 8:
            layers.append(over_sam(s, "aww"))
        yield s.frame(*layers)

    # Night: curled up side by side, the ball between them
    def sleepers():
        return [s.pile(), s.dog(dog_lying(), pos), s.ball(ball_spot), s.cat(cat_loaf("-w-"), loaf_x),
                *snores(pos + 15, FEET_ROW - 3, s.tick + 1), *snores(loaf_x + CAT_FACE + 2, FEET_ROW - 2, s.tick + 6)]

    yield from night_falls(s, sleepers, [s.pile(), s.cat(cat_loaf("^.^"), loaf_x),
                                         s.dog(dog_sprite(DOG_STAND, eye="^", mouth=BALL), pos)])
    for _ in range(6):
        yield s.frame(s.pile(), s.ball(ball_spot), s.cat(cat_loaf("^.^"), loaf_x),
                      s.dog(dog_sprite(DOG_STAND, tail="wag", eye="^"), pos))
    return None


def revenge_story(s):
    """The dog sneaks up on Mochi's pile of stolen balls and takes one back. The cat wakes
    and gives chase. Usually the dog gets away; sometimes (s.twist) it trips, the ball
    bounces right back to the cat, and it goes back on the pile."""
    cat_x = s.cat_x
    s.stash = max(s.stash, 1)  # there's always at least the ball Mochi stole last time
    grab_pos = s.pile_x + width_of(ball_pile(s.stash))  # facing left, the nose is the left edge

    # Tiptoe in from the right, facing left, slowing down near the pile
    pos, step = s.width, 0
    while pos > grab_pos:
        if pos - grab_pos > 12 or step % 2 == 0:
            pos -= 1
        sneaking = mirror(dog_sprite(DOG_WALK[(pos // 2) % 4], tail="down"))
        yield s.frame(s.sam("idle"), s.sleeping_cat(), s.dog(sneaking, pos))
        step += 1

    # Hold still... then take one off the top
    waiting = mirror(dog_sprite(DOG_STAND, tail="down"))
    for _ in range(5):
        yield s.frame(s.sam("idle"), s.sleeping_cat(), s.dog(waiting, pos), over_dog(s, "...", pos, facing="left"))
    s.stash -= 1
    s.events.add("took one back")
    snatched = mirror(dog_sprite(DOG_STAND, tail="down", mouth=BALL))
    for _ in range(3):
        yield s.frame(s.sam("idle"), s.sleeping_cat(), s.dog(snatched, pos - 1))

    # Turn around and creep away
    for i in range(8):
        if i % 2:
            pos += 1
        yield s.frame(s.sam("idle"), s.sleeping_cat(), s.dog(walking_dog(s, pos, mouth=BALL, tail="down"), pos))

    # The cat wakes up
    for _ in range(5):
        yield s.frame(s.sam("idle"), s.cat(cat_loaf("O.O"), cat_x), s.pile(), over_cat(s, "!"),
                      s.dog(dog_sprite(DOG_STAND, mouth=BALL), pos), over_dog(s, "!", pos))

    # Run! The cat is faster, but the dog has a head start
    over_pile = Leap(cat_running(), ball_pile(s.stash), s.pile_x) if s.stash else None
    trip_at = pos + (s.width - pos) // 3
    i = 0
    while cat_x < s.width:
        pos += 2
        cat_x = min(cat_x + 3, pos - CAT_RUN_WIDTH - 2)
        if s.twist and pos >= trip_at:
            break
        running = dog_sprite(DOG_WALK[i % 4], tail="wag", mouth=BALL, ear="up")
        laugh = over_sam(s, "ha!" if i % 4 < 2 else "ha")
        yield s.frame(s.sam("cheer" if i % 2 else "idle"), laugh, s.pile(), (["."], pos + 1, FEET_ROW, DUST_COLOR),
                      s.cat(cat_running(), cat_x, over_pile.height(cat_x) if over_pile else 0), s.dog(running, pos))
        i += 1
    else:
        for _ in range(8):
            yield s.frame(s.sam("idle"), s.pile())
        return "dog"

    # Whoops: the dog trips, and the ball bounces off its head... straight to the cat
    s.events.discard("took one back")
    cat_lift = over_pile.height(cat_x) if over_pile else 0
    catch_x = cat_x + CAT_RUN_WIDTH
    mouth = pos + DOG_MOUTH
    flight = 8
    for k in range(flight + 1):
        u = k / flight
        ball = s.ball(round(mouth + (catch_x - mouth) * u), round(2 + 6 * 4 * u * (1 - u)))
        h = (2, 1, 0)[min(k, 2)]
        yield s.frame(s.sam("idle"), over_sam(s, "eek!"), s.pile(), s.cat(cat_running(), cat_x, cat_lift),
                      s.dog(dog_lying("@"), pos + min(k, 2), h), ball)
    pos += 2
    holding = cat_running("^.^", ball=True)
    for i in range(10):
        yield s.frame(s.sam("idle"), s.pile(), s.cat(holding, cat_x, cat_lift), s.dog(dog_lying("@"), pos),
                      s.say("* . *" if i % 2 else ". * .", pos + 10, 5))

    # Back on the pile it goes
    home = s.cat_x
    hop_home = Leap(mirror(holding), ball_pile(s.stash), s.pile_x) if s.stash else None
    for x in slide(cat_x, home, 2):
        yield s.frame(s.sam("idle"), s.pile(), s.cat(mirror(holding), x, hop_home.height(x) if hop_home else 0),
                      s.dog(dog_sprite(DOG_STAND, tail="down", eye="."), pos), over_dog(s, "?", pos))
    s.stash += 1
    for _ in range(10):
        yield s.frame(s.sam("idle"), s.sleeping_cat(), s.dog(dog_sprite(DOG_STAND, tail="down", eye="."), pos))
    return "cat"


def ambush_story(s):
    """Rivals: Mochi only pretended to sleep. As the dog jumps, the cat springs up, knocks it
    out of the air, grabs the ball, and makes off with it."""
    s.events.add("ambush")
    pos, cat_x, stop_at = yield from crash_and_dash(s, ambush=True)

    # Off she goes with it, and the dog can only watch
    holding = cat_running("^.^", ball=True)
    grumpy = dog_sprite(DOG_STAND, tail="down", eye=".")
    while cat_x < s.width:
        cat_x += 3
        if pos + DOG_WIDTH < min(cat_x, stop_at) - 2:
            pos += 1
        yield s.frame(s.sam("idle"), over_sam(s, "hey!"), s.pile(), s.cat(holding, cat_x),
                      s.dog(walking_dog(s, pos), pos))
    for i in range(14):
        yield s.frame(s.sam("idle"), s.pile(), s.dog(grumpy, pos), over_dog(s, "grr" if i < 8 else "...", pos))
    return "cat"


def finale_story(s):
    """Season finale: it's Sam's birthday. Everyone turns up around the cake, they sing,
    Sam blows out the candles, and then the credits roll."""
    width = s.width
    cake_x = width // 2 - CAKE_WIDTH // 2
    sam_x = cake_x - SAM_WIDTH - 2
    dog_x = sam_x - DOG_WIDTH - 2
    cat_x = cake_x + CAKE_WIDTH + 2
    squirrel_x = cat_x + CAT_WIDTH + 2
    crow_x, crow_row = cake_x, FEET_ROW - 7
    party_cat = cat_loaf("^.^")
    text = "HAPPY BIRTHDAY, SAM!"
    s.snowman_x = squirrel_x + SQUIRREL_WIDTH + 2  # the snowman joins the end of the line
    s.tree_x = cake_x                              # and the Christmas tree stands behind the cake

    def cake(lit, step):
        flames = ("' ' '" if step % 2 else ", , ,") if lit else "~ ~ ~"
        return [(CAKE, cake_x, FEET_ROW, CAKE_COLOR), (CANDLES, cake_x + 2, FEET_ROW - 3, CANDLE_COLOR),
                ([flames], cake_x + 2, FEET_ROW - 4, FLAME_COLOR if lit else SMOKE_COLOR)]

    def banner(shown):
        x = (width - len(text)) // 2
        return [([ch], x + i, 3, TITLE_COLORS[i % len(TITLE_COLORS)]) for i, ch in enumerate(text[:shown])]

    def confetti(step):
        rng = random.Random(width)
        bits = []
        for i in range(width // 3):
            x, start = rng.randrange(width), rng.randrange(FEET_ROW)
            row = (step // 2 + start) % FEET_ROW
            bits.append((["*+.,"[i % 4]], x + (step // 3 + i) % 3 - 1, row, FLOWER_COLORS[i % len(FLOWER_COLORS)]))
        return bits

    # Everyone turns up: the dog from the left, the cat and the squirrel from the right, Pip from the sky
    steps = 24
    for i in range(steps + 1):
        u = i / steps
        dog_now = round(-DOG_WIDTH + (dog_x + DOG_WIDTH) * u)
        early = min(1.0, i / (steps - 6))  # Mochi gets there first and settles down
        cat_now = round(width + (cat_x - width) * early)
        late = max(0.0, (i - 8) / (steps - 8))
        squirrel_now = round(width + (squirrel_x - width) * late)
        layers = [cake(True, i), s.sam("idle", sam_x), s.dog(walking_dog(s, dog_now), dog_now),
                  s.cat(mirror(cat_running("^.^")) if early < 1 else party_cat, cat_now)]
        if i >= 8:
            layers.append(s.squirrel(squirrel_now, i))
        layers.append(s.crow(round(width + (crow_x - width) * u), round(crow_row * u), i))
        yield s.frame(*layers)

    def party(lit, step, extra=(), hop=0, sam_pose="idle"):
        dog = dog_sprite(DOG_JUMP if hop else DOG_STAND, tail="wag", eye="^", ear="up" if hop > 1 else "down")
        return [cake(lit, step), s.sam(sam_pose, sam_x), s.dog(dog, dog_x, hop), s.cat(party_cat, cat_x, hop // 2),
                s.squirrel(squirrel_x, step // 2, hop), s.crow(crow_x, crow_row, step), *extra]

    # The banner goes up and everyone sings
    for i in range(36):
        singing = [] if i < 10 else [s.say("la", x, h + (i // 3) % 2) for x, h in
                                      ((dog_x + DOG_HEAD - 1, 7), (cat_x + 3, 4), (squirrel_x + 2, 4))]
        yield s.frame(party(True, i, [banner(i * 2), *singing]))

    # Make a wish... and blow
    for i in range(10):
        words = "make a wish..." if i < 6 else "whoooo"
        yield s.frame(party(True, i, [banner(len(text)), s.say(words, sam_x, 9)]))  # just over Sam's head
    for i in range(4):
        yield s.frame(party(False, i, [banner(len(text))]))

    # Hooray!
    for i in range(28):
        hop = (0, 1, 2, 1)[i % 4]
        hearts = [(["<3"], x, FEET_ROW - 9 - (i % 6) // 2, HEART_COLOR) for x in (dog_x + 8, cat_x + 4)]
        yield s.frame(*confetti(i), party(False, i, [banner(len(text)), *hearts], hop=hop,
                                          sam_pose="cheer" if (i // 2) % 2 else "idle"))

    # Night falls on the last day of the year: fireworks!
    s.weather = "sunny"  # the snow stops
    s.sky.update(sun=None, birds=False, night=True, moon=True, stars=len(star_field(width)))
    yield from fireworks(s, party(False, 0))
    yield from credits(s)
    s.sky.update(new_sky())
    return None


def fireworks(s, scene_layers, length=56):
    """Rockets go up and burst over a HAPPY NEW YEAR! banner."""
    text = "HAPPY NEW YEAR!"
    banner_x = (s.width - len(text)) // 2
    rng = random.Random(s.width + 11)
    rockets = [(rng.randrange(0, length - 14), rng.randrange(6, s.width - 6), rng.randrange(1, 5),
                TITLE_COLORS[i % len(TITLE_COLORS)]) for i in range(max(6, s.width // 10))]
    for t in range(length):
        layers = []  # fireworks first, so they go up behind the party, not through it
        for launch, x, burst_row, color in rockets:
            age = t - launch
            rise = FEET_ROW - 6 - burst_row
            if 0 <= age < rise:  # going up
                layers.append((["|"], x, FEET_ROW - 6 - age, color))
            elif rise <= age < rise + 5:  # BANG
                r = age - rise + 1
                if r == 1:
                    s.cue("firework")
                for angle in range(0, 360, 45):
                    dx = round(2 * r * math.cos(math.radians(angle)))
                    dy = round(r * math.sin(math.radians(angle)))
                    layers.append((["*" if r < 4 else "."], x + dx, burst_row + dy, color))
        layers += list(scene_layers)
        if t >= 10:
            layers += [([ch], banner_x + i, 3, TITLE_COLORS[i % len(TITLE_COLORS)]) for i, ch in enumerate(text)]
        yield s.frame(*layers)


def credits(s):
    """The end-of-year credits, rolling up the screen."""
    w = s.world

    def billing(card, role=None):
        return f"{card[0]:<10}{(role or card[1]):>18}"

    pile = f"{w.stash} ball" + ("" if w.stash == 1 else "s")
    status = {3: "best friends", 2: "friends", 1: "getting along", 0: "frenemies", -1: "rivals"}.get(
        w.friendship, "sworn rivals")
    lines = [
        ("F E T C H !", CARD_COLOR), ("", None), ("starring", TEXT_COLOR), ("", None),
        (billing(DOG_CARD), TEXT_COLOR), (billing(CAT_CARD), TEXT_COLOR), (billing(THROWER_CARD), TEXT_COLOR),
        (billing(SQUIRREL_CARD), TEXT_COLOR), (billing(CROW_CARD), TEXT_COLOR),
        (billing(BALL_CARD, "itself"), TEXT_COLOR),
        ("", None), ("and introducing", TEXT_COLOR), ("", None),
        (f"the snowman, knocked over {w.snowmen_knocked} times", TEXT_COLOR),
        (f"{CAT_NAME}'s pile: {pile}", TEXT_COLOR),
        ("", None),
        (f"score so far: {DOG_NAME} {w.score['dog']}, {CAT_NAME} {w.score['cat']}", TEXT_COLOR),
        (f"{DOG_NAME} and {CAT_NAME}: {status}", TEXT_COLOR),
        ("", None), ("", None),
        ("thanks for watching!", CARD_COLOR),
    ]
    for step in range(2 * (FEET_ROW + len(lines)) - 10):
        rows = []
        for i, (text, color) in enumerate(lines):
            row = FEET_ROW + i - step // 2
            if text and 0 <= row < FEET_ROW:
                rows.append(([text], (s.width - len(text)) // 2, row, color))
        yield s.frame(*rows)


def egghunt_story(s):
    """Easter: Sam has hidden eggs all over the yard, and Biscuit sniffs them out one by one.
    The last one is hidden under Mochi."""
    rng = random.Random(s.width + 5)
    leap = Leap(dog_sprite(DOG_JUMP), s.obstacle(), s.cat_x)
    no_go = range(s.cat_x - 6, leap.end + DOG_MOUTH + 4)  # not by the cat, nor anywhere the dog is mid-jump
    spots = [x for x in range(DOG_START + DOG_MOUTH + 3, s.width - 4, 9) if x not in no_go and x + 2 not in no_go]
    s.eggs = sorted(x + rng.randrange(0, 3) for x in spots)
    hidden = s.cat_x + 4  # the sneaky one, under the cat
    total = len(s.eggs) + 1

    def counter():
        return ([f"eggs: {len(s.found_eggs)}/{total}"], SAM_X + SAM_WIDTH + 3, 3, CARD_COLOR)  # below the clouds

    pos = DOG_START
    for i in range(10):
        yield s.frame(s.sam("cheer" if i < 6 else "idle"), over_sam(s, "find the eggs!"), s.sleeping_cat(),
                      s.dog(standing_dog(s, i), pos), counter())

    under_cat_done = False
    while pos + DOG_MOUTH < s.width - 2:
        # Sniffing along: is the nose right over an egg?
        nose = pos + DOG_MOUTH
        egg = next((x for x in s.eggs if x not in s.found_eggs and nose - 8 <= x <= nose + 1), None)
        clear_of_cat = not clearance(dog_crouch(), s.obstacle(), pos - s.cat_x)
        if egg is not None and clear_of_cat:
            for k in range(8):
                sniffing = dog_crouch(tail="wag", eye=s.dog_eye())
                found = k >= 5
                if found:
                    s.found_eggs.add(egg)
                yield s.frame(s.sam("idle"), s.sleeping_cat(), s.dog(sniffing, pos), counter(),
                              s.say("!" if found else "sniff", nose - 2, 5))
            continue

        # The one under Mochi: a sniff, an indignant cat, and there it is
        if not under_cat_done and nose >= s.cat_x - 4:
            for k in range(6):
                yield s.frame(s.sam("idle"), s.sleeping_cat(), s.dog(standing_dog(s, k), pos), counter(),
                              s.say("sniff?", nose - 3, 7))
            for k in range(8):
                if k == 5:
                    s.found_eggs.add(hidden)
                egg_layer = [] if k >= 5 else [(EGG, hidden, FEET_ROW, EGG_COLORS[0])]
                yield s.frame(s.sam("idle"), egg_layer, s.cat(cat_loaf("O.O"), s.cat_x, 3), s.pile(),
                              s.say("hmph!", s.cat_x + 2, 7) if k < 5 else [],
                              s.dog(standing_dog(s, k), pos), counter(), over_dog(s, "!" if k >= 5 else "", pos))
            under_cat_done = True
            s.events.add("egg under the cat")
            continue

        sprite = walking_dog(s, pos) if pos % 3 else dog_crouch(tail="wag", eye=s.dog_eye())  # nose to the ground
        height = max(leap.height(pos), clearance(sprite, s.obstacle(), pos - s.cat_x))
        if height:
            sprite = dog_sprite(DOG_JUMP, tail="wag", eye=s.dog_eye(), ear="up" if height >= 2 else "down")
        yield s.frame(s.sam("idle"), s.sleeping_cat("=.=" if under_cat_done else None), s.dog(sprite, pos, height),
                      counter())
        pos += 1

    # All found!
    for i in range(18):
        hop = (0, 1, 2, 1)[i % 4]
        happy = dog_sprite(DOG_JUMP if hop else DOG_STAND, tail="wag", eye="^", ear="up" if hop > 1 else "down")
        yield s.frame(s.sam("cheer" if (i // 2) % 2 else "idle"), s.sleeping_cat("=.="), s.dog(happy, pos, hop),
                      counter(), (["all found!"], (s.width - 10) // 2, 2, CARD_COLOR))
    return None


def valentine_story(s):
    """Valentine's Day: one ball, two sweethearts. Sam's throw lands right in front of Mochi, the dog
    and the cat grab it at the same moment, and after a tug of war Sam makes them share."""
    ball_x = s.cat_x  # right at Mochi's nose
    meet = ball_x - DOG_MOUTH  # where the dog stands to hold the other side of it
    pos = DOG_START
    start_x, start_h = SAM_X + SAM_RELEASE[0], SAM_RELEASE[1]

    for i, pose in enumerate(["idle"] * 2 + ["windup"] * 3):
        hand = SAM_HAND if pose == "idle" else SAM_WINDUP
        yield s.frame(s.sam(pose), s.sleeping_cat("-w-"), s.ball(SAM_X + hand[0], hand[1]), s.dog(standing_dog(s, i), pos))

    # A gentle lob that lands right by the cat's nose, while the dog trots over
    flight = max(6, (ball_x - start_x) // 2)
    for k in range(1, flight + 1):
        u = k / flight
        bx = round(start_x + (ball_x - start_x) * u)
        bh = round(start_h * (1 - u) + 4 * 4 * u * (1 - u))
        pos = min(meet, pos + 1)
        yield s.frame(s.sam("throw" if k < 3 else "idle"), s.sleeping_cat("-w-"), s.ball(bx, bh),
                      s.dog(walking_dog(s, pos) if pos < meet else standing_dog(s, k), pos))
    while pos < meet:
        pos += 1
        yield s.frame(s.sam("idle"), s.sleeping_cat("O.-"), s.ball(ball_x), s.dog(walking_dog(s, pos), pos))

    # Both grab it at once. Tug of war!
    for i in range(18):
        shift = (0, 1, 0, -1)[i % 4]
        layers = [s.sam("idle" if i < 10 else "cheer"), s.cat(cat_loaf(">.<"), s.cat_x + shift + 1), s.pile(),
                  s.dog(dog_sprite(DOG_STAND, tail="down", eye=".", mouth=BALL), pos + shift)]
        layers.append(over_dog(s, "grr", pos + shift) if i % 4 < 2 else over_cat(s, "hss"))
        if i >= 10:
            layers.append(over_sam(s, "SHARE!"))
        yield s.frame(*layers)

    # ...fine. They lie down face to face, the ball between them.
    for i in range(30):
        layers = [s.sam("idle" if i < 20 else "cheer"), s.dog(dog_lying("^"), meet - 1), s.ball(ball_x),
                  s.cat(cat_loaf("^.^"), ball_x + 1), s.pile()]
        if i >= 6:
            layers.append((["<3"], ball_x - 1, FEET_ROW - 3 - (i % 8) // 2, HEART_COLOR))
        if i >= 20:
            layers.append(over_sam(s, "aww"))
        yield s.frame(*layers)
    return None


STORIES = {
    "fetch": fetch_story,
    "squirrel": squirrel_story,
    "crow": crow_story,
    "steal": steal_story,
    "friends": friends_story,
    "ambush": ambush_story,
    "egghunt": egghunt_story,
    "valentine": valentine_story,
    "finale": finale_story,
    "revenge": revenge_story,
}
