import pickle
from os.path import dirname
from unittest.mock import patch

from kutana.loaders import load_plugins


def test_load_plugins():
    plugins = load_plugins(dirname(__file__) + "/assets", verbose=True)

    assert len(plugins) == 3
    assert {"echo", "hello 1", "hello 2"} == set(p.name for p in plugins)


@patch("kutana.plugin.Plugin.on_match")  # on_match is incompatible with pickle
def test_pickle_dumps(_):
    plugins = load_plugins("tests/assets", verbose=True)

    assert len(plugins) == 3
    assert {"echo", "hello 1", "hello 2"} == set(p.name for p in plugins)

    pickle.dumps(plugins)
