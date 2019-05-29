![Kutana logo](docs/_static/kutana-logo-512.png)

[![Documentation Status](https://readthedocs.org/projects/kutana/badge/?version=latest)](https://kutana.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://travis-ci.com/ekonda/kutana.svg?branch=master)](https://travis-ci.com/ekonda/kutana)
[![CodeFactor](https://www.codefactor.io/repository/github/ekonda/kutana/badge)](https://www.codefactor.io/repository/github/ekonda/kutana)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3119bfb791604b9db38e8e7a13e1d415)](https://www.codacy.com/app/michaelkrukov/kutana?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ekonda/kutana&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/ekonda/kutana/badge.svg?branch=master)](https://coveralls.io/github/ekonda/kutana?branch=master)
[![Codebeat Badge](https://codebeat.co/badges/fd698be3-d0f9-4e3c-b235-1c3a3cdb98a9)](https://codebeat.co/projects/github-com-ekonda-kutana-master)
[![PyPI version](https://badge.fury.io/py/kutana.svg)](https://badge.fury.io/py/kutana)

[English](README.md) | Русский

# Kutana

Библиотека для разработки систем для мессенджеров и социальных сетей. Хорошо
подходит для разработки ботов. Демонстрацию возможностей библиотеки вы
можете найти в папке [example](https://github.com/ekonda/kutana/tree/master/example).

> Хорошая основа для создания бота с помощью kutana -
> [kubot](https://github.com/ekonda/kubot).

## Установка

- Установить модуль `kutana` (используйте python3, если нужно)

```bash
python -m pip install kutana
```

## Использование

- Создать приложение Kutana и добавить менеджеры.
- Загрузить и зарегистрировать плагины плагины с помощью функциии
    `load_plugins`. Файлы c плагинами должны быть python модулями
    с доступным `plugin` полем, в котором должен находиться экземпляр
    класса `Plugin` или поле `plugins` со список из экземпляров `Plugin`.
- Запустить приложение.

## Пример `run.py`

> Токен для VKManager будет загружен из файла "configuration.json",
> а плагины будут загружены из папки "plugins/"

```py
from kutana import *

# Загрузка настроек
with open("configuration.json") as fh:
    config = json.load(fh)

# Создание приложения
app = Kutana()

# Добавление VKManager в приложение
app.add_manager(VKManager(config["vk_token"]))

# Загрузить и зарегистрировать плагины
app.register_plugins(load_plugins("plugins/"))

# Запустить приложение
app.run()
```

## Пример плагина (`plugins/echo.py`)

```py
from kutana import Plugin

plugin = Plugin(name="Echo")

@plugin.on_startswith_text("echo")
async def _(message, env):
    await env.reply("{}".format(env,body))
```

> Если ваша функция существует только для декаратора, вы можете
> использовать `_`, чтобы избежать ненужных имён

## Доступные менеджеры

- VKManager (для [vk.com](https://vk.com) групп)
- TGManager (для [telegram.org](https://telegram.org) ботов)
  - Тип `document` назван `doc` внутри библиотека.

  - `TGAttachmentTemp` используется для хранения вложений до отправки с
    помощью `send_message` или `reply`. Вложения не могут быть загружены иначе.

  - Если вам нужно скачать файл (вложение) из телеграмма, вы должны
    использовать `TGEnvironment.get_file_from_attachment`.

## Авторы

- **Michael Krukov** - [@michaelkrukov](https://github.com/michaelkrukov)
- [Другие участники](CONTRIBUTORS.md)
