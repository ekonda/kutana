import asyncio
import logging

from .base import DEFAULT_RECEIVABLE_EVENTS, Vkontakte


class VkontakteLongpoll(Vkontakte):
    def __init__(self, *args, longpoll_settings=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._longpoll_settings = longpoll_settings or {}
        self._longpoll_data = {}
        self._longpoll_url_template = "{}?act=a_check&key={}&wait=25&ts={}"

    async def _update_longpoll_data(self):
        self._longpoll_data = await self._direct_request(
            "groups.getLongPollServer", {"group_id": self.group["id"]}
        )

    async def on_start(self, app):
        await super().on_start(app)

        await self._direct_request(
            "groups.setLongPollSettings",
            {
                "group_id": self.group["id"],
                "api_version": self.api_version,
                "enabled": 1,
                **DEFAULT_RECEIVABLE_EVENTS,
                **self._longpoll_settings,
            },
        )

        await self._update_longpoll_data()

    async def _fetch_updates(self):
        try:
            response = await self.client.post(
                self._longpoll_url_template.format(
                    self._longpoll_data["server"],
                    self._longpoll_data["key"],
                    self._longpoll_data["ts"],
                )
            )
            return response.json()
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("Exceptions while gettings updates (Vkontakte)")
            await asyncio.sleep(1)
            return None

    async def acquire_updates(self, queue: asyncio.Queue):
        while True:
            response = await self._fetch_updates()

            if not response:
                continue

            if "ts" in response:
                self._longpoll_data["ts"] = response["ts"]

            if "failed" in response:
                if response["failed"] in (2, 3):
                    await self._update_longpoll_data()
                continue

            for update in response["updates"]:
                if update["type"] == "group_change_settings":
                    await self._update_group_data()

                await queue.put((self._make_update(update), self))
