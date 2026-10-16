"""Every drawing in the show. Each sprite is a list of text rows, top to bottom.
Spaces are see-through, so whatever is behind shows through them.

Drawings that change (a face, a tail, a hat) are built by small functions, so
moods, outfits and running gags can swap parts without redrawing the whole thing."""

MIRROR = str.maketrans("()/\\<>[]{}", ")(\\/><][}{")


def mirror(sprite):
    """Flip a sprite to face the other way."""
    width = max(len(line) for line in sprite)
    return [line.ljust(width)[::-1].translate(MIRROR) for line in sprite]


BALL = "O"


def width_of(sprite):
    return max(len(line) for line in sprite)


def merge(back, front, dx):
    """One sprite made of two, with `front` drawn dx columns right of `back`, bottoms lined up."""
    height = max(len(back), len(front))
    back = [""] * (height - len(back)) + back
    front = [""] * (height - len(front)) + front
    rows = []
    for b, f in zip(back, front):
        row = list(b.ljust(max(len(b), dx + len(f))))
        for j, ch in enumerate(f):
            if ch != " ":
                row[dx + j] = ch
        rows.append("".join(row))
    return rows


# --- Biscuit, the dog (faces right; mirror() to face left) -----------------------------

DOG_WALK = [  # (legs, paws): back, under, forward, under
    ("| |____| |", "|_|    |_|"),
    ("\\ \\____\\ \\", " \\_\\    \\_\\"),
    ("| |____| |", "|_|    |_|"),
    ("/ /____/ /", "/_/    /_/"),
]
DOG_STAND = DOG_WALK[0]
DOG_JUMP = ("\\ \\____/ /", " \\_\\  /_/")  # back legs kicked back, front legs reaching
DOG_TAILS = {  # (top of tail, bottom of tail, rump)
    "up": ("\\\\", "\\\\", "  ("),
    "wag": ("//", "//", "  ("),
    "down": ("  ", "  ", " _("),
}
DOG_EARS = {  # a long floppy ear hanging from the top of the head; lifted a little when jumping
    "down": ("|", "( |", "\\_|"),
    "up": ("|", "(_|", "  \\"),
}


def dog_sprite(legs=DOG_STAND, tail="up", eye="'", ear="down", mouth=" "):
    top, bottom, rump = DOG_TAILS[tail]
    ear_top, ear_mid, ear_low = DOG_EARS[ear]
    upper, paws = legs
    return [
        "            ____",
        " " + top + "      __/" + ear_top + " " + eye + " \\__",
        "  " + bottom + "____/ " + ear_mid + "     @",
        rump + "       " + ear_low + ",___/" + mouth,
        "   " + upper,
        "   " + paws,
    ]


def dog_crouch(**looks):
    """Haunches folded: ready to spring, or squashed by a landing."""
    return dog_sprite(**looks)[:4] + ["   (_/____\\_)"]


def dog_lying(eye="-"):
    return [
        "            ____",
        "  _      __/| " + eye + " \\__",
        " ( \\____/ ( |     @",
        "  \\_______\\_|,___/",
    ]


DOG_WIDTH = 19
DOG_HEIGHT = 6
DOG_MOUTH = 18   # column where a held ball sits, two rows above the paws
DOG_NOSE = 18    # column of the nose, three rows above the paws
DOG_HEAD = 14    # column above the middle of the head, for "!" and "?"
DOG_SCARF = 13   # column under the chin, two rows above the paws (where a scarf goes)
FOOT_CHARS = "\\/|"

# --- Sam, the thrower ------------------------------------------------------------------
# About one and a half times Biscuit's height. {hat} is the top of the head, {face}
# the face, {neck} the spot for a scarf, {feet} the shoes (or rain boots).

SAM_POSES = {
    "idle":    ["   {hat}", "  ({face})", " .-'{neck}'-.", " | |  | |", " | |  | |", " ' |__| '", "   |  |", "   |  |", "  {feet}"],
    "step":    ["   {hat}", "  ({face})", " .-'{neck}'-.", " | |  | |", " | |  | |", " ' |__| '", "   |  \\", "   |   \\", "  _|    \\_"],
    "windup":  ["\\  {hat}", " \\({face})", "  ''{neck}'-.", "   |  | |", "   |  | |", "   |__| '", "   |  |", "   |  |", "  {feet}"],
    "throw":   ["   {hat}    /", "  ({face})  /", " .-'{neck}'-'", " | |  |", " | |  |", " ' |__|", "   |  |", "   |  |", "  {feet}"],
    "cheer":   ["\\  {hat}  /", " \\({face})/", "  '-{neck}-'", "   |  |", "   |  |", "   |__|", "   |  |", "   |  |", "  {feet}"],
    "slip":    ["\\  {hat}  /", " \\(O_O)/", "  '-{neck}-'", "   |  |", "   |  |", "   |__|", "    \\  \\", "     \\  \\", "      \\_\\_"],
    "sitting": ["   {hat}", "  (>_<)", " .-'{neck}'-.", " | |  | |", " ' |__| '", "   |__|_____"],
    "fallen":  ["          {hat}", " _/\\_____(x_x)"],
}
SAM_WIDTH = 9
SAM_HEIGHT = 9
SAM_HAND = (9, 3)      # where a ball sits in Sam's hand, standing
SAM_WINDUP = (-1, 9)   # ...held back over the head
SAM_RELEASE = (11, 9)  # ...and where it leaves the hand


def sam_sprite(pose="idle", face="^_^", hat="___", neck="  ", boots=False):
    feet = "[|  |]" if boots else "_|  |_"
    return [row.format(hat=hat, face=face, neck=neck, feet=feet) for row in SAM_POSES[pose]]


UMBRELLA = ["  _.-^-._", " /_______\\", "     |"]

# --- Mochi, the cat ----------------------------------------------------------------------
# Asleep, Mochi is a loaf facing left. Running, Mochi faces right.

WITCH_HAT = ["  /\\", " /__\\"]


def cat_loaf(face="-.-", ball=False, spiky=False):
    """Mochi asleep in a loaf. spiky: fur standing on end after a thunderclap."""
    return [
        "  /\\_/\\/\\/\\" if spiky else "  /\\_/\\___",
        (BALL if ball else " ") + "( " + face + " )  \\~",
        " (__(__)__)",
    ]


def cat_running(face=">.<", ball=False):
    return [
        "  _      /\\_/\\",
        " ( \\____( " + face + " )" + (BALL if ball else ""),
        "  \\        __/",
        "  /_/\\_\\ /_/",
    ]


CAT_WIDTH = 12        # the sleeping loaf
CAT_FACE = 3          # column of the middle of the loaf's face
CAT_RUN_WIDTH = 15    # running, not counting a held ball
CAT_RUN_FACE = 11

# --- Nutmeg, the squirrel (faces left; mirror() to face right) ---------------------------

SQUIRREL_FRAMES = [
    ["    ,~~.", " _ (    )", "<'\\_)__/"],
    ["    .~~,", " _ (    )", "<'\\_)__/"],  # tail flick
]
SQUIRREL_WIDTH = 9

# --- Pip, the crow. A carried ball hangs under the "v". -----------------------------------

CROW_FRAMES = [["\\__   __/", "   \\v/"], ["", "_.-\\v/-._"]]  # wings up, wings down
CROW_BEAK = 4

# --- Mochi's growing pile of stolen balls -------------------------------------------------


def ball_pile(count):
    """Stolen balls stacked up: four on the bottom row, then three, then two, then one."""
    rows, left = [], count
    for size in (4, 3, 2, 1):
        if left <= 0:
            break
        take = min(size, left)
        rows.append(" " * (4 - size) + " ".join(BALL * take))
        left -= take
    return list(reversed(rows)) or [""]


# --- Sky ----------------------------------------------------------------------------------

SUN_FRAMES = [
    ["\\ | /", "- O -", "/ | \\"],
    ["  |  ", "- O -", "  |  "],
]
MOON = ["   _..._", "  /  .-'", " |  (", "  \\  '-.", "   '---'"]  # a crescent, top right at night
MOON_WIDTH = 9
BOLT = ["  _/", " /", " \\_", "   /", "  /"]
BAT_FRAMES = ["/^v^\\", "\\^v^/"]
BIRD_FRAMES = ["\\v/", "-v-"]
FLOCK = [(0, 1), (5, 0), (9, 1)]  # (column offset, row) of each bird in the flock
CLOUDS = [
    ([" .--.", "(____)"], 0.1),
    ([" .-.", "(___)"], 0.5),
]
STORM_CLOUDS = [
    ([" .--.", "(____)"], 0.3),
    ([" .---.", "(_____)"], 0.75),
]

# --- Seasonal props -----------------------------------------------------------------------

EGG = [" _", "(_)"]
TREE = ["    *", "   /.\\", "  /*.*\\", " /.*.*.\\", "/_______\\", "   |_|"]
TREE_WIDTH = 9
PRESENTS = ["[#] [=]"]
ANTLERS = ["Y  Y"]   # over Biscuit's head at Christmas
SANDCASTLE = ["   |>", "  _|_", " [_|_]", "[_____]"]   # the beach day's answer to the snowman
SANDCASTLE_FALLEN = ["._[___]_."]
PARASOL = [" _.-^-._", "/_/_\\_\\_\\", "    |", "    |"]
PARASOL_WIDTH = 9
SEA_WAVES = "~^~^~-"
PUMPKIN = [" ((^w^))"]
PUMPKIN_STEM = ["\\"]
PUMPKIN_WIDTH = 8


def snowman(damage=0):
    """The snowman, rebuilt a little worse each time it gets knocked over:
    0 has a hat and a carrot nose, 1 lost the hat, 2 lost the nose too, 3 is just a lump."""
    head = {0: " (^>^)", 1: " (^>^)", 2: " (^ ^)"}.get(damage)
    body = ["(  :  )", "(__:__)"]
    return ([head] if head else []) + body


def snowman_tilted(damage=0):
    head = {0: "   (^>^)", 1: "   (^>^)", 2: "   (^ ^)"}.get(damage)
    return ([head] if head else []) + [" (  :  )", "(__:__)"]


def snowman_fallen(damage=0):
    head = {0: "(^>^)", 1: "(^>^)", 2: "(^ ^)"}.get(damage, "")
    return ["(__:__)" + head]


SNOWMAN_HAT = ["_|_"]
SNOWMAN_WIDTH = 7

# --- The season finale ----------------------------------------------------------------

CAKE = [" _______", "|~~~~~~~|", "|_______|"]
CANDLES = ["| | |"]        # stand on the cake, two columns in
CAKE_WIDTH = 9

# --- Little effects -----------------------------------------------------------------------

LANDING_DUST = [(".:", ":."), (".", "."), (".", ".")]

# --- Title lettering ----------------------------------------------------------------------

TITLE = "FETCH!"
TITLE_FONT = {
    "F": [r" _____ ", r"|  ___|", r"| |_   ", r"|  _|  ", r"|_|    "],
    "E": [r" _____ ", r"| ____|", r"|  _|  ", r"| |___ ", r"|_____|"],
    "T": [r" _____ ", r"|_   _|", r"  | |  ", r"  | |  ", r"  |_|  "],
    "C": [r"  ____ ", r" / ___|", r"| |    ", r"| |___ ", r" \____|"],
    "H": [r" _   _ ", r"| | | |", r"| |_| |", r"|  _  |", r"|_| |_|"],
    "!": [r" _ ", r"| |", r"| |", r"|_|", r"(_)"],
}
SUBTITLE = "a dog, a cat, and one red ball"
