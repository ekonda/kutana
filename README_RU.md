![Kutana logo](docs/_static/kutana-logo-512.png)

[![Documentation Status](https://readthedocs.org/projects/kutana/badge/?version=latest)](https://kutana.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/ekonda/kutana.svg?branch=master)](https://travis-ci.com/ekonda/kutana)
[![CodeFactor](https://www.codefactor.io/repository/github/ekonda/kutana/badge)](https://www.codefactor.io/repository/github/ekonda/kutana)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3119bfb791604b9db38e8e7a13e1d415)](https://www.codacy.com/app/michaelkrukov/kutana?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ekonda/kutana&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/ekonda/kutana/badge.svg?branch=master)](https://coveralls.io/github/ekonda/kutana?branch=master)
[![Codebeat Badge](https://codebeat.co/badges/fd698be3-d0f9-4e3c-b235-1c3a3cdb98a9)](https://codebeat.co/projects/github-com-ekonda-kutana-master)
[![PyPI version](https://badge.fury.io/py/kutana.svg)](https://badge.fury.io/py/kutana)
[![Plugins repo](https://img.shields.io/badge/plugins-repo-green.svg)](https://github.com/ekonda/kutana-plugins)

[English](README.md) | Русский

# Kutana
Движок разработки ботов для соц. сетей, мессенджеров и других систем.
Вы можете найти репозиторий с плагинами для kutana [здесь](https://github.com/ekonda/kutana-plugins).

### Установка
- Загрузить и установить Рython (3.5.3+)

```
https://www.python.org/downloads/
```

- Установить модуль `kutana` (используйте python3, если нужно)

```
python -m pip install kutana
```

### Использование
- Создать оснвоной объект движка Kutana и добавить контроллеры.
- Зарегистрировать плагины в "исполнителе". Импортировать плагины с помощью функциии `load_plugins`. Файлы должны быть Рython модулями и с доступным `plugin` полем. 
- Запустите движок.

Пример `run.py` (Токен для VKController будет загружен из файла
"configuration.json" и плагины будут загружены из папки "plugins/")
```py
from kutana import *

# Создание движка
kutana = Kutana()

# Добавление VKController в движок
kutana.add_controller(
    VKController(load_configuration("vk_token", "configuration.json"))
)

# Загрузить и зарегистрировать плагины
kutana.executor.register_plugins(*load_plugins("plugins/"))

# Запустить движок
kutana.run()
```


Пример `plugins/echo.py`
```py
from kutana import Plugin

plugin = Plugin(name="Echo")

@plugin.on_startswith_text("echo")
async def on_echo(message, attachments, env):
    await env.reply("{}".format(env.body))
```

### Доступные контроллеры
- VKController (vk.com группы)

### Авторы
- **Michael Krukov** - [@michaelkrukov](https://github.com/michaelkrukov)
- **Sergey Abroskin (перевод README)** - [@MerdedSpade](https://github.com/MerdedSpade)
