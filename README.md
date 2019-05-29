# Kutana

![Kutana logo](docs/_static/kutana-logo-512.png)

[![Documentation Status](https://readthedocs.org/projects/kutana/badge/?version=latest)](https://kutana.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/ekonda/kutana.svg?branch=master)](https://travis-ci.com/ekonda/kutana)
[![CodeFactor](https://www.codefactor.io/repository/github/ekonda/kutana/badge)](https://www.codefactor.io/repository/github/ekonda/kutana)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3119bfb791604b9db38e8e7a13e1d415)](https://www.codacy.com/app/michaelkrukov/kutana?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ekonda/kutana&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/ekonda/kutana/badge.svg?branch=master)](https://coveralls.io/github/ekonda/kutana?branch=master)
[![Codebeat Badge](https://codebeat.co/badges/fd698be3-d0f9-4e3c-b235-1c3a3cdb98a9)](https://codebeat.co/projects/github-com-ekonda-kutana-master)
[![PyPI version](https://badge.fury.io/py/kutana.svg)](https://badge.fury.io/py/kutana)

English | [Русский](README.ru.md)

The library for developing systems for messengers and social networks. Great
for developing bots. Refer to [example](https://github.com/ekonda/kutana/tree/master/example)
for the showcase of the library abilities.

> Nice foundation for bot using kutana library -
> [kubot](https://github.com/ekonda/kubot).

## Installation

```bash
python -m pip install kutana
```

## Usage

- Create `Kutana` application and add managers.
- Register your plugins in the executor. You can import plugin from folders
    with function `load_plugins`. Files should be a valid python modules with
    available `plugin` field with your plugin (`Plugin`) or field `plugins`
    with list of instances of `Plugin` class.
- Start application.

## Example `run.py`

> Token for VKManager is loaded from the file "configuration.json"
> and plugins are loaded from folder "plugins/"

```py
from kutana import *

# Load configuration
with open("configuration.json") as fh:
    config = json.load(fh)

# Create application
app = Kutana()

# Create and add VKManager to application
app.add_manager(VKManager(config["vk_token"]))

# Load and register plugins
app.register_plugins(load_plugins("plugins/"))

# Run application
app.run()
```

## Example plugin (`plugins/echo.py`)

```py
from kutana import Plugin

plugin = Plugin(name="Echo")

@plugin.on_startswith_text("echo")
async def _(message, env):
    await env.reply("{}".format(env.body))
```

> If your function exists only to be decorated, you can use `_` to avoid
> unnecessary names

## Available managers

- VKManager (for [vk.com](https://vk.com) groups)
- TGManager (for [telegram.org](https://telegram.org) bots)
  - `document`'s type is named `doc` inside of Kutana.

  - `TGAttachmentTemp` is used for storing attachments before sending them
    with `send_message` or `reply`. Attachments can't be uploaded other way

  - If you want to download file (attachment) from telegram, you have to use
    `TGEnvironment.get_file_from_attachment`

## Authors

- **Michael Krukov** - [@michaelkrukov](https://github.com/michaelkrukov)
- [Other contributors](CONTRIBUTORS.md)
