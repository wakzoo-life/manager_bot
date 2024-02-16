from discord.ext import commands


class CmdManager(commands.Cog, name="Command Manager"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sync", help="Sync all slash commands.")
    async def sync(self, ctx: commands.Context) -> None:
        msg = await ctx.reply(f"🔌 Now syncing command with Discord...")
        print(f"🔌 Now syncing command with Discord...")

        fmt = await ctx.bot.tree.sync()
        print(f"✅ Synced {len(fmt)} command(s).")
        await msg.edit(content=f"✅ Synced {len(fmt)} command(s).")


async def setup(bot: commands.Bot):
    await bot.add_cog(CmdManager(bot))
