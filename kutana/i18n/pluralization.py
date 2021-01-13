class Pluralization:
    class NPLURALS:
        """Namespace for nplurals for languages"""

        ru = 3
        uk = ru
        en = 2

    class PLURAL:
        """Namespace for plurals for languages"""

        @staticmethod
        def ru(n):
            if n % 100 in [11, 12, 13, 14]:
                return 2
            if n % 10 == 1:
                return 0
            if n % 10 in [2, 3, 4]:
                return 1
            return 2

        uk = ru

        @staticmethod
        def en(n):
            return 0 if n == 1 else 1

    @classmethod
    def get_languages(cls):
        return [k for k in cls.NPLURALS.__dict__.keys() if k[:1] != "_"]

    def __init__(self, language):
        self.language = language

    def get_nplurals(self):
        return getattr(self.NPLURALS, self.language)

    def get_plural(self, n):
        return getattr(self.PLURAL, self.language)(n)
