# Kutana

![Kutana logo](docs/_static/kutana-logo-512.png)

[![Documentation Status](https://readthedocs.org/projects/kutana/badge/?version=latest)](https://kutana.readthedocs.io/en/latest/?badge=latest)
[![CodeFactor](https://www.codefactor.io/repository/github/ekonda/kutana/badge)](https://www.codefactor.io/repository/github/ekonda/kutana)
[![Coverage Status](https://coveralls.io/repos/github/ekonda/kutana/badge.svg?branch=master)](https://coveralls.io/github/ekonda/kutana?branch=master)
[![Codebeat Badge](https://codebeat.co/badges/fd698be3-d0f9-4e3c-b235-1c3a3cdb98a9)](https://codebeat.co/projects/github-com-ekonda-kutana-master)
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

## Running

### From CLI

Following command will populate application's config, add specified backends and
load plugins from specified folder.

```bash
python3 -m kutana --config example/config.yml --plugins example/plugins

# usage: python3 -m kutana [-h] [--config CONFIG] [--plugins PLUGINS] [--debug]

# Run kutana application instance using provided config.

# optional arguments:
#   -h, --help         show this help message and exit
#   --config CONFIG    file with config in yaml format (default: config.yml
#   --plugins PLUGINS  folder with plugins to load (default: plugins)
#   --debug            set logging level to debug
```

Refer to the example [config.yml](https://github.com/ekonda/kutana/tree/master/example/config.example.yml)
for the configuration details.

### From python

```py
import json
from kutana import Kutana, load_plugins
from kutana.backends import Vkontakte

# Import configuration
with open("config.json") as fh:
    config = json.load(fh)

# Create application
app = Kutana()

# Add manager to application
app.add_backend(Vkontakte(token=config["vk_token"]))

# Load and register plugins
app.add_plugins(load_plugins("plugins/"))

if __name__ == "__main__":
    # Run application
    app.run()
```

> Token for Vkontakte is loaded from the file "config.json"
> and plugins are loaded from folder "plugins/"

## Example plugin (`plugins/echo.py`)

```py
from kutana import Plugin, t

plugin = Plugin(name=t("Echo"))

@plugin.on_commands(["echo"])
async def __(msg, ctx):
    await ctx.reply(ctx.body, attachments=msg.attachments)
```

> If your function exists only to be decorated, you can use `_` to avoid
> unnecessary names. Use `__` if you use something like pydash.

## Available backends

- Vkontakte (for [vk.com](https://vk.com) groups)
- Telegram (for [telegram.org](https://telegram.org) bots)

## Authors

- **Michael Krukov** - [@michaelkrukov](https://github.com/michaelkrukov)
- [Other contributors](CONTRIBUTORS.md)
