from dataclasses import dataclass
from pathlib import Path
import os
import requests
import re

env_file = Path('./edge/.env.local')
if env_file.exists():
    env = {e[0]: e[1] for e in (line.split('=') for line in env_file.read_text().splitlines() if line)}
else:
    env = dict(os.environ)


type_video = dict[str, str|list[str]]
type_collection = dict[str, str|list[type_video]]
@dataclass
class SideBarItem:
    url: str
    name: str
    def html(self) -> str:
        return f'<li><a href="{self.url}">{self.name}</a></li>'
    @staticmethod
    def from_tuple(input: tuple[str, str]):
        return SideBarItem(name=input[0], url=input[1])

class SideBarItems:
    def __init__(self, items: list[SideBarItem]):
        self.items = [item for item in items]
    def append(self, item: SideBarItem):
        self.items.append(item)
    def html(self):
        return '\n'.join(
            [item.html() for item in self.items]
        )
    @staticmethod
    def from_list(input: list[tuple[str, str]]):
        return SideBarItems((
            SideBarItem.from_tuple(item) for item in input
        ))
    
@dataclass
class DownBarItem:
    url: str
    name: str
    def html(self) -> str:
        if not self.url:
            return f'<div><p>{self.name}</p></div>'
        return f'<div><p><a href="{self.url}">{self.name}</a></p></div>'
    @staticmethod
    def from_tuple(input: tuple[str, str]):
        return DownBarItem(name=input[0], url=input[1])

class DownBarItems:
    def __init__(self, items: list[DownBarItem]):
        self.items = [item for item in items]
    def append(self, item: DownBarItem):
        self.items.append(item)
    def html(self):
        return '\n'.join(
            [item.html() for item in self.items]
        )
    @staticmethod
    def from_list(input: list[tuple[str, str]]):
        return DownBarItems((
            DownBarItem.from_tuple(item) for item in input
        ))

def clear_directory(dir_path):
    p = Path(dir_path)
    for item in p.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            clear_directory(item)
            item.rmdir()
                

def get_collections():
    url = f"https://video.bunnycdn.com/library/{env['LibraryID']}/collections?page=1&itemsPerPage=100&orderBy=date&includeThumbnails=true"

    response = requests.get(url, headers={
        "accept": "application/json",
        "AccessKey": env['AccessKey']
    })
    return response.json()

def get_videos(collection_id):
    url = f"https://video.bunnycdn.com/library/{env['LibraryID']}/videos?page=1&itemsPerPage=100&orderBy=date"
    url += '&collection=' + collection_id

    response = requests.get(url, headers={
        "accept": "application/json",
        "AccessKey": env['AccessKey']
    })
    return response.json()


def parse_groups(text):
    """
    Parses tags from text. 
    A valid tag:
      - starts with '#'
      - contains exactly one '.'
      - ends with newline or end of string
      - can contain spaces
    """
    pattern = r'#([^#\n]*\.[^#\n]*)(?:\n|$)'
    matches: list[str] = re.findall(pattern, text)
    
    # filter tags that contain exactly one dot
    tags = [tag.strip() for tag in matches if tag.count('.') == 1]
    return tags

def replace_all(_in: str, keys: dict[str, str]) -> str:
    text = _in
    for k, v in keys.items():
        text = text.replace(k, v)
    return text

def get_by_name(_in: list[dict[str, str]], property: tuple[str, str], default=None):
    for el in _in:
        if el.get(property[0]) == property[1]:
            return el
    return default

def get_collections_playlists():
    COLLECTIONS: list[type_collection] = []
    PLAYLISTS: dict[str, dict[str, type_video]] = {}
    for col in get_collections()['items']:
        # read items.(guid, name, videoCount); add items.(previewImageUrl)
        new_collection: dict[str, str|list] =  {
            'name': col['name'],
            'guid': col['guid'],
            'videoCount': col['videoCount'],
            'previewImageUrl': (col['previewImageUrls'] or ['./media/no_image.svg'])[0],
            'videos': []
        }
        # print(get_videos(col['guid']))
        for vid in get_videos(col['guid'])['items']:
            new_video = {
                'name': vid['title'],
                'guid': vid['guid'],
                'length': vid['length'],
                'previewImageUrl': f'https://{env["CDNHostname"]}/{vid["guid"]}/{vid["thumbnailFileName"]}',
                'embedUrl':  f'https://{env["VideoHostName"]}/embed/{env["LibraryID"]}/{vid["guid"]}{env["QueryParams"]}',
                'description': 
                    f"<h2>{vid['title']}</h2>\n" +\
                    get_by_name(vid['metaTags'], ('property', 'description'), default={}).get('value', '') +\
                    f'\n#All Videos.{new_collection["name"]}',
                'groups': []
            }
            new_video['groups'] = parse_groups(new_video['description'])
            for group in new_video['groups']:
                if PLAYLISTS.get(group) is None:
                    PLAYLISTS[group] = {}
                video_name = new_video['name']
                if video_name in PLAYLISTS[group]:
                    i = 1
                    while f'({i}){video_name}' in PLAYLISTS[group]:
                        i += 1
                    video_name = f'({i}){video_name}'
                PLAYLISTS[group][video_name] = new_video
            new_collection['videos'].append(new_video)
        COLLECTIONS.append(new_collection)
    return COLLECTIONS, PLAYLISTS

# prepare out
out_dir = Path('./out-html-v2')
src_dir = Path('./src-html-v2')
clear_directory(out_dir)
(out_dir/'media').mkdir()

# make it!
COLLECTIONS, PLAYLISTS = get_collections_playlists()

init_page = (src_dir/'index.html').read_text()
init_video = (src_dir/'init_video.txt').read_text().strip()
init_video_playlist, init_video_name = init_video.split('\n')
init_video_obj = PLAYLISTS[init_video_playlist][init_video_name]

formatted_init_page = replace_all(init_page,
    {
        '{title}': "Video Viewer",
        '{phrase_up}': "Upper Phrase",
        '{phrase_down}': "Bottom Phrase",
        '{init_video.link}': init_video_obj['embedUrl'],
        '{init_video.description}': init_video_obj['description'],
        '{init_video.source}': init_video_playlist,
        '{side_bar_items}': SideBarItems.from_list([
                ("Home", "./"),
                ("Content1", "#"),
                ("All Videos", "#")
            ]).html(),
        '{down_bar_items}': DownBarItems.from_list([
                ("Content1", "#"),
                ("Content2", "#"),
                ("Content3", "#"),
                ("Content4", "#"),
                ("Content5", "#"),
                ("Content6", "#"),
                ("Content7", "#"),
                ("Shonot", "#"),
            ]).html(),
    }
)
(out_dir/'index.html').write_text(formatted_init_page)


init_styles = (src_dir/'styles.css').read_text()
(out_dir/'styles.css').write_text(init_styles)


(out_dir/'media'/'no_image.svg').write_bytes(
    (src_dir/'no_image.svg').read_bytes()
)