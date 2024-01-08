# Kutana

![Kutana logo](./docs/kutana-logo-512.png?raw=true "Kutana")

[![PyPI version](https://badge.fury.io/py/kutana.svg)](https://badge.fury.io/py/kutana)

The library for developing systems for messengers and social networks. Great
for developing bots. Refer to [example](https://github.com/ekonda/kutana/tree/master/example)
for the showcase of the library abilities.

This library uses generalized attachment types, possible actions e.t.c. for flexibility
to use plugins with different backends.

## Installation

```bash
python -m pip install kutana
```

## Documentation

You can read the extended description of the library in
the [docs/index.md](example/config.example.yml) file. At the moment,
the documentation is not in the best condition. If you would like
to contribute to its writing, welcome to the issues.

## Running

### From CLI

Following command will populate application's config, add specified backends and
load plugins from specified folder.

```bash
python3 -m kutana run example/config.yml

# usage: kutana [-h] {init,run} ...
#
# helpfull cli utility
#
# positional arguments:
#   {init,run}
#     init      initiate kutana project
#     run       run kutana project using provided config (working directory will be changed to the one with config file)
#
# optional arguments:
#   -h, --help  show this help message and exit
```

Refer to the example [config.yml](example/config.example.yml)
for the configuration details.

### From code

```py
from kutana import Kutana
from kutana.backends import VkontakteLongpoll
from kutana.loaders import load_plugins_from_path

# Create application
app = Kutana()

# Add manager to application
app.add_backend(VkontakteLongpoll(token="VK-GROUP-TOKEN"))

# Load and register plugins
for plugin in load_plugins_from_path("example/plugins/"):
    app.add_plugin(plugin)

if __name__ == "__main__":
    # Run application
    app.run()
```

## Example plugin (`plugins/echo.py`)

```py
from kutana import Plugin

plugin = Plugin(name="Echo")

@plugin.on_commands(["echo"])
async def _(msg, ctx):
    await ctx.reply(ctx.body, attachments=msg.attachments)
```

> If your function exists only to be decorated, you can use `_` to avoid
> unnecessary names.

## Available backends

- Vkontakte (for [vk.com](https://vk.com) groups)
- Telegram (for [telegram.org](https://telegram.org) bots)
