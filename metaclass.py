SEP = ':'

class BeatmapMetadata:
    """
    This class represents an osu! beatmap's metadata.
    It does not represent any other component of the beatmap.

    It contains methods for fetching any metadata field, and 
    writing to any metadata field.
    """

    def __init__(self, map_path: str):
        self._path = map_path
        self._beatmap_data = open(self._path, 'r').readlines()

        # determine the line numbers for metadata section
        self._meta_line = self._get_line('[Metadata]')
        self._difficulty_line = self._get_line('[Difficulty]')

        # build the list of metadata lines
        meta_list = self._beatmap_data[self._meta_line:self._difficulty_line-1]

        # this looks very ugly but it's a necessary evil to make accessing 
        #  metadata fields easier when using this class as a client
        self.title = meta_list[1].split(SEP)[1].strip('\n')
        self.title_unicode = meta_list[2].split(SEP)[1].strip('\n')
        self.artist = meta_list[3].split(SEP)[1].strip('\n')
        self.artist_unicode = meta_list[4].split(SEP)[1].strip('\n')
        self.creator = meta_list[5].split(SEP)[1].strip('\n')
        self.version = meta_list[6].split(SEP)[1].strip('\n')
        self.source = meta_list[7].split(SEP)[1].strip('\n')
        self.tags = meta_list[8].split(SEP)[1].strip('\n').split(' ')
        self.beatmap_id = int(meta_list[9].split(SEP)[1].strip('\n'))
        self.beatmapset_id = int(meta_list[10].split(SEP)[1].strip('\n'))

    

    def _get_line(self, phrase: str):
        """returns the start line for a beatmap data category ``phrase``"""
        for num, line in enumerate(self._beatmap_data, 0):
            if phrase in line:
                return num

    def write(self):
        """
        write any new/modified metadata into the beatmap
        (replaces original values)
        """
        before = '\n'.join(self._beatmap_data[0:self._meta_line-1])
        after = '\n'.join(self._beatmap_data[self._difficulty_line:-1])
        
        # form metadata string
        mtdata_str = \
            "\n[Metadata]" + \
            "\nTitle:" + self.title + \
            "\nTitleUnicode:" + self.title_unicode + \
            "\nArtist:" + self.artist + \
            "\nArtistUnicode:" + self.artist_unicode + \
            "\nCreator:" + self.creator + \
            "\nVersion:" + self.version + \
            "\nSource:" + self.source + \
            "\nTags:" + ' '.join(self.tags) + \
            "\nBeatmapID:" + str(self.beatmap_id) + \
            "\nBeatmapSetID:" + str(self.beatmapset_id) + \
            "\n\n"

        with open(self._path, 'w') as f:
            f.write(before)
            f.close()

        with open(self._path, 'a') as f:
            f.write(mtdata_str)
            f.write(after)
            f.close()