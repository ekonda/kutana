import os
import pytest
from kutana.i18n import t, set_default_language, load_translations, clear_translations
from kutana.i18n.translator import load_translations_file
from kutana.i18n.pluralization import Pluralization


def test_pluralization():
    languages = Pluralization.get_languages()
    assert languages

    for lang in languages:
        plur = Pluralization(lang)

        nplurals = plur.get_nplurals()
        assert nplurals

        used_nplurals = set()

        for i in range(100):
            plural = plur.get_plural(i)
            used_nplurals.add(plural)
            assert plural >= 0
            assert plural < nplurals

        assert len(used_nplurals) == nplurals


def get_message(name, beers, lang=None):
    return "- {}\n- {}\n- {}".format(
        t("Hello, {}!", name, lang=lang),
        t("Hi!", ctx="c:gopnik", lang=lang),
        t("I already drank {} beers.", beers, num=beers, lang=lang)
    )


def test_translation():
    clear_translations()
    load_translations(os.path.join(os.path.dirname(__file__), "assets/i18n"))

    set_default_language("en")
    assert get_message("Jack", 1) == "- Hello, Jack!\n- Hi!\n- I already drank 1 beer."
    assert get_message("Jack", 5) == "- Hello, Jack!\n- Hi!\n- I already drank 5 beers."

    set_default_language("ru")
    assert get_message("Jack", 1) == "- Привет, Jack!\n- Здарова!\n- Я уже выпил 1 бутылку пива."
    assert get_message("Jack", 5) == "- Привет, Jack!\n- Здарова!\n- Я уже выпил 5 бутылок пива."

    assert get_message("Jack", 5, "en") == "- Hello, Jack!\n- Hi!\n- I already drank 5 beers."


def test_translation_exception():
    clear_translations()
    load_translations(os.path.join(os.path.dirname(__file__), "assets/i18n"))

    with pytest.raises(ValueError):
        t("I already drank {} beers.", 5, lang="ru")


def test_utils():
    clear_translations()

    load_translations(os.path.join(os.path.dirname(__file__), "assets/i18n"))
    load_translations(os.path.join(os.path.dirname(__file__), "assets/i18n/en.yml"))
    load_translations(os.path.join(os.path.dirname(__file__), "assets/i18n/ru.yml"))

    load_translations("")
    load_translations_file("")

    assert t("Hello, {}!", "Михаил", lang="ru") == "Привет, Михаил!"
