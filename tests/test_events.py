import uninhibited

pe = uninhibited.PriorityEvent()


def test(*args, **kwargs):
    return 'test(*%s, **%s)' % (args, kwargs)


def test2(*args, **kwargs):
    return 'test2', args, kwargs


pe.add(test, priority=10)
pe.add(test2, priority=10)
pe.add(test, priority=0)
pe.add(test2, priority=500)
