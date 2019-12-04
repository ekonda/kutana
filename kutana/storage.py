class Storage:
    """Use Storage.create for instantiation of Storage object."""

    @staticmethod
    async def create(*args, **kwargs):
        raise NotImplementedError

    async def save(self, name, key):
        raise NotImplementedError

    async def load(self, name, default=None):
        raise NotImplementedError
