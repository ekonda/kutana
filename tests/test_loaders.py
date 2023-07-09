from kutana.helpers import get_path
from kutana.loaders import load_plugins_from_path


def test_load_plugins():
    plugins = load_plugins_from_path(get_path(__file__, "assets"))

    assert len(plugins) == 5
    assert {"plugin 1", "plugin 2", "plugin 4", "plugin 5", "plugin 6"} == set(
        p.name for p in plugins
    )
