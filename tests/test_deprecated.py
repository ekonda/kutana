from kutana import Plugin

def test_deprecated():
    plugin = Plugin('')

    assert plugin.on_any_message()
    assert plugin.on_any_unprocessed_message()
    assert plugin.on_any_update()
    assert plugin.on_any_unprocessed_update()
    assert plugin.vk.on_payload()
