import os
import os.path
import yaml
from .pluralization import Pluralization


DEFAULT_LANGUAGE = "en"
TRANSLATIONS = {}


class Translation:
    __slots__ = ("msgid", "msgctx", "msgstr", "language")

    def __init__(self, msgid, msgctx, msgstr=None):
        self.msgid = msgid
        self.msgctx = msgctx
        self.msgstr = msgstr or msgid

    @staticmethod
    def make_key(msgid, msgctx):
        return (msgid, msgctx or "")

    @property
    def key(self):
        return self.make_key(self.msgid, self.msgctx)

    def get(self, num=None, language=None):
        if num is None:
            if isinstance(self.msgstr, (list, tuple)):
                raise ValueError('Translated string requires "num" argument')
            return self.msgstr
        return self.msgstr[Pluralization(language or DEFAULT_LANGUAGE).get_plural(num) % len(self.msgstr)]


def load_translations(path):
    if not path:
        return

    if os.path.isfile(path):
        load_translations_file(path)

    if not os.path.isdir(path):
        return

    for dirpath, __, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".yml"):
                load_translations_file(os.path.join(dirpath, filename))


def load_translations_file(path):
    if not os.path.isfile(path):
        return

    language = "".join(os.path.basename(path).rsplit(".yml", 1))

    with open(path, "r") as fh:
        strings = yaml.safe_load(fh.read())

    if language not in TRANSLATIONS:
        TRANSLATIONS[language] = {}

    for string in strings:
        translation = Translation(
            msgid=string["msgid"],
            msgctx=string.get("msgctx"),
            msgstr=string.get("msgstr"),
        )

        TRANSLATIONS[language][translation.key] = translation


def clear_translations():
    for language in TRANSLATIONS.values():
        language.clear()
    TRANSLATIONS.clear()


def set_default_language(language):
    global DEFAULT_LANGUAGE
    DEFAULT_LANGUAGE = language


def t(msgid, *args, ctx=None, num=None, lang=None, **kwargs):
    translation = Translation(msgid, ctx)
    if num is not None:
        translation.msgstr = [translation.msgstr]

    language = lang or DEFAULT_LANGUAGE
    if language in TRANSLATIONS:
        translation = TRANSLATIONS[language].get(translation.key, translation)

    return translation.get(num=num, language=language).format(*args, **kwargs)


load_translations(os.path.join(__file__, "default"))
