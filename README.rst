uninhibited
===========

Dead simple event handling for Python; minus the straight jacket.

Tested with Python 2.7, 3.4, 3.5.

|Test Status| |Coverage Status| |Documentation Status|

-  PyPi: https://pypi.python.org/pypi/uninhibited


Why should I use this?
----------------------

-  Simple, tiny, and straight forward to use.
-  Prioritized based handlers. Or ``set``. Or ``list``. Or any
   ``iterable``.
-  Doctests.
-  Extensible; Batteries included, not required.
-  Replaceable container implementation.


Installation
------------

.. code:: sh

    pip install uninhibited


Running tests
-------------

Tox is used to handle testing multiple python versions.

.. code:: sh

    tox


.. |Test Status| image:: https://circleci.com/gh/akatrevorjay/uninhibited.svg?style=svg
   :target: https://circleci.com/gh/akatrevorjay/uninhibited
.. |Coverage Status| image:: https://coveralls.io/repos/akatrevorjay/uninhibited/badge.svg?branch=develop&service=github
   :target: https://coveralls.io/github/akatrevorjay/uninhibited?branch=develop
.. |Documentation Status| image:: https://readthedocs.org/projects/uninhibited/badge/?version=latest
   :target: http://uninhibited.readthedocs.org/en/latest/?badge=latest


Async
-----

This is a rough as of yet, asynchronous iterators just aren't there yet
in Python ``3.5.1``.

Python ``3.5.2`` (``rc1`` at time of writing) happens to fix most of my
grievances with them, however, so expect some changes here going
forward.
