from os.path import dirname
from kutana.loaders import load_plugins


def test_load_plugins():
    plugins = load_plugins(dirname(__file__) + "/assets", verbose=True)

    assert len(plugins) == 3
    assert {"echo", "hello 1", "hello 2"} == set(p.name for p in plugins)
