import os

import yaml

import aiohttp

class Listener:
    """Listener object for Hypixel (Skyblock) commands."""
    def __init__(self, session=None):
        if not session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20))
        else:
            self.session = session
