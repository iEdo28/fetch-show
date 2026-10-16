"""Numbers that shape the show: screen layout, timing, colors, and how often things happen."""

# Screen layout. Rows count down from the top of the scene.
ROWS = 15            # 3 rows of sky, room to leap, the characters, and the ground
FEET_ROW = ROWS - 2  # the row everyone stands on
GROUND_ROW = ROWS - 1
SKY = 3
SUN_ROW = 2
SAM_X = 1            # where Sam stands
DOG_START = 12       # where Biscuit waits for the throw
THROW_PEAK = 8       # how high Sam throws the ball
MIN_WIDTH = 80       # narrowest terminal the show is laid out for
DELAY = 0.12         # seconds per frame

# The cast: (name, role, loves)
DOG_CARD = ("BISCUIT", "the dog", "the red ball")
CAT_CARD = ("MOCHI", "the cat", "naps and stealing")
THROWER_CARD = ("SAM", "the thrower", "throwing things")
SQUIRREL_CARD = ("NUTMEG", "the squirrel", "acorns and mischief")
CROW_CARD = ("PIP", "the crow", "shiny red things")
BALL_CARD = ("THE BALL", "the ball", "being chased")

# Colors (256-color terminal palette)
DOG_COLOR = 179
BALL_COLOR = 196
HEART_COLOR = 205
PERSON_COLOR = 33
UMBRELLA_COLOR = 135
CAT_COLOR = 208
SQUIRREL_COLOR = 130
CROW_COLOR = 61
SNORE_COLOR = 117
ALERT_COLOR = 226
DUST_COLOR = 137
GRASS_DAY = 34
GRASS_NIGHT = 22
SNOW_GROUND = 255
FOOTPRINT_COLOR = 244
SUN_COLORS = [220, 214, 208, 202, 196]  # midday through to sunset
MOON_COLOR = 229
STAR_COLOR = 230
CLOUD_COLORS = {"sunny": 252, "leaves": 252, "rain": 244, "snow": 250}
CLOUD_NIGHT = 240
BIRD_COLOR = 244
RAIN_COLOR = 75
SNOW_COLOR = 255
PUDDLE_COLOR = 39
FLOWER_COLORS = [205, 220, 135, 196, 213]
EGG_COLORS = [219, 159, 229, 157, 183]
LEAF_COLORS = [166, 172, 130, 178, 136]
PUMPKIN_COLOR = 208
STEM_COLOR = 34
SNOWMAN_COLOR = 255
HAT_COLOR = 240
NOSE_COLOR = 94
SCARF_COLOR = 160
BEANIE_COLOR = 160
FLOWER_HAT_COLOR = 205
BANDAGE_COLOR = 223
BOOTS_COLOR = 220
TITLE_COLORS = [196, 208, 220, 34, 33, 135]
CAKE_COLOR = 218
BOLT_COLOR = 228
SAND_COLOR = 222
SEA_COLOR = 32
PARASOL_COLOR = 203
CASTLE_COLOR = 180
SKY_HEART_COLOR = 211
FLASH_COLOR = 231
THUNDER_COLOR = 250
STORM_CLOUD_COLOR = 238
WITCH_HAT_COLOR = 93
BAT_COLOR = 241
GLOW_COLORS = [208, 214, 202]          # a jack-o'-lantern's candle flickering
TREE_COLOR = 28
TRUNK_COLOR = 94
TREE_LIGHT_COLORS = [196, 226, 46, 51, 201, 208]
PRESENT_COLORS = [160, 33, 135]
SANTA_COLOR = 160
ANTLER_COLOR = 94
CANDLE_COLOR = 255
FLAME_COLOR = 214
SMOKE_COLOR = 245
TEXT_COLOR = 245
CARD_COLOR = 202  # "STARRING", names, episode titles

# Seasons. Each season lasts one full story (three episodes).
SEASONS = ["spring", "summer", "autumn", "winter"]
SEASON_GROUND = {"spring": 34, "summer": 70, "autumn": 136, "winter": SNOW_GROUND}
SEASON_COLORS = {"spring": 205, "summer": 220, "autumn": 166, "winter": 117}
SEASON_WEATHER = {  # the odds of each kind of weather in each season
    "spring": {"sunny": 3, "rain": 2},
    "summer": {"sunny": 4, "rain": 1},
    "autumn": {"leaves": 3, "rain": 2},
    "winter": {"snow": 1},
}
WEATHER_WORDS = {"sunny": "sunny", "rain": "rainy", "snow": "snowy", "leaves": "windy"}

# How often things happen
SLIP_CHANCE = 0.6    # on a rainy day, how often Sam slips in the puddle
STORM_CHANCE = 0.35  # how often a rainy day turns into a thunderstorm
TRIP_CHANCE = 0.5    # after a plain fetch, how often Sam trips over the cat
REVENGE_TRIP_CHANCE = 0.4  # how often the dog trips in its getaway and the cat wins the ball back
BEST_FRIENDS = 3     # friendship needed for Mochi to bring the ball back (the meter runs -3 to 3)
RIVALS = -2          # at or below this, Mochi only pretends to sleep, and ambushes
YEAR = 13            # episodes a year: four seasons of three, then the season finale
OPENER_ODDS = {"fetch": 2, "squirrel": 1, "crow": 1}  # the first episode of each season
