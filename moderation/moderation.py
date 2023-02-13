import asyncio
import re
import sqlite3
import time
import aiosqlite
import discord
import discord.errors
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions
import utils as utilities
time_regex = re.compile("(?:(\d{1,5})(h|s|m|d))+?")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


def log_counter():
    db = sqlite3.connect("./database.db")
    cur = db.cursor()
    cur.execute("SELECT COUNT (*) FROM moderationLogs")
    global new_case
    result = cur.fetchone()
    new_case = result[0] + 1
    return new_case


def log_converter(type):
    global newtype
    if type == 1:
        newtype = "warn"
        return newtype
    elif type == 2:
        newtype = "mute"
        return newtype
    elif type == 3:
        newtype = "unmute"
        return newtype
    elif type == 4:
        newtype = "kick"
        return newtype
    elif type == 5:
        newtype = "softban"
        return newtype
    elif type == 6:
        newtype = "ban"
        return newtype
    elif type == 7:
        newtype = "unban"
        return newtype


class TimeConverter(commands.Converter):
    async def convert(argument):
        args = argument.lower()
        matches = re.findall(time_regex, args)
        time = 0
        for v, k in matches:
            try:
                time += time_dict[k]*float(v)
            except KeyError:
                raise commands.BadArgument(
                    "{} is an invalid time-key! h/m/s/d are valid!".format(k))
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v))
        return time


class moderation(commands.Cog):
    """Moderation commands for people who do not behave."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        database = await utilities.connect_database()
        await database.execute("CREATE TABLE IF NOT EXISTS moderationLogs (logid INTEGER PRIMARY KEY, guildid int, moderationLogType int, userid int, moduserid int, content varchar, duration int)")
        await database.commit()
        time.sleep(2)
        try:
            await database.close()
        except ConnectionError:
            print("Closed log db")
            pass

    @app_commands.command(name="kick", description="Kick an user.")
    @commands.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = None):
        """Kicks an user, Format: @user Reason for kick"""
        database = await utilities.connect_database()
        await interaction.channel.purge(limit=1)
        try:
            log_counter()
            database.execute("INSERT OR IGNORE INTO moderationLogs (logid, guildid, moderationLogType, userid, moduserid, content, duration) VALUES(?, ?, ?, ?, ?, ?)",
                             (new_case, interaction.guild.id, 4, member.id, interaction.user.id, reason, "0"))
            await database.commit()
            await asyncio.sleep(2)
            await database.close()
        except aiosqlite.DatabaseError as e:
            print(e)
            try:
                await member.kick(reason=reason)
                await interaction.response.send_message(f"✅Kicked {member.name}#{member.discriminator}")
            except MissingPermissions:
                return await interaction.response.send_message("You do not have the right permission to kick this user.")

    @app_commands.command(name='ban', description="Ban an user")
    @commands.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, *, reason: str = None):
        """Bans an user. Format: ban @user reason"""
        database = await utilities.connect_database()
        await interaction.channel.purge(limit=1)
        try:
            await member.ban(reason=reason)
        except MissingPermissions:
            await interaction.response.send_message("You do not have the permission(s) to use this.")
        try:
            log_counter()
            await database.execute("INSERT OR IGNORE INTO moderationLogs (logid, guildid, moderationLogType, userid, moduserid, content, duration) VALUES (?, ?, ?, ?, ?, ?,?)", (new_case, interaction.guild.id, 6, member.id, interaction.user.id, reason, "0"))
            await database.commit()
            await asyncio.sleep(2)
            await database.close()
        except sqlite3.Connection.Error as e:
            print(f"Connection Closed {e}\n")
            pass
        await interaction.response.send_message(f"Logged and Banned ✅ {member}")
        try:
            await member.send(f"Hey {member.display_name} You got banned in **{interaction.guild.name}** for: \n**{reason}**")
        except discord.errors.Forbidden:
            return await interaction.channel.send(f"❎Failed to dm {member.name}#{member.discriminator}. Logged ban. ")

    @app_commands.command(name='unban', description="unban an user.")
    @commands.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, member: str, *, reason: str = None):
        """Unbans an user from the server. Format: username#0000"""
        database = await utilities.connect_database()
        await interaction.channel.purge(limit=1)
        banned_users = await interaction.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await interaction.guild.unban(user)
                await interaction.response.send_message(f'Unbanned {user.mention}')
                try:
                    log_counter()
                    cur = database.cursor()
                    await database.execute("INSERT OR IGNORE INTO moderationLogs (logid, guildid, moderationLogType, userid, moduserid, content, duration) VALUES (?, ?, ?, ?, ?, ?, ?)", (new_case, interaction.guild.id, 7,  member.id, interaction.user.id, reason, "0"))
                    await database.commit()
                    await asyncio.sleep(2)
                    await cur.close()
                    await database.close()
                except sqlite3.Connection.Error:
                    print("Db closed")
                    pass
            return

    @commands.command(name='clear', aliases=['Clear', 'Clr'])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=200):
        """Clears the channel by given amount. Max of 200"""
        await ctx.channel.purge(limit=amount)
        await ctx.send("Channel cleared!")
        time.sleep(1)
        await ctx.channel.purge(limit=1)

    @app_commands.command(name='mute', description="Mute a user.")
    @commands.has_permissions(manage_messages=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, time: str = None, *, reason: str = None):
        """Mute an  user. Format @user time(optional, 1h, 1d etc) Reason for mute"""
        database = await utilities.connect_database()
        role = discord.utils.get(interaction.guild.roles, name="Muted")
        role_to_remove = []
        log_counter()
        new_time = await TimeConverter.convert(argument=time)
        if not role:
            await interaction.guild.create_role(name="Muted")
            for channel in interaction.guild.channels:
                await channel.set_permissions(role, speak=False, send_messages=False, read_message_history=True, read_messages=False)
        try:
            if member is not None:
                if time is not None:
                    await member.remove_roles()
                    await member.add_roles(role)
                    await database.execute("INSERT INTO moderationLogs (logid, guildid, moderationLogType, userid, moduserid, content, duration) VALUES(?, ?, ?, ?, ?, ?, ?)", (new_case, interaction.guild.id, 2, member.id, interaction.user.id, reason, time))
                    await database.commit()
                    await asyncio.sleep(2)
                    await database.close()
                    embed = utilities.create_simple_embed("Muted", discord.Color.blue(
                    ), f"Muted {member.display_name}", f"✅Muted user {member.name}#{member.discriminator} for **{reason}**")
                    try:
                        await member.send(f"You got muted in **{interaction.guild.name}** for {reason} and lasts. {time}.")
                    except discord.errors.Forbidden:
                        return await interaction.response.send_message(f"Logged mute, Could not dm  <@{member.id}>")
                    await interaction.channel.send(embed=embed)
                    await asyncio.sleep(new_time)
                    await member.remove_roles(role)
                else:
                    await member.edit(roles=[])
                    await member.add_roles(role)
                    await database.execute("INSERT INTO moderationLogs (logid, guildid, moderationLogType, userid, moduserid, content, duration) VALUES(?, ?, ?, ?, ?, ?, ?)", (new_case, interaction.guild.id, 2, member.id, interaction.user.id, reason, time))
                    await database.commit()
                    await asyncio.sleep(2)
                    await database.close()
                    embed = utilities.create_simple_embed("Muted", discord.Color.blue(
                    ), f"Muted {member.display_name}", f"✅Muted user {member.name}#{member.discriminator} for **{reason}**")
                    try:
                        await member.send(f"You got muted in  **{interaction.guild.name}** for {reason} and is permanent.")
                    except discord.errors.Forbidden:
                        return await interaction.channel.send(f"Logged mute, Could not dm. <@{member.id}>")
                    await interaction.channel.send(embed=embed)
            else:
                if member == interaction.user:
                    return await interaction.response.send_message("You can not mute yourself.")
                elif member == self.bot.user:
                    return await interaction.response.send_message("You can not mute me.")
        except MissingPermissions or discord.errors.Forbidden:
            return await interaction.response.send_message("I can not mute that user since my roles are lower.")

    @app_commands.command(name='ping', description="check the bots ping.")
    @commands.has_permissions(add_reactions=True)
    async def ping(self,  interaction: discord.Interaction):
        """check latency."""
        await interaction.response.send_message('Pong! `{0} ms `'.format(round(self.bot.latency * 1000)))

    @app_commands.command(name='warn', description="Warn an user.")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, *, reason: str):
        """Warn an user. Format: @user reason for warn"""
        database = await utilities.connect_database()
        if member is not None:
            if reason is not None:
                log_counter()
                await database.execute("INSERT INTO moderationLogs (logid, guildid, moderationLogType, userid, moduserid, content, duration) VALUES (?, ?, ?, ?, ?, ?,?)", (new_case, interaction.guild.id, 1, member.id, interaction.user.id, reason, "0"))
                await database.commit()
                await asyncio.sleep(2)
                await database.close()
                try:
                    await member.send(f"You got warned in  {interaction.guild.name} for: `{reason}.`")
                    await interaction.channel.send(f"✅ Warned {member.display_name}!")
                except discord.errors.Forbidden or discord.HTTPException:
                    return await interaction.response.send_message(f"Logged warning for {member.name}#{member.discriminator}, I could not dm them.")

    @app_commands.command(name='modlogs')
    @commands.has_permissions(manage_messages=True)
    async def modlogs(self, interaction: discord.Interaction, member: discord.Member = None):
        """Shows user logs. Format: @user """
        database = await utilities.connect_database()
        index = 0
        embed = discord.Embed(
            title=f"logs for: ({member.id}) {member.name}#{member.discriminator}", description="___ ___", color=discord.Color.blue())
        if member is not None:
            try:
                async with database.execute('SELECT logid, moderationLogType, moduserid, content, duration FROM moderationLogs WHERE guildid = ? AND userid = ?', (interaction.guild.id, member.id)) as cursor:
                    async for entry in cursor:
                        logid, moderationLogTypes, moduserid, content, duration = entry
                        Moderator = await self.bot.fetch_user(int(moduserid))
                        type = log_converter(moderationLogTypes)
                        if duration == 0:
                            embed.add_field(
                                name=f"**Case {logid}**", value=f"**User:**{member.name}#{member.discriminator}\n**Type:**{type}\n**Admin:**{Moderator.name}#{Moderator.discriminator}\n**Reason:**{content}", inline=False)
                        else:
                            embed.add_field(
                                name=f"**Case {logid}**", value=f"**User:**{member.name}#{member.discriminator}\n**Type:**{type}\n**Admin:**{Moderator.name}#{Moderator.discriminator}\n**Reason:**{content}\n**Duration:**{duration}", inline=False)
            except Exception as e:
                return print(e)
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(2)
        await database.close()

    @app_commands.command(name='delcase')
    @commands.has_permissions(manage_messages=True)
    async def delwarn(self, interaction: discord.Interaction, caseno: int):
        """Delete a case. Format: delcase <id>"""
        if caseno is not None:
            database = await utilities.connect_database()
            await database.execute("DELETE FROM moderationLogs WHERE logid = ?", (int(caseno),))
            await database.commit()
            await asyncio.sleep(2)
            await database.close()
            await interaction.response.send_message(f"✅Deleted {caseno}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(moderation(bot))
