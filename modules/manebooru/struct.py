"""
Classes for Manebooru responses.
"""

import random

from modules.manebooru.api import API_search


class ManebooruPagesInteractive:
    """Interactive object for a paged response object.
Calls the API automatically if new images are necessary."""
    __slots__ = {'session', 'querylist', 'options',
                 'per_page', 'current', 'total', 'data'}

    def __init__(self, session, querylist, per_page=10, **options):
        self.session = session
        self.querylist = querylist
        self.per_page = per_page
        self.current = [1, 1]  # (page, image)
        self.data = None
        self.options = {'sf': 'image id', 'sd': 'descending', **options}
        print(self.options)
        self.total = 0

    async def apiget(self):
        """Calls the API to refresh the current data."""
        self.data = await API_search(self.session, self.querylist, self.current[0], self.per_page, **self.options)
        self.total = self.data['total']

    def msgget(self):
        """Returns the message to send to Discord."""
        imgid = self.data['images'][self.current[1] - 1]['id']
        imgurl = f"https://manebooru.art/images/{imgid}"
        maxpage = min(self.per_page, self.total - self.per_page * (self.current[0] - 1))
        curindex = (self.current[0] - 1) * self.per_page + self.current[1]
        maxpages = -(self.data['total'] // -self.per_page)
        content = f"```apache\nResults: {self.total}\nCurrent_page: {self.current[0]}/{maxpages}\nCurrent_image: {self.current[1]}/{maxpage} | {curindex}/{self.data['total']}\n```\n{imgurl}"
        return {'content': content, 'embed': None}

    def timeout(self):
        """Returns a timeout message."""
        imgid = self.data['images'][self.current[1] - 1]['id']
        imgurl = f"https://manebooru.art/images/{imgid}"
        maxpage = min(self.per_page, self.total - self.per_page * (self.current[0] - 1))
        curindex = (self.current[0] - 1) * self.per_page + self.current[1]
        maxpages = -(self.data['total'] // -self.per_page)
        content = f"```\nResults: {self.total}\nCurrent page: {self.current[0]}/{maxpages}\nCurrent image: {self.current[1]}/{maxpage} | {curindex}/{self.data['total']}\n```\n{imgurl}\n**TIMED OUT**"
        return {'content': content, 'embed': None}

    async def next(self):
        """Go to the next image."""
        # Total limit
        if self.current[0] * self.per_page + self.current[1] == self.total + self.per_page:
            # It's the last image!
            return -1
        self.current[1] += 1

        # Page limit
        if self.current[1] == self.per_page + 1:
            # Next page
            self.current[0] += 1
            self.current[1] = 1
            await self.apiget()
        return self.msgget()

    async def prev(self):
        """Go to the previous image."""
        # Total limit
        if self.current[0] * self.per_page + self.current[1] == self.per_page + 1:
            # It's the first image already!
            return -1
        self.current[1] -= 1

        # Page limit
        if self.current[1] == 0:
            # Previous page
            self.current[0] -= 1
            self.current[1] = self.per_page
            await self.apiget()
        return self.msgget()

    async def fast_forward(self):
        """Go to the next page."""
        # Total limit
        if self.current[0] * self.per_page + self.current[1] == self.total:
            # It's the last image!
            return -1
        if self.current[0] * self.per_page + 1 > self.total:
            # Next page is over the end
            self.current[1] = self.total + self.per_page - self.current[0] * self.per_page
        else:
            self.current[0] += 1
            self.current[1] = 1
            await self.apiget()
        return self.msgget()

    async def rewind(self):
        """Go to the previous page."""
        # Total limit
        if self.current == [1, 1]:
            return -1
        if self.current[1] != 1:
            # Go to first image of page
            self.current[1] = 1
        else:
            # If it's already first image, go to last page
            self.current[0] -= 1
            self.current[1] = 1
        return self.msgget()

    async def random(self):
        """Go to a random image."""
        index = random.randint(1, self.data['total'])
        self.current[0], self.current[1] = -(
                    index // -self.per_page), index % self.per_page if index % self.per_page != 0 else 10
        await self.apiget()
        return self.msgget()
