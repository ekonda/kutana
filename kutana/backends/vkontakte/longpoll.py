import asyncio
import json
import aiohttp
from .backend import Vkontakte
from ...logger import logger


class VkontakteLongpoll(Vkontakte):
    def __init__(self, *args, longpoll_settings=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.longpoll_settings = longpoll_settings or {}
        self.longpoll_data = {}
        self.longpoll_url_template = "{}?act=a_check&key={}&wait=25&ts={}"

    async def update_longpoll_data(self):
        self.longpoll_data = await self.raw_request(
            "groups.getLongPollServer", {"group_id": self.group_id}
        )

    async def _get_updates(self):
        longpoll_url = self.longpoll_url_template.format(
            self.longpoll_data["server"],
            self.longpoll_data["key"],
            self.longpoll_data["ts"],
        )

        try:
            async with self.session.post(longpoll_url) as resp:
                return await resp.json(content_type=None)
        except (json.JSONDecodeError, aiohttp.ClientError, asyncio.TimeoutError):
            return None

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception("Exceptions while gettings updates (Vkontakte)")
            await asyncio.sleep(1)
            return None

    async def acquire_updates(self, submit_update):
        response = await self._get_updates()

        if response is None:
            return

        if "ts" in response:
            self.longpoll_data["ts"] = response["ts"]

        if "failed" in response:
            if response["failed"] in (2, 3):
                await self.update_longpoll_data()
            return

        for update_data in response["updates"]:
            if "type" not in update_data or "object" not in update_data:
                continue

            if update_data["type"] == "group_change_settings":
                changes = update_data["object"]["changes"]

                screen_name = changes.get("screen_name")
                if screen_name:
                    self.group_screen_name = screen_name["new_value"]

                title = changes.get("title")
                if title:
                    self.group_name = title["new_value"]

            await submit_update(self._make_update(update_data))

    async def on_start(self, app):
        await super().on_start(app)

        longpoll_settings = {
            **self.default_updates_settings,
            **self.longpoll_settings,
        }

        await self.raw_request(
            "groups.setLongPollSettings",
            {
                "group_id": self.group_id,
                "api_version": self.api_version,
                "enabled": 1,
                **longpoll_settings,
            }
        )

        await self.update_longpoll_data()
