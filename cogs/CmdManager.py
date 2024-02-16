from discord.ext import commands


class CmdManager(commands.Cog, name="Command Manager"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sync", help="Sync all slash commands.")
    async def sync(self, ctx: commands.Context) -> None:
        fmt = await ctx.bot.tree.sync()
        await ctx.send(f"✅ Synced {len(fmt)} command(s).")


async def setup(bot: commands.Bot):
    await bot.add_cog(CmdManager(bot))
