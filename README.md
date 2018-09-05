![Kutana logo](docs/_static/kutana-logo-512.png)

[![Documentation Status](https://readthedocs.org/projects/kutana/badge/?version=latest)](https://kutana.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/vk-brain/kutana.svg?branch=master)](https://travis-ci.com/vk-brain/kutana)
[![CodeFactor](https://www.codefactor.io/repository/github/vk-brain/kutana/badge)](https://www.codefactor.io/repository/github/vk-brain/kutana)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3119bfb791604b9db38e8e7a13e1d415)](https://www.codacy.com/app/michaelkrukov/kutana?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=vk-brain/kutana&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/vk-brain/kutana/badge.svg?branch=master)](https://coveralls.io/github/vk-brain/kutana?branch=master)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/vk-brain/kutana.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/vk-brain/kutana/alerts/)
[![PyPI version](https://badge.fury.io/py/kutana.svg)](https://badge.fury.io/py/kutana)

# Kutana
The engine for developing bots for soc. networks, instant messengers and other systems.

### Installation
- Download and install python (3.5.2+)

```
https://www.python.org/downloads/
```

- Install `kutana` module (use python3 if needed)

```
python -m pip install kutana
```

### Usage
- Create `Kutana` engine and add controllers. You can use shortcuts like `VKKutana` for adding and registering controllers, callbacks and other usefull functions.
- You can set settings in `Kutana.settings`.
- Add or create plugins other files and register them in executor. You can import plugin from files with function `load_plugins`. Files should be a valid python modules with available `plugin` field with your plugin (`Plugin`).
- Start engine.

Example `run.py`
```py
from kutana import Kutana, VKKutana, load_plugins

# Creation
kutana = VKKutana(configuration="configuration.json")

# Settings
kutana.settings["MOTD_MESSAGE"] = "Greetings, traveler."

# Create simple plugin
plugin = Plugin()

@self.plugin.on_text("hi", "hi!")
async def greet(message, attachments, env, extenv):
    await env.reply("Hello!")

kutana.executor.register_plugins(plugin)

# Load plugins from folder
kutana.executor.register_plugins(*load_plugins("plugins/"))

# Start kutana
kutana.run()
```

Example `plugins/echo.py`
```py
from kutana import Plugin

plugin = Plugin()

plugin.name = "Echo"

@plugin.on_startswith_text("echo")
async def on_message(message, attachments, env, extenv):
    await env.reply("{}!".format(env.body))
```

### Available controllers
- VKController (vk.com groups)

### Tasks
Task|Priority
---|---
Find and fix all current bugs | high
Find and fix grammar and semantic errors | high
Create proper documentation | medium
Adding tests | medium
Add module to PyPi | low
Developing plugins | very low

### Authors
- **Michael Krukov** - [@michaelkrukov](https://github.com/michaelkrukov)
