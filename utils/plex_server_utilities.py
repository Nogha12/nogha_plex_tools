import os
from plexapi.server import PlexServer

PLEX_SERVER_BASE_URL = 'http://127.0.0.1:32400'
PLEX_ACESS_TOKEN = 'ifKMozkWsDrzzhPvNoHT'

class PlexInfo:
    def __init__(self):
        self.plex = self.get_plex_host()
        self.last_section = None
        self.last_media = None
    
    def get_plex_host(self):
        return PlexServer(PLEX_SERVER_BASE_URL, PLEX_ACESS_TOKEN)

    def get_plex_info(self, file_path):
        if self.last_section and self.last_media and self.last_media.type == 'show':
            for episode in self.last_media.episodes():
                for part in episode.iterParts():
                    if os.path.basename(part.file) == os.path.basename(file_path):
                        return {
                            'title': episode.title,
                            'season': episode.seasonNumber,
                            'episode': episode.index,
                            'series': self.last_media.title,
                            'originally_available_at': str(episode.originallyAvailableAt),
                            'summary': episode.summary,
                        }
        
        sections = self.plex.library.sections()
        for section in sections:
            for media in section.all():
                if media.type == 'show':
                    for episode in media.episodes():
                        for part in episode.iterParts():
                            if os.path.basename(part.file) == os.path.basename(file_path):
                                self.last_section = section
                                self.last_media = media
                                return {
                                    'title': episode.title,
                                    'season': episode.seasonNumber,
                                    'episode': episode.index,
                                    'series': self.last_media.title,
                                    'originally_available_at': str(episode.originallyAvailableAt),
                                    'summary': episode.summary,
                                }
                elif media.type == 'movie':
                    for part in media.iterParts():
                        if os.path.basename(part.file) == os.path.basename(file_path):
                            self.last_section = section
                            self.last_media = media
                            return {
                                'title': media.title,
                            }
        return None

def plex_update_libraries():
    """Tell the Plex server to update its libraries"""
    plex = PlexServer(PLEX_SERVER_BASE_URL, PLEX_ACESS_TOKEN)
    plex.library.update()
    return