from http.client import HTTPException

from matplotlib.pyplot import close
from helpers import *
from discord.channel import TextChannel
from discord.colour import Color
from discord.embeds import Embed
from discord.ext import commands
import discord
from discord.ext.commands.bot import Bot
from discord.ext.commands.context import Context
from discord.guild import Guild
from discord.member import Member
from discord.message import Message
from discord.permissions import PermissionOverwrite
from discord.role import Role
from loguru import logger
import traceback
from google.auth.transport import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource, MediaFileUpload
from googleapiclient.errors import HttpError
from typing import *
from zipfile import BadZipFile, ZipFile
import os
from metaclass import *


OK = ":white_check_mark:"
NG = ":x:"



class Submissions(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.parent_guild_id = 797228377442353182
        self.scopes = [
            'https://www.googleapis.com/auth/drive.file', 
            'https://www.googleapis.com/auth/drive.install']
        self.partic_role_id = 797389869655523398
        self.song_title = 'Epistrofi'
        self.song_artist = 'SEPHID'
        self.useful_tags = \
            "MasterMapper 2022 MM22 #2 Qualifiers QF Electronic Instrumental English Vocal Chop".split(' ')
        self.submission_id = 1
        self.folder_name = "MasterMapper Submissions"


    @commands.Cog.listener()
    @logger.catch
    async def on_ready(self):
        print("Online!")


    @commands.Cog.listener()
    @logger.catch
    async def on_message(self, msg: Message):
        """this method handles user submissions."""

        if msg.author == self.bot.user or \
            not isinstance(msg.channel, discord.DMChannel):
            return

        if len(msg.attachments) != 1:
            return


        # ensure user is a participant
        guild = await self.bot.fetch_guild(self.parent_guild_id)
        partic_role: Role = guild.get_role(self.partic_role_id)

        user: Member = await guild.fetch_member(msg.author.id)


        if partic_role not in user.roles:
            await msg.channel.send(NG+" You are not a registered participant.")
            return

        # do a simple check on the attachment to see if it is osz
        map_pkg = msg.attachments[0]
        
        if not map_pkg.filename.endswith('.osz'):
            print("not osz file")
            return

        await msg.channel.trigger_typing()

        # user and msg have been validated. Now download the beatmap package
        fname = "_{0}_submission.zip".format(user.id)
        fdir = "_{0}_submission".format(user.id)
        await map_pkg.save(fname)

        # extract the beatmap package contents in preparation for map validation
        #   and anonymization
        try:
            with ZipFile(fname, 'r') as zf:
                zf.extractall(fdir)
            clean_dir(fname=fname)

        except BadZipFile:
            await msg.channel.send(NG+" Please submit an actual beatmap package.")
            clean_dir(fname=fname, fdir=fdir)
            return

        except:
            await msg.channel.send(NG+" An error occurred. Please try again!")
            clean_dir(fname=fname, fdir=fdir)
            return


        # scan the map directory
        osu_files = [file for file in os.listdir(fdir) if file.endswith(".osu")]

        # reject the submission if there exist multiple or no .osu files
        mapcount = len(osu_files)
        if mapcount != 1:
            await msg.channel.send(
                NG+" Your submission must contain exactly one (1) .osu file. Found {0}.".format(
                    mapcount
                ))
            clean_dir(fdir=fdir)
            return

        # parse beatmap metadata
        map_filename = osu_files[0]
        map_path = fdir + '/' + map_filename

        mtdata = BeatmapMetadata(map_path)

        # check to see if the submission has an online beatmapset id
        #  and reject if it does
        if mtdata.beatmapset_id != -1:
            await msg.channel.send(
                NG+" You cannot submit work which has been uploaded to the osu! website.")
            clean_dir(fdir=fdir)
            return

        # check basic metadata    
        if mtdata.title != self.song_title:
            await msg.channel.send(
                NG+" Song title mismatch. Are you submitting the correct beatmap?")
            clean_dir(fdir=fdir)
            return
        
        if mtdata.artist != self.song_artist:
            await msg.channel.send(
                NG+" Song artist mismatch. Are you submitting the correct beatmap?")
            clean_dir(fdir=fdir)
            return

        # anonymize the entry
        old_creator_name = str(mtdata.creator)
        mtdata.creator = generate_rand_diffname()
        namelist = 'used_names.txt'

        # check to see if generated name was used already
        #  and keep generating new ones until we get an unused name
        if os.path.exists(namelist):
            used_names = open(namelist, 'r').readlines()
            while mtdata.creator in used_names:
                mtdata.creator = generate_rand_diffname()
            with open(namelist, 'a') as f:
                f.write('\n'+mtdata.creator)
                f.close()
            
        else:
            with open(namelist, 'w') as f:
                f.write(mtdata.creator)
                f.close()

        indicator = old_creator_name + " --> " + mtdata.creator + '\n'

        if os.path.exists("name mappings.txt"):
            with open("name mappings.txt", 'a') as f:
                f.write(indicator)
                f.close()
        else:
            with open("name mappings.txt", 'w') as f:
                f.write(indicator)
                f.close()

        # add some potentially useful tags (if they don't exist already)
        for tag in self.useful_tags:
            if tag not in mtdata.tags:
                mtdata.tags.append(tag.casefold())

        mtdata.write()

        # rename the .osu file and map pkg as well for anonymization
        sub_name = 'submission_{0}'.format(self.submission_id)

        os.rename(map_path, fdir+'/{0}.osu'.format(sub_name))
        os.rename(fdir, sub_name)
        self.submission_id += 1

        # validation finished. Now re-zip
        with ZipFile(sub_name+'.zip', 'w') as zf:
            for foldername, subfolders, filenames in os.walk(sub_name):
                for filename in filenames:
                    filepath = os.path.join(foldername, filename)
                    zf.write(filepath, os.path.basename(filepath))

        oszname = sub_name+'.osz'
        os.rename(sub_name+'.zip', oszname)
        clean_dir(fdir=sub_name)

        # upload to Google Drive
        creds = get_creds(self.scopes)
        service: Resource = build('drive', 'v3', credentials=creds)

        folder_id = None

        # check if folder exists first
        page_token = None
        while folder_id is None:
            response: dict = service.files().list(q="mimeType='application/vnd.google-apps.folder'",
                                                  spaces="drive",
                                                  fields="nextPageToken, files(id, name)",
                                                  pageToken=page_token).execute()
            for file in response.get('files', []):
                if file.get('name') == self.folder_name:
                    folder_id = file.get('id')
                    break
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        if folder_id is None:
            # folder not found, so create it
            folder_metadata = {
                'name': self.folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            fldr: dict = service.files().create(body=folder_metadata,
                                                fields='id').execute()
            folder_id = fldr.get('id')

        

        file_metadata = {
            'name': oszname,
            'parents': [folder_id]
            }

        media = MediaFileUpload(oszname, resumable=True)
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id').execute()

        service.close()


        await msg.channel.send(
            OK+" Your submission has been received! Submission id: {0}".format(self.submission_id))