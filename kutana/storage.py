class Storage:
    async def initiate(self):  # pragma: no cover
        pass

    async def save(self, name, value):
        raise NotImplementedError

    async def load(self, name, default=None):
        raise NotImplementedError
