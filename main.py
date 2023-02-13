from typing import Optional
import discord
from discord.ext import commands
from discord.ext.commands import Context, Greedy
import utils
import assets
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
# Zephyr server id 791423538531401760
# Test server 1038431009676460082
MY_GUILD = discord.Object(id=1038431009676460082)
appID = 1074125326147391571


class copsbot(commands.Bot):
    def __init__(self, intents=intents):
        super().__init__(intents=intents, command_prefix=commands.when_mentioned,
                         application_id=appID, description="Application bot made by Senpai_Desi")

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=MY_GUILD)

    async def on_ready(self):
        link = utils.load_json(assets.jsonfile)
        linkurl = link["invite_url"]
        print(f"[INFO]  {self.user} has connected to the discord gateaway!")
        for extension in assets.modules:
            await bot.load_extension(extension)
            print(f"[INFO]  Loaded {extension}")
        await bot.change_presence(activity=discord.Game(name="Use /help to get help!"))
        print(f"[INFO]  {linkurl}\n")
        print("[INFO]    Loaded all slash commands\n")


bot = copsbot(intents=intents)
bot.remove_command("help")
"""
*sync -> global sync
*sync guild -> sync current guild
*sync copy -> copies all global app commands to current guild and syncs
*sync delete -> clears all commands from the current guild target and syncs (removes guild commands)
*sync id_1 id_2 -> sync  guilds with 1 and 2
"""


@bot.command(name="synccmd")
@utils.is_bot_admin()
async def sync(
        ctx: Context, guilds: Greedy[discord.Object], spec: Optional[str] = None) -> None:
    if not guilds:
        if spec == "guild":
            synced = await ctx.bot.tree.sync()
        elif spec == "copy":
            ctx.bot.tree.copy_global_to(guild=MY_GUILD)
            synced = await ctx.bot.tree.sync()
        elif spec == "delete":
            ctx.bot.tree.clear_commands()
            await ctx.bot.tree.sync()
            synced = []
        else:
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        print(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return
    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1
    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


json = utils.load_json(assets.jsonfile)
token = json["token"]
bot.run(token=token)