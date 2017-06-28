import uninhibited
import itertools
import random

from faker import Factory
fake = Factory.create()


def iter_event_names():
    while True:
        name = fake.name()
        yield name
        yield name.replace(' ', '_')


def test_add_events():
    event_names = list(itertools.islice(iter_event_names(), random.randint(10, 20)))
    d = uninhibited.Dispatch()

    d.add_events(event_names)

    ret = set(event_names) - set(d.events)
    return not ret


def test_given_event_names_are_added():
    event_names = set(itertools.islice(iter_event_names(), random.randint(10, 20)))
    d = uninhibited.Dispatch(event_names)

    ret = set(event_names) - set(d.events)
    return not ret
