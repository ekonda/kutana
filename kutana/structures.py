import collections


class objdict(collections.MutableMapping):
    """dict with gettings and settings throught dot."""

    __slots__ = ("_store",)

    def __init__(self, *args, **kwargs):
        self._store = dict()

        self.update(dict(*args))
        self.update(kwargs)

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            return object.__setattr__(self, name, value)

        return self.__setitem__(name, value)

    def __getitem__(self, key):
        return self._store[key]

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            self._store[key] = objdict(value)
        else:
            self._store[key] = value

    def __delitem__(self, key):
        del self._store[key]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __str__(self):
        return str(self._store)

    def __repr__(self):  # pragma: no cover
        return repr(self._store)


class icedict(collections.Mapping):
    """Immutable dict.
    Thanks
    https://stackoverflow.com/questions/2703599/what-would-a-frozen-dict-be
    """

    __slots__ = ("_store",)

    def __init__(self, *args, **kwargs):
        self._store = dict(*args)
        self._store.update(kwargs)

    def __eq__(self, other):
        if isinstance(other, icedict):
            return self._store == other._store

        return self._store == other

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __getattr__(self, name):
        return self.__getitem__(name)

    def __getitem__(self, key):
        return self._store[key]

    def __str__(self):
        return str(self._store)

    def __repr__(self):  # pragma: no cover
        return repr(self._store)
