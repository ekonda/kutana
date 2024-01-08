import asyncio
import logging

from aiohttp import web

from ...helpers import get_random_string
from .base import DEFAULT_RECEIVABLE_EVENTS, Vkontakte


class VkontakteCallback(Vkontakte):
    def __init__(
        self,
        *args,
        address=None,
        path="/",
        host="0.0.0.0",
        port=10888,
        updates_queue_maxsize=0,
        callback_settings=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._address = address
        self._path = path
        self._host = host
        self._port = port
        self._updates_queue_maxsize = updates_queue_maxsize
        self._callback_settings = callback_settings or {}

        self._app_runner = None
        self._updates_queue: asyncio.Queue

    async def _handle_request(self, request):
        data = await request.json()

        if data["type"] == "group_change_settings":
            await self._update_group_data()

        elif data["type"] == "confirmation":
            response = await self._direct_request(
                "groups.getCallbackConfirmationCode",
                {"group_id": data["group_id"]},
            )

            return web.Response(body=f"{response['code']}")

        await self._updates_queue.put(self._make_update(data))

        return web.Response(body="ok")

    def _make_server_app(self):
        app = web.Application()
        app.add_routes([web.post(self._path, self._handle_request)])
        return app

    async def _start_server(self):
        app = self._make_server_app()

        self._app_runner = web.AppRunner(app)

        await self._app_runner.setup()

        site = web.TCPSite(self._app_runner, self._host, self._port)

        await site.start()

    async def _stop_server(self):
        if self._app_runner:
            await self._app_runner.cleanup()

    async def on_start(self, app):
        await super().on_start(app)

        # Prepare queue and start server
        self._updates_queue = asyncio.Queue(self._updates_queue_maxsize)

        await self._start_server()

        # Notify user if we won't setup group
        if not self._address:
            logging.warning(
                "No address provided for VkontakteCallback! You "
                "will have to setup your group's settings manually."
            )
            return

        # Delete other callback servers poiting to our address
        servers = await self._direct_request(
            "groups.getCallbackServers",
            {"group_id": self.group["id"]},
        )

        for server in servers["items"]:
            if server["url"] == self._address:
                await self._direct_request(
                    "groups.deleteCallbackServer",
                    {
                        "group_id": self.group["id"],
                        "server_id": server["id"],
                    },
                )

        # Add a new callback server
        response = await self._direct_request(
            "groups.addCallbackServer",
            {
                "group_id": self.group["id"],
                "url": self._address,
                "title": get_random_string(),
                "secret_key": get_random_string(24),
            },
        )

        server_id = response["server_id"]

        # Updated callback server's settings
        await self._direct_request(
            "groups.setCallbackSettings",
            {
                "group_id": self.group["id"],
                "api_version": self.api_version,
                "server_id": server_id,
                **DEFAULT_RECEIVABLE_EVENTS,
                **self._callback_settings,
            },
        )

    async def on_shutdown(self, app):
        await super().on_shutdown(app)
        await self._stop_server()

    async def acquire_updates(self, queue):
        while True:
            await queue.put((await self._updates_queue.get(), self))
