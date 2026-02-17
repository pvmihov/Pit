import path_logic
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
    return "\n"

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
    return "\n"