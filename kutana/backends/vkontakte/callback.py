from urllib.parse import urlparse
import asyncio
import re
from aiohttp import web
from .backend import Vkontakte
from ...helpers import get_random_string
from ...logger import logger


DEFAULT_ADDRESS = "0.0.0.0:8080/callback/1"


class VkontakteCallback(Vkontakte):
    def __init__(
        self,
        *args,
        address=None,
        address_path=None,
        host="0.0.0.0",
        port=10888,
        queue_limit=0,
        callback_settings=None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.callback_settings = callback_settings or {}

        if address:
            if not re.match(r"^https://", address):
                address = f"https://{address}"

            self._address = address
            self._address_path = address_path or urlparse(address).path or "/"

        else:
            self._address = None
            self._address_path = address_path or "/"

        self._server_path = self._address_path
        self._server_host = host
        self._server_port = port
        self._server_app_runner = None

        self._queue_limit = queue_limit
        self.updates_queue = None

    async def handle_request(self, request):
        data = await request.json()

        if data["type"] == "confirmation":
            resp = await self.request(
                "groups.getCallbackConfirmationCode",
                group_id=data["group_id"]
            )

            return web.Response(body=f"{resp['code']}")

        await self.updates_queue.put(self._make_update(data))

        return web.Response(body="ok")

    def make_server_app(self):
        app = web.Application()
        app.add_routes([web.post(self._server_path, self.handle_request)])
        return app

    async def start_server(self):
        app = self.make_server_app()

        self._server_app_runner = web.AppRunner(app)

        await self._server_app_runner.setup()

        site = web.TCPSite(
            self._server_app_runner,
            self._server_host,
            self._server_port
        )

        await site.start()

    async def stop_server(self):
        if self._server_app_runner:
            await self._server_app_runner.cleanup()

    async def on_start(self, app):
        await super().on_start(app)

        # Setup queue
        self.updates_queue = asyncio.Queue(self._queue_limit, loop=app.get_loop())

        # Start web server
        await self.start_server()

        if not self._address:
            logger.warning(
                "No address provided for VkontakteCallback! You "
                "will have to setup your group's settings manually."
            )
            return

        # Delete existing servers in group's callback servers
        servers = await self.request(
            "groups.getCallbackServers",
            group_id=self.group_id
        )

        title_num = 1

        for server in servers["items"]:
            if server["url"] == self._address:
                await self.request(
                    "groups.deleteCallbackServer",
                    group_id=self.group_id,
                    server_id=server["id"],
                )

            elif server["title"].startswith("kutana@") and server["title"][7:].isdigit():
                title_num = max(title_num, int(server["title"][7:]) + 1)

        # Add server to group's callback servers
        response = await self.request(
            "groups.addCallbackServer",
            group_id=self.group_id,
            url=self._address,
            title=f"kutana@{title_num}",
            secret_key=get_random_string(),
        )

        server_id = response["server_id"]

        # Setup callback server
        callback_settings = {
            **self.default_updates_settings,
            **self.callback_settings,
        }

        await self.request(
            "groups.setCallbackSettings",
            group_id=self.group_id,
            api_version=self.api_version,
            server_id=server_id,
            **callback_settings,
        )

    async def on_shutdown(self, app):
        await super().on_shutdown(app)
        await self.stop_server()

    async def acquire_updates(self, submit_update):
        await submit_update(await self.updates_queue.get())
