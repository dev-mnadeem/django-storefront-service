"""Settings for the test suite.

`Eshop.settings` refuses to import without DJANGO_SECRET_KEY unless DEBUG is
on, which is right for a server but would make a bare `pytest` on a fresh
checkout fail before collecting anything. Tests run in development mode
unless the environment says otherwise.
"""

import os

os.environ.setdefault("DJANGO_DEBUG", "true")

from Eshop.settings import *  # noqa: E402, F403
