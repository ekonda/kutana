![Kutana logo](docs/_static/kutana-logo-512.png)

# Kutana
The engine for developing bots for soc. networks, instant messengers and other systems.

## Installation
- Download and install python (3.5.2+)

```
https://www.python.org/downloads/
```

- Install python modules from requirements.txt using installed python (user python3 if needed)

```
python -m pip install -r requirements.txt
``` 

- Put folder `kutana` into your python path or into your project (proper module in pypi will be available later).

```
- myproject/
-- kutana/
-- ...
```

## Usage
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

## Available controllers
- VKontakte groups (only groups)

## Tasks
Task|Priority
---|---
Find and fix all current bugs | high
Find and fix grammar and semantic errors | high
Create proper documentation | medium
Adding tests | medium
Add module to PyPi | low 
Developing plugins | very low