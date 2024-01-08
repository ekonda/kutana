from functools import wraps
from random import random
from kutana import Plugin
from kutana.helpers import make_hash
from kutana.storage import Document
from datetime import datetime, timezone, timedelta


plugin = Plugin(
    name="Flipping",
    description="Place your bets on coin flipping (.flipping)",
)


DAILY_REWARD_AMOUNT = 100


class FlippingData:
    @classmethod
    def load_from(cls, ctx):
        return cls(ctx.sender)

    def __init__(self, sender: Document):
        self._now = datetime.now(timezone.utc)
        self._sender = sender
        self._sender_hash = make_hash(sender)
        self._ensure_required_fields()

    @property
    def _flipping_data(self):
        return self._sender["flipping"]

    def _ensure_required_fields(self):
        self._sender["flipping"] = self._sender.get("flipping") or {}

        if "balance" not in self._flipping_data:
            self._flipping_data["balance"] = 0

        if "daily_reward_collected_at" not in self._flipping_data:
            self._flipping_data["daily_reward_collected_at"] = None

    @property
    def balance(self) -> int:
        return self._flipping_data["balance"]

    @balance.setter
    def balance(self, value: int):
        self._flipping_data["balance"] = value

    def _can_collect_daily_money(self):
        if not self._flipping_data["daily_reward_collected_at"]:
            return True

        daily_reward_collected_at = datetime.fromisoformat(
            self._flipping_data["daily_reward_collected_at"]
        )

        return daily_reward_collected_at + timedelta(days=1) < self._now

    def collect_daily_reward(self):
        if not self._can_collect_daily_money():
            return False

        self.balance += DAILY_REWARD_AMOUNT

        self._flipping_data["daily_reward_collected_at"] = self._now.isoformat()

        return True

    async def save(self):
        await self._sender.save()


def with_flipping_data(func):
    @wraps(func)
    async def wrapper(msg, ctx):
        smd = FlippingData.load_from(ctx)

        result = await func(msg, ctx, smd)

        await smd.save()

        return result

    return wrapper


@plugin.on_commands(["flipping", "flipping help"])
async def _(msg, ctx):
    await ctx.reply(
        "ℹ️ Avaialble commands:\n"
        "- flipping balance (to get your current balance)\n"
        "- flipping daily (collect daily income)\n"
        "- flipping play <bet amount> (play with specified bet amount)"
    )


@plugin.on_commands(["flipping daily"])
@plugin.with_storage()
@with_flipping_data
async def _(msg, ctx, smd: FlippingData):
    if smd.collect_daily_reward():
        await ctx.reply(
            f"✅ You have successfully received your daily reward! Your balance: {smd.balance}"
        )
    else:
        await ctx.reply(
            "❎ You have already received a daily reward! Come back tomorrow."
        )


@plugin.on_commands(["flipping balance"])
@plugin.with_storage()
@with_flipping_data
async def _(msg, ctx, smd: FlippingData):
    await ctx.reply(f"💵 Your balance: {smd.balance}")


@plugin.on_commands(["flipping play"])
@plugin.with_storage()
@with_flipping_data
async def _(msg, ctx, smd: FlippingData):
    if not ctx.body or not ctx.body.isnumeric():
        await ctx.reply('🔺 Enter your bet after "play".')
        return

    bet = int(ctx.body)

    if bet <= 0:
        await ctx.reply("🔺 Bet should be higher than 0!")
        return

    if smd.balance < bet:
        await ctx.reply("🔺 There are not enough funds for this bet!")
        return

    if random() < 0.5:
        smd.balance -= bet
        await ctx.reply(
            "😔 Unfortunately, you lost! Your bet went to the house.\n"
            f"💵 Your current balance is: {smd.balance}."
        )
    else:
        smd.balance += bet
        await ctx.reply(
            f"🔥 Congratulations, you have won! You received {bet}!\n"
            f"💵 Your current balance is: {smd.balance}."
        )
