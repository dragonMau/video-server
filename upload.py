from pathlib import Path
import urllib.parse
import requests
import urllib
import time
import ctypes
import os

env_file = Path('./edge/.env.local')
if env_file.exists():
    env = {e[0]: e[1] for e in (line.split('=') for line in env_file.read_text().splitlines() if line)}
else:
    env = dict(os.environ)

# setup variables
DIRECTORY = Path(r"C:\Users\mseli\Downloads\drive videos lll\drive videos")
prefix = '03_hitvaaduyot/'

# setup classes and functions
class UnsuccesfulUpload(requests.exceptions.HTTPError): pass
class ConnctionIssue(requests.exceptions.HTTPError): pass
class UnexpectedJson: pass
def print_nl(*args, **kwargs):
    LINECLS = "\x1b[2K\r"
    print(LINECLS, end='')
    print(*args, **kwargs)

class ProgressFileReader:
    def __init__(self, path, chunk_size=1024 * 1024):
        self.path = Path(path)
        self.file = open(self.path, 'rb')
        self.total = self.path.stat().st_size
        self.read_bytes = 0
        self.chunk_size = chunk_size
        print_nl(end='')

    def read(self, size=-1):
        chunk = self.file.read(size if size > 0 else self.chunk_size)
        if chunk:
            self.read_bytes += len(chunk)
            print(f"  {self.read_bytes:,} / {self.total:,} bytes", end='\r')
        return chunk

    def __len__(self):
        return self.total
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.file.close()
        print()  # move to next line after progress is done

def ask_api(url):
    headers = {
        "accept": "application/json",
        "AccessKey": env['AccessKey']
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        if response.status_code == 499:
            raise ConnctionIssue(
                f"\nrequest.{url=};\nrequest.{headers=};"
                f"\n{response.status_code=};\n{response.text=};\n{response.headers=};"
            )
        raise UnsuccesfulUpload(
            f"\nrequest.{url=};\nrequest.{headers=};"
            f"\n{response.status_code=};\n{response.text=};\n{response.headers=};"
        )
    return response.json()
    
def post_api(url: str, payload:dict[str, str]):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "AccessKey": env['AccessKey']
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        if response.status_code == 499:
            raise ConnctionIssue(
                f"\nrequest.{url=};\nrequest.{headers=};"
                f"\n{response.status_code=};\n{response.text=};\n{response.headers=};"
            )
        raise UnsuccesfulUpload(
            f"\nrequest.{url=};\nrequest.{headers=};\nrequest.{payload=};"
            f"\n{response.status_code=};\n{response.text=};\n{response.headers=};"
        )
    return response.json()
    
def get_libraries(search:str=""):
    print_nl(f"looking up collection '{search}'..", end='\r')
    time.sleep(1)
    url = f"https://video.bunnycdn.com/library/{env['LibraryID']}/collections?page=1&itemsPerPage=100&orderBy=date&includeThumbnails=false"

    search = search.strip()
    if search:
        url += '&search=' + urllib.parse.quote_plus(search)

    return ask_api(url)

def get_videos(collection:str="", search:str=""):
    print_nl(f"looking up video '{search}' in '{collection}'..", end='\r')
    time.sleep(1)
    url = f"https://video.bunnycdn.com/library/{env['LibraryID']}/videos?page=1&itemsPerPage=100&orderBy=date"
    search = search.strip()
    if search:
        url += '&search=' + urllib.parse.quote_plus(search)
    collection = collection.strip()
    if collection:
        url += '&collection=' + urllib.parse.quote_plus(collection)
    return ask_api(url)

def create_video(title:str, collectionId:str):
    print_nl(f"creating video '{title}'..", end='\r')
    time.sleep(1)
    url = f"https://video.bunnycdn.com/library/{env['LibraryID']}/videos"
    title = title.strip(); collectionId = collectionId.strip()
    if not title: raise Exception()
    if not collectionId: raise Exception()
    payload = {
        "title": title,
        "collectionID": collectionId
    }
    return post_api(url, payload)

def upload_video(video_id: str, video_path: str):
    print_nl(f"uploading video '{str(video_path)}'..", end='\r')
    time.sleep(1)
    url = f"https://video.bunnycdn.com/library/{env['LibraryID']}/videos/{video_id}"
    headers = {
        "AccessKey": env['AccessKey'],
        "Content-Type": "application/octet-stream"
    }

    video_path: Path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    with ProgressFileReader(video_path) as stream:
        response = requests.put(url, headers=headers, data=stream)

        if response.status_code != 200:
            if response.status_code == 499:
                raise ConnctionIssue(
                    f"\nrequest.{url=};\nrequest.{headers=};"
                    f"\n{response.status_code=};\n{response.text=};\n{response.headers=};"
                )
            raise UnsuccesfulUpload(
                f"\nrequest.{url=};\nrequest.{headers=};\nrequest.video_path={video_path};"
                f"\n{response.status_code=};\n{response.text=};\n{response.headers=};"
            )
        return response.json()

def delete_video(video_id):
    print_nl(f"deleting video '{video_id}'..", end='\r')
    time.sleep(1)
    url = f"https://video.bunnycdn.com/library/{env['LibraryID']}/videos/{video_id}"
    
    headers = {
        "accept": "application/json",
        "AccessKey": env['AccessKey']
    }
    response = requests.delete(url, headers=headers)
    
    if response.status_code != 200:
        if response.status_code == 499:
            raise ConnctionIssue(
                f"\nrequest.{url=};\nrequest.{headers=};"
                f"\n{response.status_code=};\n{response.text=};\n{response.headers=};"
            )
        raise UnsuccesfulUpload(
            f"\nrequest.{url=};\nrequest.{headers=};"
            f"\n{response.status_code=};\n{response.text=};\n{response.headers=};"
        )
    return response.json()

def set_wakelock():
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002

    # Prevent sleep & screen off
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )
    print_nl("Preventing sleep. Press Ctrl+C to exit.")

def drop_wakelock():
    ES_CONTINUOUS = 0x80000000
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    print_nl("Sleep allowed again.")

def main():
    directories = [DIRECTORY/d for d in DIRECTORY.iterdir() if d.suffix != '.db']

    for each in directories:
        files = [each/d for d in each.iterdir() if d.suffix != '.db']
        for file in files:
            col_name = prefix + file.parent.name
            vid_name = file.name
            response = get_libraries(col_name)
            if response['totalItems'] == 0:
                raise NotADirectoryError(f'no entries {file=}')
            if response['totalItems'] > 1:
                raise Exception(f'too much entries {file=}')
            if response['totalItems'] == 1:
                col_guid = response['items'][0]["guid"]
                response = get_videos(col_guid, vid_name)
                if response['totalItems'] == 0:
                    response = create_video(vid_name, col_guid)
                    vid_guid = response['guid']
                    vid_stat = response['status']
                elif response['totalItems'] == 1:
                    vid_guid = response['items'][0]['guid']
                    vid_stat = response['items'][0]['status']
                else:
                    raise Exception(f'too much videos {response=}')
                print_nl(col_name, vid_name, vid_stat)
                if vid_stat in (0, 6):
                    print_nl(f"uploading \"{str(file)}\"...")
                    if vid_stat == 6:
                        delete_video(vid_guid)
                        response = create_video(vid_name, col_guid)
                        vid_guid = response['guid']
                    response = upload_video(vid_guid, file)
                    print_nl(response)

if __name__ == "__main__":
    while True:
        repeat = False
        try:
            set_wakelock()
            main()
        except KeyboardInterrupt:
            print_nl('Interrupted.')
        except ConnctionIssue as e:
            print('\n', e)
            repeat = True
            time.sleep(30)
        else:
            print_nl('done')
        finally:
            drop_wakelock()
        if not repeat: break