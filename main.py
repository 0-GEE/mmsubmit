from discord.ext import commands
from cogs import *
from dotenv import load_dotenv
import os

def main():
    load_dotenv()
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    sub_fldr_id = os.getenv('SUBMIT_FOLDER')
    guild_id = int(os.getenv('GUILD_ID'))
    mem_role_id = int(os.getenv('MEMBER_ROLE_ID'))
    org_role_id = int(os.getenv('ORG_ROLE_ID'))

    bot = commands.Bot(command_prefix='>?')

    bot.add_cog(Submissions(bot, sub_fldr_id, guild_id, mem_role_id, org_role_id))

    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()