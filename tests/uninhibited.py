def test(*args, **kwargs):
    return 'test(*%s, **%s)' % (args, kwargs)


def test2(*args, **kwargs):
    return 'test2', args, kwargs


import asyncio

loop = asyncio.get_event_loop()
loop.set_debug(True)


def run(*fs):
    return [loop.run_until_complete(f) for f in fs]


async def atest(*args, **kwargs):
    await asyncio.sleep(1)
    return 'atest', args, kwargs


@asyncio.coroutine
def atest2(*args, **kwargs):
    yield from asyncio.sleep(1)
    return 'atest2', args, kwargs


async def atest3(*args, **kwargs):
    await asyncio.sleep(5)
    return 'atest3(*%s, **%s)' % (args, kwargs)


async def atest4(*args, **kwargs):
    raise Exception("test4: %s %s" % (args, kwargs))


import uninhibited

pe = events.PriorityEvent()

pe.add(test, priority=10)
pe.add(test2, priority=10)
pe.add(test, priority=0)
pe.add(test2, priority=500)

ape = events.AsyncPriorityEvent()

ape.add(atest, priority=10)
ape.add(atest2, priority=10)
ape.add(atest3, priority=10)
# ape.add(atest4, priority=10)
ape.add(atest, priority=0)
ape.add(atest2, priority=500)


def ape_ifire():
    return ape.ifire('arg1')


def ape_ifire_by_priority():
    return list(ape.ifire_by_priority('arg1'))


def ape_fire():
    return ape.fire('arg1')


def ape_fire_by_priority():
    return list(ape.fire_by_priority('arg1'))


def ape_wait():
    for p, results in ape.fire_by_priority('arg1'):
        # fs = (f for handler, f in results)
        handlers, fs = zip(*list(results))
        f = asyncio.wait(fs)
        yield p, results, f


def ape_gather():
    for p, results in ape.fire_by_priority('arg1'):
        # fs = (f for handler, f in results)
        handlers, fs = zip(*list(results))
        f = asyncio.gather(*fs)
        yield p, results, f


def ape_as_completed():
    for p, hs, rs in ape.fire_by_priority('arg1'):
        for f in asyncio.as_completed(rs):
            r = loop.run_until_complete(f)
            yield p, f, r


async def test_aiter():
    gen = ape.ifire('test')
    ret = []
    async for handler, result in gen:
        print(handler, result)
        ret.append((handler, result))
    return ret


async def test_iter():
    gen = ape.ifire('test')
    ret = []
    for f in gen:
        print(f)
        handler, result = await f
        print(handler, result)
        ret.append((handler, result))
    return ret


def test2():
    return ape.ifire('test')


