from pathlib import Path
import hashlib
import zlib
import path_logic
import urllib.request
import urllib.error
import zipfile
import io
import random
import string

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
    except urllib.error.HTTPError:
        raise ServerError('Server failed to handle request.')
    except urllib.error.URLError:
        raise ServerError('Failed to connect to server.')
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
    except urllib.error.HTTPError:
        raise ServerError('Server failed to handle request.') 
    except urllib.error.URLError:
        raise ServerError('Failed to connect to server.')
    
def find_cur_branch(root_dir):
    head_file = root_dir / 'HEAD'
    text = head_file.read_text()
    return text

def pull(project_dir, host_num):
    try:
        fetch(project_dir / '.pit', host_num)
    except ServerError as err:
        raise err
    cur_branch = find_cur_branch(project_dir / '.pit') 
    request = urllib.request.Request(url=f'http://localhost:{host_num}/pull',data=None,headers={'content-type':'text/plain', 'X-Current-Branch': cur_branch},method='GET')
    print(f'Attempting to contact localhost:{host_num}')
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                print('Connection succeeded. Begging pulling')
                branch_head = response.read()
                branch_head = branch_head.decode('utf-8')
            elif response.status == 204:
                return f'{cur_branch} does not exist on localhost:{host_num}'
            else:
                raise ServerError('Server returned wrong status.')
    except urllib.error.HTTPError:
        raise ServerError('Server failed to handle request.')  
    except urllib.error.URLError:
        raise ServerError('Failed to connect to server.')
    temp_head_file = None
    while True:
        temp_name = ''
        for i in range(0,6):
            temp_name+=random.choice(string.ascii_letters)
        temp_head_file = project_dir / '.pit' / 'refs' / 'heads' / temp_name
        if not temp_head_file.exists():
            break
    head_file = project_dir / '.pit' / 'HEAD'
    head_file.write_text(temp_name)
    cur_head_file = project_dir / '.pit' / 'refs' / 'heads' / cur_branch
    cur_tree = cur_head_file.read_text()
    temp_head_file.write_text(cur_tree)
    cur_head_file.write_text(branch_head)
    try:
        value = path_logic.merge(root_dir=(project_dir / '.pit'),branch_name=cur_branch,ask_for_comm_name=False)
        if value==2:
            return f'Because of conflicts with localhost:{host_num}, a temporary branch {temp_name} was created.\n{cur_branch} was copied from the server.\nYou can merge them with pit merge'
        elif value==1:
            head_file.write_text(cur_branch)
            temp_head_file.unlink()
            return ''
        else:
            head_file.write_text(cur_branch)
            cur_head_file.write_text(cur_tree)
            temp_head_file.unlink()    
            return f'branch {cur_branch} is ahead or concurrent with {host_num}'       
    except path_logic.UncommitedChanges:
        head_file.write_text(cur_branch)
        cur_head_file.write_text(cur_tree)
        temp_head_file.unlink()
        raise path_logic.UncommitedChanges('Please commit all changes before pulling')
    except path_logic.ConflictingChanges as err:
        head_file.write_text(cur_branch)
        cur_head_file.write_text(cur_tree)
        temp_head_file.unlink()
        raise err  
        
    
