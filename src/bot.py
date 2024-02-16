import os
import asyncio

from discord import Game, Intents
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix="wl!", intents=Intents.all(), application_id=os.getenv("CLIENT_ID"))
bot.remove_command("help")


async def load_extensions():
    print("------------------------------------")

    directory_prefix = "." if os.path.exists("cogs") else "src"

    for file in os.listdir(os.path.join(directory_prefix, "cogs")):
        if file.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                print(f"cogs.{file[:-3]} ({file}) ✅")
            except Exception as e:
                print(f"cogs.{file[:-3]} ({file}) ❌ -> {e}")

    print("------------------------------------")


@bot.event
async def on_ready():
    print(f"🔌 {bot.user} ({bot.user.id}) is now syncing command with Discord...")
    await bot.tree.sync()
    print(f"🚀 {bot.user} ({bot.user.id}) is ready!")

    await bot.change_presence(activity=Game(name="왁물원 생활! 팀 운영 지원"))


async def main():
    async with bot:
        await bot.load_extension("jishaku")
        await load_extensions()

        await bot.start(os.getenv("TOKEN"))


asyncio.run(main())
