from pathlib import Path
import hashlib
import zlib
import path_logic
import urllib.request
import urllib.error
import zipfile
import io

class ServerError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

def clone(paste_dir,host_num):
    print(f'Attempting to contact localhost:{host_num}')
    request = urllib.request.Request(url=f'http://localhost:{host_num}/clone',data=None,headers={'content-type':'application/zip'},method='GET')
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                #everything is super
                print('Connection succeeded. Beggining cloning.')
                zip_raw_files = response.read()
                virt_file = io.BytesIO(zip_raw_files)
                with zipfile.ZipFile(virt_file,'r') as zip_opened:
                    zip_opened.extractall(paste_dir)
            else:
                raise ServerError('Server returned wrong status.')
    except urllib.error.URLError:
        raise ServerError('Failed to connect to server.')
    except urllib.error.HTTPError:
        raise ServerError('Server failed to handle request.')
    path_logic.put_content_after_clone(root_dir=(paste_dir / '.pit'))

def fetch(root_dir, host_num):
    print(f'Attempting to contact localhost:{host_num}')
    request = urllib.request.Request(url=f'http://localhost:{host_num}/fetch',data=None,headers={'content-type':'application/zip'},method='GET')
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                print('Connection succeeded. Beggining fetching.')
                zip_raw_files = response.read()
                virt_file = io.BytesIO(zip_raw_files)
                with zipfile.ZipFile(virt_file,'r') as zip_opened:
                    zip_opened.extractall(root_dir)
            else:
                raise ServerError('Server returned wrong status.')
    except urllib.error.URLError:
        raise ServerError('Failed to connect to server.')
    except urllib.error.HTTPError:
        raise ServerError('Server failed to handle request.') 
    
def pull(project_dir, host_num):
    fetch(project_dir / '.pit', host_num)
    