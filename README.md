# MasterMapper Submission System

This is an automated submission handler created for the [osu!MasterMapper beatmapping contest](https://osu.ppy.sh/community/forums/topics/1495284?n=1) which manifests as a Discord bot. Upon receiving a submission, the system first checks the submission context (submissions are only accepted through DM Channels). Then, it ensures that the submitting user is a valid contest participant and that the submission message contains exactly one (1) file attachment. It then verifies that the file is a valid osu! beatmap package before parsing the beatmap contained within and verifying that its metadata is correct. Then, the submission anonymizes the submission system by modifying the ``creator`` field of the beatmap's metadata along with the file names. Lastly, it records the true creator name and alias mappings into a file and uploads the submission to a dedicated folder on Google Drive.  

The submission system offers several utility commands to configure it as the contest progresses:
1. ``set_title {title1 title2 ...}`` sets the song titles that the system will check submission song titles against in the validation process. Simply replace ``{title1 title2 ...}`` with the desired song titles delimited by whitespace when invoking this command. If any title has a space within it, wrap the entire title in double quotes. 
2. ``clear_title`` changes the submission system's checking mode to allow any song titles to pass. It takes no arguments.
3. ``title`` retrieves the song titles list which the submission system is currently checking submission titles against. It takes no arguments.
4. ``set_artist {artist1 artist2 ...}`` sets the song artists that the system will check submission song artists against in the validation process. Simply replace ``{artist1 artist2 ...}`` with the desired song artists delimited by whitespace when invoking this command. If any artist name has a space within it, wrap the entire name in double quotes.
5. ``artist`` retrieves the song artists list which the submission system is currently checking submission artists against. It takes no arguments.
6. ``add_tags {tag1 tag2 ...}`` adds tags of your choice to the tags which are automatically added to submission metadata (if they do not exist already). Simply replace ``{tag1 tag2 ...}`` with the desired tag words delimited by whitespace when invoking this command.
7. ``remove_tags {tag1 tag2 ...}`` removes tags of your choice from the tags which are automatically added to submission metadata (if they exist). Simple replace ``{tag1 tag2 ...}`` with the desired tag words delimited by whitespace when invoking this command.
8. ``clear_tags`` removes all tags from the list of tags which are automatically added to submission metadata. It takes no arguments.
9. ``tags`` retrieves all tags which are automatically being added to submission metadata. It takes no arguments.
10. ``set_deadline {deadline}`` sets the deadline that the system will check submission times against. ``{deadline}`` must be replaced with a _valid ISO format date string_ (format: YYYY-MM-DD) (example: 2022-02-20)
11. ``deadline`` retrieves the deadline that the system is currently checking submission times against. It takes no arguments.
12. ``configured`` tells you whether or not the submission system considers itself to be properly configured for operation. The submission system will accept submissions if and only if this command produces ``True``. It takes no arguments.
13. ``names`` retrieves the submitting usernames-to-alias mappings in the form of a text document. It takes no arguments.


As MasterMapper Submission System was created for the exclusive use of the [osu!MasterMapper beatmapping contest](https://osu.ppy.sh/community/forums/topics/1495284?n=1), it cannot be invited to any other guilds (servers).