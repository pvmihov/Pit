import path_logic
import server_logic
from pathlib import Path

def _find_root_folder(path):
    #receives path and goes recursively to its father, until it finds a repository
    #if it cant find anything, it returns None
    while True:
        attempt = path / '.pit'
        if attempt.exists() and attempt.is_dir():
            return path
        if path.parent == path:
            return None
        path=path.parent
    
def _init(folder_path):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder!=None:
        if str(root_folder)==str(cur_folder): return str(cur_folder)+' is already a repository.'
        else: return str(cur_folder)+' is already part of repository in '+str(root_folder)
    result = path_logic.init(cur_folder)
    if result==False:
        #should be impossible
        return str(cur_folder)+' is already a repository.'
    return 'Completed init in '+folder_path

def _log(folder_path):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    result = path_logic.log(root_dir=(root_folder / '.pit'))
    print(result)
    return ""

def _commit(folder_path,message):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    for c in message:
        if c == '\n':
            return 'Message must not contain new lines'
    path_logic.commit(root_dir=(root_folder / '.pit'),commit_message=message)
    return 'Completed commit in '+str(folder_path)+' with message:'+message

def _add(folder_path, file_path):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    file = Path(file_path).resolve()
    if not file.is_relative_to(root_folder):
        return 'The path '+str(file)+' is not inside the repository.'
    if file.is_dir()==False:
        path_logic.add_file(root_dir=(root_folder / '.pit'), file=file)
    else:
        path_logic.add_folder(root_dir=(root_folder / '.pit'),folder_dir=file)
    return 'Completed add for '+str(file_path)

def _checkout(folder_path, branch_name):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    try:
        result=path_logic.checkout(root_dir=(root_folder / '.pit'),branch_name=branch_name)
        if result:
            return "Switched to branch "+branch_name
        else:
            return "Created branch "+branch_name
    except path_logic.UncommitedChanges as error:
        return error.message
    
def _show(folder_path):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    result = path_logic.show_index(root_dir=(root_folder / '.pit'))
    print(result)
    return ""

def _retrieve(folder_path, commit_name, file_path, loc_path):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    file = Path(file_path).resolve()
    if not file.is_relative_to(root_folder):
        return 'The path '+str(file)+' is not inside the repository.'
    file_name = str(file)
    file_name = file_name.removeprefix(str(root_folder)+'/')
    if loc_path=="":
        try:
            result = path_logic.retrieve(root_dir=(root_folder / '.pit'),commit_name=commit_name,file_name=file_name,create=False,create_place=None)
        except path_logic.UnableToRetrieve as error:
            return error.message 
        try:
            result_text = result.decode('utf-8')
        except UnicodeDecodeError:
            return "The content of the file is not in text form"
        print(result_text)
        return ""
    else:
        loc_file = Path(loc_path).resolve()
        if loc_file.is_dir():
            return "The desired location is a directory"
        try:
            path_logic.retrieve(root_dir=(root_folder / '.pit'),commit_name=commit_name,file_name=file_name,create=True,create_place=loc_file)
        except path_logic.UnableToRetrieve as error:
            return error.message
        if commit_name=='last' and file_path==loc_path: return "Restore information of file "+str(loc_file)
        else: return "Retrieve information of file "+file_name+" to "+str(loc_file)
    
def _status(folder_path, file_path):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    file = Path(file_path).resolve()
    if not file.is_relative_to(root_folder):
        return 'The path '+str(file)+' is not inside the repository.'
    if file.is_dir():
        return "The path given is a directory"
    return path_logic.status(root_dir=(root_folder / '.pit'),file=file)   

def _ls_tree(folder_path, commit_name):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    try:
        toprint = path_logic.ls_tree(root_dir=(root_folder / '.pit'),commit_name=commit_name)
    except UnicodeDecodeError:
        return 'The commit does not exist'
    except path_logic.NonExistentTree as error:
        return error.message
    print(toprint)
    return ''

def _branch(folder_path):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    answer = path_logic.branch_list(root_dir=(root_folder / '.pit'))
    print(answer)
    return ''


def _merge(folder_path, branch_name):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    try:
        if path_logic.merge(root_dir=(root_folder / '.pit'),branch_name=branch_name)>0:
            return "Completed merge with "+branch_name
        else:
            return "Already up to date"
    except path_logic.UncommitedChanges as error:
        return error.message
    except path_logic.NonExistentBranch as error1:
        return error1.message
    except path_logic.ConflictingChanges as error2:
        return error2.message
    

def _clone(folder_path, server_num):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder is not None:
        return str(cur_folder)+' is already part of a repository.'
    try:
        number = int(server_num)
    except:
        return 'The server number must be a number'
    if number<1024 or number>65535:
        return 'The server must be a number between 1024 and 65535'
    desired_folder = cur_folder / 'project'
    if desired_folder.exists():
        return str(desired_folder)+' must not exist to create repository in it.'
    try:
        server_logic.clone(desired_folder,server_num)
    except server_logic.ServerError as err:
        return err.message
    return 'Finished cloning into '+str(desired_folder)

def _fetch(folder_path, server_num):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    try:
        number = int(server_num)
    except:
        return 'The server number must be a number'
    if number<1024 or number>65535:
        return 'The server must be a number between 1024 and 65535'
    try:
        server_logic.fetch(root_dir=(root_folder / '.pit'),host_num=number)
    except server_logic.ServerError as err:
        return err.message
    return 'Finished fetching from '+str(server_num)

def _pull(folder_path, server_num):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    try:
        number = int(server_num)
    except:
        return 'The server number must be a number'
    if number<1024 or number>65535:
        return 'The server must be a number between 1024 and 65535'
    try:
        text = server_logic.pull(project_dir=root_folder,host_num=number)
        if text:
            return text
    except server_logic.ServerError as err:
        return err.message
    except path_logic.UncommitedChanges as err2:
        return err2.message
    except path_logic.ConflictingChanges as err3:
        return err3.message
    return 'Finished pulling from '+str(server_num)   

def _push(folder_path, server_num):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    try:
        number = int(server_num)
    except:
        return 'The server number must be a number'
    if number<1024 or number>65535:
        return 'The server must be a number between 1024 and 65535'
    try:
        text = server_logic.push(root_dir=(root_folder / '.pit'),host_num=number)
        if text:
            return text
    except server_logic.ServerError as err:
        return err.message
    except path_logic.UncommitedChanges as err2:
        return err2.message
    except path_logic.ConflictingChanges as err3:
        return err3.message
    return 'Finished pushing to '+str(server_num)   

def _clone_branch(folder_path, branch_name, server_num):
    cur_folder = Path(folder_path).resolve()
    if cur_folder.exists()==False:
        return "Communicator didn't receive valid folder."
    elif cur_folder.is_dir()==False:
        return "Communicator didn't receive valid folder."
    root_folder = _find_root_folder(cur_folder)
    if root_folder==None:
        return str(cur_folder)+' is not part of a repository.'
    try:
        number = int(server_num)
    except:
        return 'The server number must be a number'
    if number<1024 or number>65535:
        return 'The server must be a number between 1024 and 65535'
    try:
        text = server_logic.clone_branch(root_dir=(root_folder / '.pit'),branch_name=branch_name,host_num=server_num)
        if text:
            return text
        else: return f'Finished cloning {branch_name} from localhost:{server_num}'
    except server_logic.ServerError as err:
        return err.message