import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import asyncio
from discord.app_commands import Choice
from typing import Optional
import aiosqlite
class applications(commands.Cog):
    """Application handling"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="apply")
    @app_commands.describe(q1="What is your age?",
                           q2="What is your device?",
                           q3="What is your Gaming style? {signle, double, paw, claw}?",
                           q4="What’s your experience in competitive?(what scrims/tournaments have you played in)",
                           q5="what were your past teams?",
                           q6="What is your region? (EU, AS, NA)?",
                           q7=" How active are you on C-OPS (1-10)?",
                           q8="How active are you on discord? (1-10)?",
                           q9="How toxic are you from 1-10 (Be honest)?",
                           q10="Are you able to vc or atleast listen? {yes or no}?",
                           q11="How loyal are you from 1-10?",
                           q12="If you do not make it to comp do you want to be a casual player {yes / no}?",
                           q13="How long have you been playing for?",
                           q14="What is your ign?")
    @app_commands.checks.cooldown(1, 8600)
    async def answer(self, interaction : discord.Interaction, q1:str, q2:str, q3:str, q4:str, q5:str, q6:str, q7:str, q8:str, q9:str, q10:str, q11:str, q12:str, q13:str, q14:str):
        application_chan = self.bot.get_user(521028748829786134)
        await interaction.response.send_message("Sent the application, An overview will be sent to your dms!", ephemeral=True)

        embed = discord.Embed(title="Your application", color = discord.Color.orange())
        embed.add_field(name = "What is your age?:", value= q1, inline=False)
        embed.add_field(name = "What is your device?", value= q2, inline=False)
        embed.add_field(name='What is your Gaming style? {signle, double, paw, claw}?', value=q3, inline=False)
        embed.add_field(name='What’s your experience in competitive?(what scrims/tournaments have you played in)', value=q4, inline=False)
        embed.add_field(name='what were your past teams?', value=q5, inline=False)



        embed.add_field(name="What is your region? (EU, AS, NA)?", value=q6, inline=False)
        embed.add_field(name = "How active are you on C-OPS (1-10)?", value = q7, inline=False)
        embed.add_field(name="How active are you on discord? (1-10)?", value=q8, inline=False)
        embed.add_field(name="How toxic are you from 1-10 (Be honest)?", value=q9, inline=False)
        embed.add_field(name="Are you able to vc or atleast listen? {yes or no}?", value=q10, inline=False)
        embed.add_field(name="How loyal are you from 1-10?", value=q11, inline=False)
        embed.add_field(name="If you do not make it to comp do you want to be a casual player {yes / no}?", value=q12, inline=False)
        embed.add_field(name="How long have you been playing for?", value=q13, inline=False)
        embed.add_field(name="What is your ign?", value=q14, inline=False)
        await interaction.user.send(embed=embed)

                    
        try:
            appdb = sqlite3.connect("./applications/applications.db")
            appdb.execute("CREATE TABLE IF NOT EXISTS applications (userid int, q1 int, q2 text, q3 text, q4 text, q5 int, q6 int, q7 int, q8 text, q9 int, q10 text, q11 text, q12 text, q13 text, q14 text)")
            appdb.execute('INSERT OR IGNORE INTO applications (userid, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (interaction.user.id, q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14,))
            appdb.commit()
            appdb.close()
            await application_chan.send(f"@here new application from {interaction.user.mention}! use /review {interaction.user.mention} to review it!")
        except ConnectionError :
            pass
        except Exception as e:
            await interaction.user.send(f"Sorry I encountered an error while saving your application. If this happens multiple times please dm Senpai_Desi#4108 with the following information: \n `Exception occured in application fron {interaction.user.name}#{interaction.user.discriminator} {e}`` ")

        
    @app_commands.command(name="view")
    async def view(self, interaction : discord.Interaction, member : discord.Member):
        if interaction.user.id != 759839292884910111 or 521028748829786134:
            return await interaction.response.send_message("You are not authorized to view this.", ephemeral=True)
        appdb = await aiosqlite.connect("./applications/applications.db")
        async with appdb.execute('SELECT q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14 FROM applications WHERE userid = ?', (member.id,)) as cursor:
            async for entry in cursor:
                q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12, q13, q14= entry

                embed = discord.Embed(title='Applications', color = discord.Color.gold())
                embed.add_field(name=f"Showing Application from **{member.id}**", value="use /accept or /deny with reason to acept or deny!")
                embed.add_field(name = "What is your age?:", value= q1, inline=False)
                embed.add_field(name = "What is your device?", value= q2, inline=False)
                embed.add_field(name='What is your Gaming style? {signle, double, paw, claw}?', value=q3, inline=False)
                embed.add_field(name='What’s your experience in competitive?(what scrims/tournaments have you played in)', value=q4, inline=False)
                embed.add_field(name='what were your past teams?', value=q5, inline=False)
                embed.add_field(name="What is your region? (EU, AS, NA)?", value=q6, inline=False)
                embed.add_field(name = "How active are you on C-OPS (1-10)?", value = q7, inline=False)
                embed.add_field(name="How active are you on discord? (1-10)?", value=q8, inline=False)
                embed.add_field(name="How toxic are you from 1-10 (Be honest)?", value=q9, inline=False)
                embed.add_field(name="Are you able to vc or atleast listen? {yes or no}?", value=q10, inline=False)
                embed.add_field(name="How loyal are you from 1-10?", value=q11, inline=False)
                embed.add_field(name="If you do not make it to comp do you want to be a casual player {yes / no}?", value=q12, inline=False)
                embed.add_field(name="How long have you been playing for?", value=q13, inline=False)
                embed.add_field(name="What is your ign?", value=q14, inline=False)
                await interaction.response.send_message(embed=embed)
        try:
            await appdb.close()
        except ValueError:
            pass


    @app_commands.command(name="accept")
    async def accept(self, interaction : discord.Interaction, memberid : str, reason : Optional[str]):
        member = self.bot.get_user(int(memberid))
        if reason is not None:
            await member.send(f"Hello {member.mention}! I am glad to inform you that you have been accepted into Zephyr! Congratulations. Reason for this being {reason}")
        else:
            await member.send(f"Hello {member.mention}! I am glad to inform you that you have been accepted into Zephyr! Congratulations")
        await interaction.response.send_message("Done", ephemeral=True)

    @app_commands.command(name="deny")
    async def deny(self, interaction : discord.Interaction, memberid : str, reason : Optional[str]):
        db = await aiosqlite.connect("./applications/applications.db")
        member = self.bot.get_user(int(memberid))
        if reason is not None:    
            await member.send(f"Hey, Unfortunately your application got denied with the reason : **{reason}**\nYour stored application got removed. You are always welcome to re apply!")
        else:
            await member.send(f"Hey, Unfortunately your application got denied.\nYour stored application got removed. You are always welcome to re apply!")

        await db.execute("DELETE FROM applications WHERE userid = ?", (memberid,))
        await db.commit()
        try:
            await db.close()
        except ValueError:
            pass
        await interaction.response.send_message("Done, Informed user and deleted their entry.")
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(applications(bot))
