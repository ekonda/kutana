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

        longpoll_settings = dict(
            message_new=1, message_reply=0, message_allow=0,
            message_deny=0, message_edit=0, photo_new=0, audio_new=0,
            video_new=0, wall_reply_new=0, wall_reply_edit=0,
            wall_reply_delete=0, wall_reply_restore=0, wall_post_new=0,
            wall_repost=0, board_post_new=0, board_post_edit=0,
            board_post_restore=0, board_post_delete=0, photo_comment_new=0,
            photo_comment_edit=0, photo_comment_delete=0,
            photo_comment_restore=0, video_comment_new=0,
            video_comment_edit=0, video_comment_delete=0,
            video_comment_restore=0, market_comment_new=0,
            market_comment_edit=0, market_comment_delete=0,
            market_comment_restore=0, poll_vote_new=0, group_join=0,
            group_leave=0, group_change_settings=1, group_change_photo=0,
            group_officers_edit=0, user_block=0, user_unblock=0
        )

        longpoll_settings.update(self.longpoll_settings)

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
