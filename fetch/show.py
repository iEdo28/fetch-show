"""The whole broadcast as one stream of frames: the opening titles, a recap when
picking up from a save, then episode after episode, forever.

The terminal (walking_dog.py) and the web page both just play this stream."""

import itertools

from .episodes import end_card, episode_card, plan_episode, previously_card
from .world import World
from .intro import intro
from .stage import Scene, new_sky


def broadcast(world, width, with_intro=True, saved=None):
    """Yield frames (lists of colored text lines) forever.

    world:       what the show remembers; a fresh World() to start the series over
    width():     the current screen width in columns, checked before each episode
    saved(world): called after every episode, to keep the memory somewhere
    """
    ticks = itertools.count()  # one shared clock, so clouds and birds keep drifting between scenes
    sky = new_sky()
    if with_intro:
        yield from intro(Scene(width(), ticks, sky))
    if world.episodes:
        yield from previously_card(Scene(width(), ticks, sky), world)

    for number in itertools.count(world.episodes + 1):
        episode = plan_episode(number, world)
        world.start(episode)
        columns = width()

        def scene():
            return Scene(columns, ticks, sky, episode.weather, episode.season, slip=episode.slip,
                         trip=episode.trip, twist=episode.twist, world=world, storm=episode.storm,
                         holiday=episode.holiday)

        yield from episode_card(scene(), episode)
        stage = scene()
        winner = yield from episode.story(stage)
        world.remember(episode, winner, stage.events)
        if saved:
            saved(world)
        yield from end_card(scene(), episode, world)


def directors_cut(world, width, episode):
    """Play one hand-picked episode, with its cards. Works on a copy of the memory,
    so the saved series isn't changed."""
    world = World.from_json(world.to_json())
    episode.world = world
    world.start(episode)
    ticks = itertools.count()
    sky = new_sky()

    def scene():
        return Scene(width(), ticks, sky, episode.weather, episode.season, slip=episode.slip,
                     trip=episode.trip, twist=episode.twist, world=world, storm=episode.storm,
                     holiday=episode.holiday)

    yield from episode_card(scene(), episode)
    stage = scene()
    winner = yield from episode.story(stage)
    world.remember(episode, winner, stage.events)
    yield from end_card(scene(), episode, world)
