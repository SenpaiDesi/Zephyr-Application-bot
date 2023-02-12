from datetime import datetime
from sqlite3 import IntegrityError
import discord
from discord import app_commands
from discord.ext import commands
import utils
process = "Starting task {}/2"
current_date_pretty = datetime.now().strftime("%d/%m/%Y %H:%M:%S")


class Feedback(discord.ui.Modal, title="feedback",):
    name = discord.ui.TextInput(
        label="Name", placeholder="Enter your (discord) name", min_length=1)
    feedback = discord.ui.TextInput(label="Feedback", placeholder="Your feedback here",
                                    required=True, max_length=600, style=discord.TextStyle.long, min_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        admin = await interaction.client.fetch_user(521028748829786134)
        await admin.send(f"Feedback by {interaction.user.display_name}\nName: {self.name}\n\n Feedback: **{self.feedback}**")
        return await interaction.response.send_message("Thanks for your feedback! We received it.")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        return await interaction.response.send_message("Oops, something did not go right. Informed the devs.")


class admins(commands.Cog):
    """The commands used by devs."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="listguilds", description="List all guilds.")
    @utils.is_bot_admin()
    async def listguilds(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Guilds", color=discord.Color.red())
        for guild in self.bot.guilds:
            embed.add_field(
                name=f"{guild.name}", value=f"ID:{guild.id}\nMembers: {guild.member_count}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="load", description="Load a module")
    @utils.is_bot_admin()
    async def load(self, interaction: discord.Interaction, _module: str):
        if not utils.is_bot_developer(interaction.user.id):
            return

        try:
            await self.bot.load_extension(_module)
        except Exception as e:
            await interaction.response.send_message(f"{type(e).__name__} - {e}")
        else:
            await interaction.response.send_message(f"Loaded `{_module}`")

    @app_commands.command(name="unload", description="Unload a module")
    @utils.is_bot_admin()
    async def unload(self, interaction: discord.Interaction, _module: str):
        if not utils.is_bot_developer(interaction.user.id):
            return

        try:
            await self.bot.unload_extension(_module)
        except Exception as e:
            await interaction.response.send_message(f"{type(e).__name__} - {e}")
        else:
            await interaction.response.send_message(f"Unloaded `{_module}` ")

    @app_commands.command(name="reload", description="Reload a module")
    async def _reload(self, interaction: discord.Interaction, _module: str):
        if not utils.is_bot_developer(interaction.user.id):
            return

        try:
            await self.bot.unload_extension(_module)
            await self.bot.load_extension(_module)
        except Exception as e:
            await interaction.response.send_message(f"{type(e).__name__} - {e}")
        else:
            await interaction.response.send_message(f"Reloaded `{_module}`")

    @commands.command(name="dbsetup")
    @utils.is_bot_admin()
    async def dbsetup(self, ctx):
        database = await utils.connect_database()
        message = await ctx.send(process.format("1"))
        try:
            await database.execute("CREATE TABLE IF NOT EXISTS guilds (guildID INTEGER PRIMARY KEY, prefix TEXT)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS moderationLogs (logid INTEGER PRIMARY KEY, guildid INTEGER, moderationLogType INTEGER, userid INTEGER, moduserid INTEGER, content VARCHAR, duration INTEGER)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS logtypes (ID INTEGER PRIMARY KEY, type TEXT)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS botdevs (userid INTEGER PRIMARY KEY, name TEXT)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS playerdatabase (memberid INTEGER PRIMARY KEY, region TEXT, ID TEXT, ign TEXT, rank TEXT, rankkd TEXT, customkd TEXT)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS inventory(memberid, item)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS skininv (memberid INTEGER, skinname TEXT)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS devnotes (memberid INT UNIQUE, date TEXT)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS messages (date TEXT, message TEXT)")
            await database.commit()
            await database.execute("CREATE TABLE IF NOT EXISTS economy (memberid INTEGER UNIQUE, credits BIGINT, tokens BIGINT)")
            await database.commit()
            await message.edit(content=process.format("2"))
        except Exception as e:
            return await ctx.send(f"Could not complete task 1 because of \n{e}")

        try:
            await database.execute("INSERT OR IGNORE INTO logtypes VALUES (?, ?)", (1, "warn",))
            await database.execute("INSERT OR IGNORE INTO logtypes VALUES (?, ?)", (2, "mute",))
            await database.execute("INSERT OR IGNORE INTO logtypes VALUES (?, ?)", (3, "unmute",))
            await database.execute("INSERT OR IGNORE INTO logtypes VALUES (?, ?)", (4, "kick",))
            await database.execute("INSERT OR IGNORE INTO logtypes VALUES (?, ?)", (5, "softban",))
            await database.execute("INSERT OR IGNORE INTO logtypes VALUES (?, ?)", (6, "ban",))
            await database.execute("INSERT OR IGNORE INTO logtypes VALUES (?, ?)", (7, "unban",))
            await database.commit()
        except Exception as e:
            return await ctx.send(f"Could not complete task 2 because of \n{e}")
        try:
            await database.close()
            await message.edit(content="Done!")
        except ValueError:
            pass

    @app_commands.command(name="botadmins", description="modify bot admins.")
    @utils.is_bot_admin()
    async def modify_bot_admins(self, interaction: discord.Interaction, action: str, user: discord.Member):
        database = await utils.connect_database()
        user = await self.bot.fetch_user(user.id)
        string_member_name = str(user.name)

        if action == "add":
            try:
                try:
                    await database.execute("INSERT INTO botdevs VALUES (?, ?)", (user.id, string_member_name))
                except IntegrityError:
                    return await interaction.response.send_message("This user is already a bot admin.")
                await database.commit()
                embed = utils.create_simple_embed(title="✅Success", color=discord.Color.random(
                ), field_title=f"Completed {action}", field_content=f"Completed {action} on {user.id}")
                await interaction.response.send_message(embed=embed)
                await database.close()
            except ValueError:
                pass
        elif action == "delete" or "remove":
            try:
                await database.execute(f"DELETE FROM botdevs WHERE userid = {user.id} ")
                await database.commit()
                embed = utils.create_simple_embed(title="✅Success", color=discord.Color.blue(
                ), field_title=f"Completed {action}", field_content=f"Completed {action} on {user.id}")
                await interaction.response.send_message(embed=embed)
                await database.close()
            except ValueError:
                pass

    @commands.command(name="listadmins")
    async def list_admins(self, ctx):
        database = await utils.connect_database()
        if not utils.is_bot_developer(ctx.author.id):
            return await ctx.send_message("No permission to use this command.", ephemeral=True)
        message = "Bot Admins:\n"
        async with database.execute("SELECT userid, name FROM botdevs") as cursor:
            async for entry in cursor:
                userid, username = entry
                message += f"Dev ID: {userid} -- Dev Name: {username}\n"

        await ctx.send(message)
        try:
            await database.close()
        except ValueError:
            pass

    @app_commands.command(name="feedback", description="provide feedback!")
    async def feedback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(Feedback())

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        try:
            if interaction.command.name == "inbox":
                return
        except AttributeError:
            return
        database = await utils.connect_database()
        check = await database.execute("SELECT date FROM devnotes WHERE memberid = ?", (interaction.user.id,))
        check_result = await check.fetchall()
        message = await database.execute("SELECT message FROM messages")
        message_check = await message.fetchall()
        if check_result:
            return
        else:
            if message_check:
                await interaction.channel.send(f"Hey <@{interaction.user.id}> you have an unread message from developers! Use </inbox:1055908884017074326> to read it.",)
            else:
                return
        try:
            await database.close()
        except ValueError:
            pass

    @app_commands.command(name="inbox", description="Check messages you got from developers.")
    async def inbox(self, interaction: discord.Interaction):
        database = await utils.connect_database()
        message = await database.execute("SELECT message FROM messages")
        send_message = await message.fetchone()
        send_message = str(send_message).strip("(")
        send_message = str(send_message).strip(")")
        send_message = str(send_message).strip(",")
        send_message = str(send_message).strip("'")
        print(message)
        await interaction.response.send_message(send_message, ephemeral=True)
        try:
            await database.execute("INSERT INTO devnotes VALUES (?, ?)", (interaction.user.id, current_date_pretty,))
        except IntegrityError:
            pass
        await database.commit()
        try:
            await database.close()
        except ValueError:
            pass

    @app_commands.command(name="addmessage", description="Dev only command to add a developer alert")
    @utils.is_bot_admin()
    async def add_message(self, interaction: discord.Interaction, *, message_content: str = None):
        database = await utils.connect_database()
        if message_content is None:
            return await interaction.response.send_message("Hey you forgot to add a message!", ephemeral=True)
        else:
            await database.execute("DELETE FROM messages")
            await database.commit()
            await database.execute("INSERT INTO messages VALUES (?, ?)", (current_date_pretty, message_content))
            await database.commit()
            await interaction.response.send_message("Done!", ephemeral=True)
        try:
            await database.close()
        except ValueError:
            pass

    @app_commands.command(name="resetmessages", description="Resets Read status for all users.")
    @utils.is_bot_admin()
    async def reset_messages(self, interaction: discord.Interaction):
        database = await utils.connect_database()
        await database.execute("DELETE FROM devnotes")
        await database.commit()
        try:
            await database.close()
        except ValueError:
            pass
        await interaction.response.send_message("Done!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(admins(bot))
