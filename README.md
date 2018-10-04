![Kutana logo](docs/_static/kutana-logo-512.png)

[![Documentation Status](https://readthedocs.org/projects/kutana/badge/?version=latest)](https://kutana.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/ekonda/kutana.svg?branch=master)](https://travis-ci.com/ekonda/kutana)
[![CodeFactor](https://www.codefactor.io/repository/github/ekonda/kutana/badge)](https://www.codefactor.io/repository/github/ekonda/kutana)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3119bfb791604b9db38e8e7a13e1d415)](https://www.codacy.com/app/michaelkrukov/kutana?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ekonda/kutana&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/ekonda/kutana/badge.svg?branch=master)](https://coveralls.io/github/ekonda/kutana?branch=master)
[![Codebeat Badge](https://codebeat.co/badges/fd698be3-d0f9-4e3c-b235-1c3a3cdb98a9)](https://codebeat.co/projects/github-com-ekonda-kutana-master)
[![PyPI version](https://badge.fury.io/py/kutana.svg)](https://badge.fury.io/py/kutana)
[![Plugins repo](https://img.shields.io/badge/plugins-repo-green.svg)](https://github.com/ekonda/kutana-plugins)

# Kutana
The engine for developing bots for soc. networks, instant messengers and other systems.
You can find repository with plugins for kutana [here](https://github.com/ekonda/kutana-plugins).

### Installation
- Download and install python (3.5.3+)

```
https://www.python.org/downloads/
```

- Install `kutana` module (use python3 if needed)

```
python -m pip install kutana
```

### Usage
- Create `Kutana` engine and add controllers.
- Register your plugins in the executor. You can import plugin from folders with function `load_plugins`. Files should be a valid python modules with available `plugin` field with your plugin (`Plugin`).
- Start engine.

Example `run.py` (token for VKController is loaded from the file
"configuration.json" and plugins are loaded from folder "plugins/")
```py
from Kutana import *

# Create engine
kutana = Kutana()

# Add VKController to engine
kutana.add_controller(
    VKController(load_configuration("vk_token", "configuration.json"))
)

# Load and register plugins
kutana.executor.register_plugins(*load_plugins("plugins/"))

# Run engine
kutana.run()
```


Example `plugins/echo.py`
```py
from kutana import Plugin

plugin = Plugin(name="Echo")

@plugin.on_startswith_text("echo")
async def on_echo(message, attachments, env):
    await env.reply("{}".format(env.body))
```

### Available controllers
- VKController (vk.com groups)

### Authors
- **Michael Krukov** - [@michaelkrukov](https://github.com/michaelkrukov)
