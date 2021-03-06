from helpers import *
from discord.ext import commands
from discord.ext.commands import Context
import discord
from discord.ext.commands.bot import Bot
from discord.message import Message
from googleapiclient.discovery import build, MediaFileUpload
from zipfile import BadZipFile, ZipFile
import os
from metaclass import *
import json
from datetime import datetime

# some emote constants to indicate submission success or failure
OK = ":white_check_mark:"
NG = ":x:"



class Submissions(commands.Cog):
    def __init__(self, bot: Bot, sub_fldr_id: str, 
                 guild_id: int, mem_role_id: int,
                 org_role_id: int):
                 
        self.bot = bot
        self.folder_id = sub_fldr_id
        self.parent_guild_id = guild_id
        self.scopes = [
            'https://www.googleapis.com/auth/drive.file', 
            'https://www.googleapis.com/auth/drive.install']
        self.partic_role_id = mem_role_id
        self.org_role_id = org_role_id
        self.configured = False

        # load configurations from file or set all configs to None
        #  if configs do not exist (configs must be set via command
        #   before using the submission system in this case)
        configs = load_configs()

        self.song_title = configs.get('song_title', None)
        self.song_artist = configs.get('song_artist', None)
        self.useful_tags = configs.get('useful_tags', None)
        self.submission_id = configs.get('submission_id', 0)

        try:
            self.deadline = datetime.fromisoformat(configs.get('deadline', None))
        except:
            self.deadline = None

        self.check_config()

        self.folder_name = "MasterMapper Submissions"
        self.submission_history = "sub_history.json"


    @commands.Cog.listener()
    async def on_ready(self):
        print("Online!")


    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        """this method handles user submissions."""

        if msg.author == self.bot.user or \
            not isinstance(msg.channel, discord.DMChannel):
            return

        if len(msg.attachments) != 1 or \
            not self.configured:
            return


        # ensure user is a participant
        guild = await self.bot.fetch_guild(self.parent_guild_id)
        partic_role = guild.get_role(self.partic_role_id)

        user = await guild.fetch_member(msg.author.id)


        if partic_role not in user.roles:
            await msg.channel.send(NG+" You are not a registered participant.")
            return

        # check to see if the deadline has already passed
        curr_time = datetime.utcnow()

        if self.deadline < curr_time:
            await msg.channel.send(NG+"The deadline has passed! You cannot submit past the deadline.")
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
        if self.song_title:
            if mtdata.title not in self.song_title:
                await msg.channel.send(
                    NG+" Song title mismatch. Are you submitting the correct beatmap?")
                clean_dir(fdir=fdir)
                return
        
        if mtdata.artist not in self.song_artist:
            await msg.channel.send(
                NG+" Song artist mismatch. Are you submitting the correct beatmap?")
            clean_dir(fdir=fdir)
            return

        # anonymize the entry by replacing the original value in the 'creator' field
        #  of the beatmap metadata with string of the format: {Adjective} + {Noun}
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
                
        # form the string representing the name mapping and
        #  store it in a text document to be read from 
        #  when the mappings need to be retrieved for 
        #  contest results
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
        normalized_tags = [tag.casefold() for tag in mtdata.tags]
        
        for tag in self.useful_tags:
            if tag.casefold() not in normalized_tags:
                mtdata.tags.append(tag.casefold())

        mtdata.write()

        # rename the .osu file and map pkg as well for total anonymization
        sub_name = 'submission_{0}'.format(self.submission_id)

        os.rename(map_path, fdir+'/{0}.osu'.format(sub_name))
        os.rename(fdir, sub_name)

        # validation finished. Now re-zip
        with ZipFile(sub_name+'.zip', 'w') as zf:
            for foldername, subfolders, filenames in os.walk(sub_name):
                for filename in filenames:
                    filepath = os.path.join(foldername, filename)
                    zf.write(filepath, os.path.basename(filepath))

        oszname = sub_name+'.osz'
        os.rename(sub_name+'.zip', oszname)
        clean_dir(fdir=sub_name)


        # now we check to see if the user has submitted during this round
        #  before
        prev_submission = None # this will be a file id if found
        history = None
        userid_str = str(msg.author.id)

        # check if a record of submission history exists
        if os.path.exists(self.submission_history):
            with open(self.submission_history, 'r', encoding='utf-8') as f:
                history = json.load(f)
                f.close()

            user_history = history.get(userid_str, [])
            if len(user_history) != 0:
                # a previous submission has been found
                prev_submission = user_history[-1]

        # prepare to upload to Google Drive
        #  by optaining authorization credentials
        creds = get_creds_server(self.scopes)
        service = build('drive', 'v3', credentials=creds)
        
        # delete the previous submission from the submissions folder
        #  on Drive
        if prev_submission:
            service.files().delete(fileId=prev_submission).execute()

            # remove previous submission name mappings for the current user
            #  and free up the user's old aliases from the used names list
            mappings = open("name mappings.txt", 'r').readlines()
            old_aliases = []

            for i, mapping in enumerate(mappings):
                if old_creator_name in mapping and mtdata.creator not in mapping:
                    old_aliases.append(mappings.pop(i).split(' --> ')[1])

            with open("name mappings.txt", 'w') as f:
                f.write(''.join(mappings))
                f.close()

            used_names = open(namelist, 'r').readlines()
            for old_alias in old_aliases:
                try:
                    used_names.remove(old_alias)
                except ValueError:
                    continue
            
            with open(namelist, 'w') as f:
                f.write(''.join(used_names))
                f.close()

        file_metadata = {
            'name': oszname,
            'parents': [self.folder_id]
            }

        # upload new submission to the submissions folder
        media = MediaFileUpload(oszname, resumable=True)
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id').execute()
        file_id = file.get('id')

        service.close()

        # update or create the submission history JSON
        if history:
            user_history = history.get(userid_str, [])
            user_history.append(file_id)
            history[userid_str] = user_history
        else:
            history = { userid_str: [file_id] }
        
        with open(self.submission_history, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)
            f.close()

        # submission was successful. Send confirmation msg
        await msg.channel.send(
            OK+" Your submission has been received! Submission id: {0}".format(self.submission_id))

        self.submission_id += 1

        # write new submission id to config file
        configs = load_configs()
        configs['submission_id'] = self.submission_id
        save_configs(configs)


    def check_config(self):
        """utility method for checking to see if any configs
        are not set (ie. have a value of ``None``)
        and setting the ``configured`` flag accordingly
        """

        cfg_list = [
            self.song_artist,
            self.useful_tags,
            self.deadline
        ]

        if None in cfg_list:
            self.configured = False
        else:
            self.configured = True


    @commands.command(name='set_title')
    async def set_title(self, ctx: Context, *args):
        """changes the song titles that the submission system checks for.
        It changes the corresponding class attribute and writes to config file.
        """

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        if len(args) == 0:
            await ctx.send("Please specify the new song titles and try again!")
            return

        
        new_titles = list(args)
        self.song_title = new_titles

        # save the new title into config file
        configs = load_configs()

        configs['song_title'] = new_titles
        save_configs(configs)

        self.check_config()

        await ctx.send("Song titles changed to ``{0}``!".format(', '.join(new_titles)))


    @commands.command(name='clear_title')
    async def clear_title(self, ctx: Context):
        """clears any title check (basically allows the system to accept
        any song title)
        """

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        self.song_title = None
        self.check_config()

        configs = load_configs()
        configs['song_title'] = None
        save_configs(configs)

        await ctx.send("Successfully removed song title restriction!")



    @commands.command(name='title')
    async def title(self, ctx: Context):
        """Outputs the song title currently set for the submission
        system to check for
        """
        if command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            if self.song_title:
                await ctx.send(', '.join(self.song_title))
            else:
                await ctx.send("No song title restriction in place.")

        
        

    @commands.command(name='set_artist')
    async def set_artist(self, ctx: Context, *args):
        """changes the song artist that the submission system checks for.
        It changes the corresponding class attribute and writes to config file.
        """

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        if len(args) == 0:
            await ctx.send("Please specify the new song artists and try again!")
            return

         # take all artists given (those with spaces in name can be delimited with double quote)
        new_artists = list(args)
        self.song_artist = new_artists

        configs = load_configs()
        
        # save new artist into config file
        configs['song_artist'] = new_artists
        save_configs(configs)

        self.check_config()

        await ctx.send("Song artists changed to ``{0}``!".format(', '.join(new_artists)))


    @commands.command(name='artist')
    async def artist(self, ctx: Context):
        """Outputs the song artists currently set for the submission system to
        look for
        """

        if command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            if self.song_artist:
                await ctx.send(', '.join(self.song_artist))
            else:
                await ctx.send("No song artists set")



    @commands.command(name='add_tags')
    async def add_tags(self, ctx: Context, *args):
        """adds tags to the internal useful tags list
        (modifies class attribute and writes to config file)
        """

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        if self.useful_tags: # the useful tags list does exist
            for tag in args:
                if tag not in self.useful_tags: 
                    self.useful_tags.append(tag) # add all arg tags into the list
        else:
            # useful tags list does not exist yet. Simply set it to 
            #  the list created from args
            self.useful_tags = list(args)

        # write new tags to config file
        configs = load_configs()
        configs['useful_tags'] = self.useful_tags
        save_configs(configs)

        self.check_config()

        await ctx.send(
            "Successfully added the following tags to internal tags list:\n ``{0}``".format(
                ', '.join(args)
            ))


    @commands.command(name='remove_tags')
    async def remove_tags(self, ctx: Context, *args):
        """removes tags from the internal useful tags list
        (modifies class attribute and writes to config file)
        """

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        if len(args) == 0:
            await ctx.send("Please specify tags to remove and try again!")
            return

        # check if there are any tags at all
        if self.useful_tags is None:
            await ctx.send("There is no internal tags list yet!")
            return

        if len(self.useful_tags) == 0:
            await ctx.send("The internal tags list is already empty!")
            return

        removed_tags = [] # store all removed tags for response msg
        for remove_tag in args:
            if remove_tag in self.useful_tags:
                self.useful_tags.remove(remove_tag)
                removed_tags.append(remove_tag)

        # write new tags to config file
        configs = load_configs()
        configs['useful_tags'] = self.useful_tags
        save_configs(configs)

        self.check_config()

        await ctx.send(
            "Successfully removed the following tags from internal tags list:\n ``{0}``".format(
                ', '.join(removed_tags)
            ))


    @commands.command(name='clear_tags')
    async def clear_tags(self, ctx: Context):
        """deletes all tags in the internal tags list"""

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        if self.useful_tags is None:
            await ctx.send("No tags list to remove from")
            return

        self.useful_tags = []

        configs = load_configs()
        configs['useful_tags'] = self.useful_tags
        save_configs(configs)

        self.check_config()

        await ctx.send("Successfully removed all tags from internal tags list")


    @commands.command(name='tags')
    async def tags(self, ctx: Context):
        """Outputs all tags in the internal tags list
        """

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        
        if self.useful_tags is None:
            await ctx.send("There is no internal tags list at the moment")
            return

        if len(self.useful_tags) == 0:
            await ctx.send("The internal tags list is empty")
            return

        await ctx.send(
            "``{0}``".format(', '.join(self.useful_tags))
        )

    
    @commands.command(name='set_deadline')
    async def set_deadline(self, ctx: Context, *args):
        """sets the submission deadline
        (modifies class attribute and writes to config file)"""

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        # see if the user has passed an appropriate iso format string
        try:
            new_deadline = datetime.fromisoformat(args[0])
        except Exception as e:
            await ctx.send(
                "Your deadline could not be parsed. Please check your formatting and try again ({0})".format(
                    str(e)
                ))
            return

        # datetime object created successfully. Now add it to attributes
        self.deadline = new_deadline
        new_deadline_str = new_deadline.isoformat()

        # save deadline (in string form) to config file
        configs = load_configs()

        # reformat using isoformat() to ensure no possibility of errors
        #  when retrieving deadline from config file in the future
        configs['deadline'] = new_deadline_str
        save_configs(configs)

        self.check_config()

        await ctx.send("Successfully updated the submission deadline to ``{0}``".format(
            new_deadline_str
        ))



    @commands.command(name='deadline')
    async def get_deadline(self, ctx: Context):
        """Outputs the deadline currently set internally
        """

        if command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            if self.deadline:
                await ctx.send(self.deadline.isoformat())
            else:
                await ctx.send("No deadline set")


    @commands.command(name='configured')
    async def is_configured(self, ctx: Context):
        """outputs the configured status"""

        if command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            await ctx.send(str(self.configured))


    @commands.command(name='names')
    async def fetch_name_mappings(self, ctx: Context):
        """sends the name mappings text document"""

        if not command_authorized(ctx, self.parent_guild_id, self.org_role_id):
            return

        # check to see if the name mappings file actually exists
        if not os.path.exists("name mappings.txt"):
            await ctx.send(
                "The name mappings file does not exist yet! Maybe no one has submitted anything yet?")
            return

        # create discord file object in preparation for sending
        name_file = discord.File("name mappings.txt")
        
        # prepare DM with the user invoking the command
        dm = ctx.author.dm_channel

        if dm is None:
            dm = await ctx.author.create_dm()

        # send the dm with the name mappings file attached
        await dm.send(file=name_file)
        