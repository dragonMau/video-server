from dataclasses import dataclass
from pathlib import Path
import os
import requests
import re
import sys
import hashlib
import json

env_file = Path('./edge/.env.local')
if env_file.exists():
    env = {e[0]: e[1] for e in (line.split('=') for line in env_file.read_text().splitlines() if line)}
else:
    env = dict(os.environ)

type_video = dict[str, str|list[str]]
type_collection = dict[str, str|list[type_video]]

OFFLINE_MODE = "--offline" in sys.argv
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
def _make_cache_filename(url, params):
    """
    Build a filename based on the URL and params.
    """
    key = url
    if params:
        # Create a deterministic string from params
        param_items = sorted(params.items())
        key += json.dumps(param_items)
    # Hash the key for filesystem safety
    hashed = hashlib.sha256(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{hashed}.json")
def get_request(url, **kwargs):
    """
    A wrapper around requests.get which supports offline mode.
    """
    params = kwargs.get("params")
    cache_file = _make_cache_filename(url, params)

    if OFFLINE_MODE:
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            # Simulate a Response object
            response = requests.Response()
            response.status_code = cached["status_code"]
            response._content = cached["content"].encode("utf-8")
            response.headers = cached["headers"]
            response.url = cached["url"]
            return response
        else:
            raise FileNotFoundError(f"No cached response for {url}")
    else:
        response = requests.get(url, **kwargs)
        # Cache the result
        cached_data = {
            "status_code": response.status_code,
            "content": response.text,
            "headers": dict(response.headers),
            "url": response.url,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cached_data, f, indent=2)
        return response
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

    response = get_request(url, headers={
        "accept": "application/json",
        "AccessKey": env['AccessKey']
    })
    return response.json()
def get_videos(collection_id):
    url = f"https://video.bunnycdn.com/library/{env['LibraryID']}/videos?page=1&itemsPerPage=100&orderBy=date"
    url += '&collection=' + collection_id

    response = get_request(url, headers={
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
        new_collection: type_collection =  {
            'name': col['name'],
            'guid': col['guid'],
            'videoCount': col['videoCount'],
            'previewImageUrl': (col['previewImageUrls'] or ['./media/no_image.svg'])[0],
            'videos': []
        }
        # print(get_videos(col['guid']))
        for vid in get_videos(col['guid'])['items']:
            new_video: type_video = {
                'name': vid['title'],
                'guid': vid['guid'],
                'length': vid['length'],
                'previewImageUrl': f'https://{env["CDNHostname"]}/{vid["guid"]}/{vid["thumbnailFileName"]}',
                'embedUrl':  f'https://{env["VideoHostName"]}/embed/{env["LibraryID"]}/{vid["guid"]}{env["QueryParams"]}',
                'description': 
                    f"<h2>{vid['title']}</h2>\n" +\
                    get_by_name(vid['metaTags'], ('property', 'description'), default={}).get('value', ''),
                'groups': [f'All Videos.{new_collection["name"]}']
            }
            new_video['groups'].extend(parse_groups(new_video['description']))
            new_video["description"] += '\n'
            for group in new_video['groups']:
                # add to playlist
                if group not in PLAYLISTS: PLAYLISTS[group] = {}
                video_name = new_video['name']
                if video_name in PLAYLISTS[group]:
                    i = 1
                    while f'({i}){video_name}' in PLAYLISTS[group]:
                        i += 1
                    video_name = f'({i}){video_name}'
                PLAYLISTS[group][video_name] = new_video
                new_video["description"] = new_video["description"].replace(f"#{group}\n", "")
                new_video["description"] += f'<a href="#">#{group}</a>\n'
                print("WARNING: Generate link url for tags in description!!!")
            new_collection['videos'].append(new_video)
        COLLECTIONS.append(new_collection)
    return COLLECTIONS, PLAYLISTS
def copy_through(file_name: str):
    (out_dir/file_name).write_bytes(
        (src_dir/file_name).read_bytes()
    )
def process_keys(keys: dict[str, str|list|dict], len_base=None) -> tuple[dict[str, int], dict[str, str]]:
    new_keys = dict()
    len_base = len_base or dict()
    clean = True
    for k, v in keys.items():
        if isinstance(v, list):
            clean = False
            len_base[k] = len(v)
            for i, el in enumerate(v):
                new_keys[f"{k}.{i}"] = el
        elif isinstance(v, dict):
            clean = False
            for ik, el in v.items():
                new_keys[f"{k}.{ik}"] = el
        else:
            new_keys[k] = v
    if not clean:
        return process_keys(new_keys, len_base)
    
    # add brackets {}
    final_dict = dict()
    for k, v in new_keys.items():
        final_dict["{"+k+"}"] = v
    return len_base, final_dict
def update_template(template_text: str, len_base: dict[str, int]) -> str:
    """
    Replaces all $key$(...) blocks in template_text with repeated content.
    """
    # Pattern matches:
    # $key$( ... )
    pattern = re.compile(
        r'\$(\w+)\$\((.*?)\)',
        re.DOTALL
    )
    
    def replacer(match: re.Match):
        key = match.group(1)  # side_bar_items
        block = match.group(2) # <li><a href="{$.url}">{$.name}</a></li>
        
        n = len_base[key]
        
        results = []
        for idx in range(n):
            text = block
            
            # Replace $ with key.index
            text = text.replace("$", f"{key}.{idx}")
            
            results.append(text)
        
        return "".join(results)
    
    # Perform replacement
    updated_text = pattern.sub(replacer, template_text)
    return updated_text
def format_page(_in: str, keys_temp: dict[str, str|list[str]]) -> str:
    len_base, keys_temp = process_keys(keys_temp)
    new_page_temp = update_template(_in, len_base)
    new_page = replace_all(new_page_temp, keys_temp)
    return new_page


# prepare out
out_dir = Path('./out-html-v2')
src_dir = Path('./src-html-v2')
clear_directory(out_dir)
(out_dir/'media').mkdir()

# make it!
COLLECTIONS, PLAYLISTS = get_collections_playlists()
from pprint import pprint
pprint(PLAYLISTS)

init_video = (src_dir/'init_video.txt').read_text().strip()
init_video_playlist, init_video_name = init_video.split('\n')
init_video_obj = PLAYLISTS[init_video_playlist][init_video_name]

init_page = (src_dir/'index.html').read_text()
formatted_init_page = format_page(init_page,
    {
        'title': "Video Viewer",
        'phrase_up': "Upper Phrase",
        'phrase_down': "Bottom Phrase",
        'init_video': {
            'link': init_video_obj['embedUrl'],
            'description': init_video_obj['description'],
            'source': init_video_playlist,
        },
        'side_bar_items': [
            {"name": "Home", "url": "/"},
            {"name": "Content1", "url": "#"},
            {"name": "All Videos", "url": "/All Videos"},
        ],
        'down_bar_items': [
            {"name": "Content1", "url":  "#"},
            {"name": "Content2", "url":  "#"},
            {"name": "Content3", "url":  "#"},
            {"name": "Content4", "url":  "#"},
            {"name": "Content5", "url":  "#"},
            {"name": "Content6", "url":  "#"},
            {"name": "Content7", "url":  "#"},
            {"name": "Shonot", "url":  "#"},
        ],
    }
)
(out_dir/'index.html').write_text(formatted_init_page)


groups_template = (src_dir/'groups.html').read_text()


groups_page = replace_all(groups_template,
    {
        '{title}': "Video Viewer",
        '{phrase_up}': "Upper Phrase",
        '{phrase_down}': "Bottom Phrase",
        '{directory}': "All Videos",
    }
)
(out_dir/'All Videos').mkdir()
(out_dir/'All Videos'/'index.html').write_text(groups_page)


copy_through('styles.css')
copy_through('media/no_image.svg')
copy_through('media/home.svg')

if '--local-test' in sys.argv:
    os.system('python -m http.server -dout-html-v2')