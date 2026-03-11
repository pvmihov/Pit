from pathlib import Path
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
    request = urllib.request.Request(url=f'http://localhost:{host_num}/branch',data=None,headers={'content-type':'text/plain', 'X-Current-Branch': cur_branch},method='GET')
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
            path_logic.checkout(root_dir=(project_dir / '.pit'),branch_name=cur_branch)
            path_logic.merge(root_dir=(project_dir / '.pit'),branch_name=temp_name)
            temp_head_file.unlink()         
            return ''
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
    
def push(root_dir, host_num):
    cur_branch = find_cur_branch(root_dir)
    cur_head_file = root_dir / 'refs' / 'heads' / cur_branch
    cur_commit = cur_head_file.read_text()
    request = urllib.request.Request(url=f'http://localhost:{host_num}/branch',data=None,headers={'content-type':'text/plain', 'X-Current-Branch': cur_branch},method='GET')
    print(f'Attempting to contact localhost:{host_num}')
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                print('Connection succeeded.')
                branch_head = response.read()
                branch_head = branch_head.decode('utf-8')
            elif response.status == 204:
                branch_head = '-1'
            else:
                raise ServerError('Server returned wrong status.')
    except urllib.error.HTTPError:
        raise ServerError('Server failed to handle request.')  
    except urllib.error.URLError:
        raise ServerError('Failed to connect to server.')
    if branch_head != '-1':
        new_branch_file = root_dir / 'objects' / branch_head
        if not new_branch_file.exists():
            return f'branch {cur_branch} is behind localhost:{host_num}'
        if cur_commit == branch_head:
            return f'branch {cur_branch} is identical to localhost:{host_num}'
        lca = path_logic.find_common_ancestor(object_folder=root_dir / 'objects',commit1=cur_commit,commit2=branch_head)
        if lca is not branch_head:
            return f'branch {cur_branch} has conflicting changes with localhost:{host_num}'
    print('Begining pushing.')
    zip_buffer = io.BytesIO()
    objects_dir = root_dir / 'objects'
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_opened:
        for file_path in objects_dir.iterdir():
            if file_path.is_file():
                # todo later, check that the file was not altered
                # hash = path_logic.sha1_file(file=file_path)
                # if hash != file_path.name: 
                #     print(f'File {file_path.name} was altered, so will not be pushed to server')
                #     continue #the file was altered and not created correctly
                archive_path = f"objects/{file_path.name}"
                zip_opened.write(file_path, archive_path)
    zip_raw_bytes = zip_buffer.getvalue()
    request = urllib.request.Request(url=f'http://localhost:{host_num}/push',data=zip_raw_bytes,headers={'content-type':'application/zip', 'X-Current-Branch': cur_branch, 'X-New-Last-Commit': cur_commit},method='POST')
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                return ''
            else:
                raise ServerError('Server returned wrong status.')
    except urllib.error.HTTPError:
        raise ServerError('Server failed to handle request.')  
    except urllib.error.URLError:
        raise ServerError('Failed to connect to server.')
    
def clone_branch(root_dir, branch_name, host_num):
    head_file_wanted = root_dir / 'refs' / 'heads' / branch_name
    if head_file_wanted.exists():
        return f'{branch_name} already exists in the local repository'
    try:
        fetch(root_dir, host_num)
    except ServerError as err:
        raise err
    request = urllib.request.Request(url=f'http://localhost:{host_num}/branch',data=None,headers={'content-type':'text/plain', 'X-Current-Branch': branch_name},method='GET')
    print(f'Attempting to contact localhost:{host_num}')
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                print('Connection succeeded. Begging pulling')
                branch_head = response.read()
                branch_head = branch_head.decode('utf-8')
            elif response.status == 204:
                return f'{branch_name} does not exist on localhost:{host_num}'
            else:
                raise ServerError('Server returned wrong status.')
    except urllib.error.HTTPError:
        raise ServerError('Server failed to handle request.')  
    except urllib.error.URLError:
        raise ServerError('Failed to connect to server.')
    head_file_wanted.write_text(branch_head)
    return ''