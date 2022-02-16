from discord.ext import commands
from cogs import *
from dotenv import load_dotenv
import os

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='>?')

bot.add_cog(Submissions(bot))

bot.run(DISCORD_TOKEN)