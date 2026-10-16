"""What the show remembers from one episode to the next: the score, the running
gags that carry over (Sam's bandage and boots, Mochi's pile of stolen balls, the
snowman that gets rebuilt a little worse every time), everyone's mood, and how
Biscuit and Mochi feel about each other.

It's saved to a small file after every episode, so the next run picks up where
this one left off, like a real ongoing series."""

import json
import os
from pathlib import Path

from .config import BEST_FRIENDS

SAVE_FILE = Path(__file__).resolve().parent.parent / "fetch_save.json"

# How each kind of episode moves the friendship meter
FRIENDSHIP_CHANGE = {
    "steal": +1,     # it ends with them napping side by side
    "revenge": -1,   # being robbed stings (and twice as much if the cat wins it back)
    "crow": +1,      # a shared adventure
    "squirrel": +1,  # likewise
    "ambush": +1,    # Mochi got even; that takes the edge off
    "finale": +1,    # everyone loves a birthday party
    "valentine": +2, # made to share, and found they didn't mind
}


class World:
    def __init__(self):
        self.score = {"dog": 0, "cat": 0}
        self.stash = 0             # balls Mochi has won and keeps in a pile
        self.bandage = 0           # episodes Sam still wears a bandage after tripping
        self.boots = False         # after one slip, Sam always wears rain boots
        self.snowman_damage = 0    # 0 is a proper snowman; 3 is just a lump of snow
        self.dog_mood = "fine"     # happy, fine or grumpy
        self.cat_mood = "sleepy"   # smug, sleepy or annoyed
        self.friendship = 0        # from -3 (sworn rivals) to 3 (best friends)
        self.season = None
        self.last_kind = None
        self.episodes = 0          # how many episodes have aired so far
        self.snowmen_knocked = 0   # for the end-of-year credits

    # --- Saving and loading ----------------------------------------------------------

    def to_json(self):
        return json.dumps(vars(self), indent=2)

    @classmethod
    def from_json(cls, text):
        """The memory saved in `text`, or a fresh one if it can't be read."""
        world = cls()
        try:
            saved = json.loads(text)
        except (TypeError, ValueError):
            return world
        if isinstance(saved, dict):
            for key, value in saved.items():
                if hasattr(world, key):  # ignore anything a newer or older version left behind
                    setattr(world, key, value)
        return world

    def save(self, path=SAVE_FILE):
        """Write the memory to disk. Written to a temporary file first and then swapped in,
        so quitting halfway through a save can't leave a broken file behind."""
        temp = Path(str(path) + ".tmp")
        temp.write_text(self.to_json())
        os.replace(temp, path)

    @classmethod
    def load(cls, path=SAVE_FILE):
        """The saved memory, or a fresh one if there's no save (or it can't be read)."""
        try:
            return cls.from_json(Path(path).read_text())
        except OSError:
            return cls()

    def start(self, episode):
        """Get ready for a new episode."""
        if episode.season != self.season and episode.season == "winter":
            self.snowman_damage = 0  # a fresh snowman every winter
        self.season = episode.season

    def remember(self, episode, winner, events):
        """Update the memory after an episode, from who won and what happened."""
        if winner:
            self.score[winner] += 1
        if episode.kind in ("steal", "ambush"):
            self.stash += 1          # the stolen ball goes on the pile
        if "took one back" in events:
            self.stash = max(0, self.stash - 1)  # the dog got one back from the pile

        self.bandage = 3 if "tripped" in events else max(0, self.bandage - 1)
        if "slipped" in events:
            self.boots = True
        if "snowman" in events:
            self.snowman_damage = min(3, self.snowman_damage + 1)
            self.snowmen_knocked += 1

        # Moods: winning feels good, losing stings, and being woken up is annoying
        self.dog_mood = {"dog": "happy", "cat": "grumpy"}.get(winner, "fine")
        if winner == "cat":
            self.cat_mood = "smug"
        elif episode.kind == "revenge" or "tripped" in events:
            self.cat_mood = "annoyed"
        else:
            self.cat_mood = "sleepy"  # moods fade after a quiet episode

        # Friendship
        if episode.kind == "friends":
            self.friendship = 0          # a lovely moment; then back to being a cat and a dog
            self.dog_mood, self.cat_mood = "happy", "sleepy"
        else:
            change = FRIENDSHIP_CHANGE.get(episode.kind, 0)
            if episode.kind == "revenge" and winner == "cat":
                change = -2
            if "tripped" in events:
                change -= 1  # Sam fell over Mochi, and Mochi blames the dog
            if episode.kind in ("finale", "valentine", "egghunt"):
                self.dog_mood, self.cat_mood = "happy", "sleepy"
            self.friendship = max(-BEST_FRIENDS, min(BEST_FRIENDS, self.friendship + change))
        self.last_kind = episode.kind
        self.episodes = episode.number
