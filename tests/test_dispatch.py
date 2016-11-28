import uninhibited
import six

EVENT_NAMES = ['one', 'two', 'three']


def test_add_events():
    d = uninhibited.Dispatch()
    d.add_events(EVENT_NAMES)
    assert list(six.keys(d.events)) == EVENT_NAMES


def test_given_event_names_are_added():
    d = uninhibited.Dispatch(EVENT_NAMES)
    assert list(six.keys(d.events)) == EVENT_NAMES

