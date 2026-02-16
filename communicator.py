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
    return ""