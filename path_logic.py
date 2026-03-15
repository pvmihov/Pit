from pathlib import Path
import hashlib
import zlib
from logic_classes import (
    Pit_file,
    Index,
    File_entry,
    Tree,
)
from typing import List

def sha1_file(file : Path) -> str:
    #returns sha-1 encryption of file
    hash = hashlib.sha1()
    with file.open('rb') as curfile:
        while chunk := curfile.read(8192):
            hash.update(chunk)
    return hash.hexdigest()

def create_blob(root_dir : Path, file : Path) -> str:
    #creates blob in the objects folder
    hash = sha1_file(file)
    blob = root_dir / 'objects' / hash
    if blob.exists():
        return hash
    open_file = file.open('rb')
    compressed_data = zlib.compress(open_file.read()) #has to be remade for big file openings
    blob.write_bytes(compressed_data)
    return hash

def init(project_dir : Path):
    #initialises all the needed files 
    dot_pit_folder = project_dir / '.pit'
    try:
       dot_pit_folder.mkdir(exist_ok=False)
    except FileExistsError:
        return False
    objects_folder = dot_pit_folder / 'objects'
    objects_folder.mkdir()
    refs_folder = dot_pit_folder / 'refs'
    refs_folder.mkdir()
    refs_heads_folder = refs_folder / 'heads'
    refs_heads_folder.mkdir()
    HEAD_file = dot_pit_folder / 'HEAD'
    HEAD_file.write_text('Main')
    Main_commit = refs_heads_folder / 'Main'
    Main_commit.write_text('-')
    index_file = dot_pit_folder / 'index'
    compresed_info = zlib.compress(b'0\x1e0\x1e')
    index_file.write_bytes(compresed_info)
    return True

def find_index_old(index,num_blobs,file_name):
    #performs binary search and returns index of first filename in index that is smaller or equal to file_name
    l=0
    r=num_blobs+1
    while l<r-1:
        mid=int((l+r)/2)
        splited = index[mid].split('\x1d')
        name = splited[0]
        if name<=file_name: l=mid
        else: r=mid
    return l

def decompress_index(index_file):
    #takes index_file which is Path object of the index, and returns the array of lines
    with index_file.open('rb') as index_opened:
        index_compressed = index_opened.read()    
    index_content = zlib.decompress(index_compressed)
    index_text = index_content.decode('utf-8')
    index = index_text.split('\x1e')
    index.pop()
    return index

def add_file(root_dir : Path, file : Path):
    if file.resolve().is_relative_to(root_dir.resolve()): return
    #runs command pit add file
    #receives a path object called file and changes the index accordingly
    project_dir = root_dir.parent
    index = Index.from_file(root_dir)
    file_name = str(file)
    name_dir = str(project_dir)
    if name_dir=='.': name_dir=''
    file_name = file_name.removeprefix(str(project_dir)+'/')
    if file.exists():
        #means file was updated
        hash = create_blob(root_dir,file)
        creation = -1
        if index.number_of_files == 0:
            #we have to create the file, it is also the first file
            creation = 0
        else: 
            position = index.find_file_in_index(file_name)
            if position==-1:
                creation = position+1
            cur_file_entry = index.files[position]
            if cur_file_entry.name!=file_name: 
                creation = position+1
        if creation!=-1:
            #this means we have to create the file
            new_entry = File_entry(name=file_name,hash=hash,has_bools=True,exists=True,changed=True)
            index.add_single_file_by_position(creation,new_entry)
        else:
            #this means file is in the index at line, position
            cur_file_entry = index.files[creation]
            if cur_file_entry.hash==hash:
                #means nothing was changed, so we shouldnt change nothing
                return
            #here the file was actually changed
            index.files[creation].hash = hash
            index.files[creation].changed = True
        index.write_to_file()    
    else:
        #means file was deleted
        #we want to change exist property to false and changed property to true
        if index.number_of_files == 0: return # there arent blobs, so 
        position = index.find_file_in_index(file_name)
        if position==0: return #the file wasnt in the index, so no need to do anything
        cur_file_entry = index.files[position]
        if cur_file_entry.name!=file_name: return #the file wasnt in the index
        #if we are here this means that the file is actually in index and we need to change the information
        if cur_file_entry.exists or (not cur_file_entry.changed):
            index.files[position]=File_entry(name=file_name,hash='...',has_bools=True,exists=False,changed=True)
            index.write_to_file()
        
def get_folder(file_name : str) -> str:
    #receives the name of a file, and returns what folder its in
    slash = -1
    for i in range(0,len(file_name)):
        if file_name[i]=='/': slash=i
    if slash == -1: return '.'
    par_name=''
    for i in range(0,slash): par_name+=file_name[i]
    return par_name

def sha1_text_old(text : str) -> str:
    #returns sha1 encryption of text
    hash = hashlib.sha1()
    hash.update(text.encode('utf-8'))
    return hash.hexdigest()

def create_filecompr_from_text_old(root_dir : Path,tree_info : str) -> str:
    hash = sha1_text_old(tree_info)
    blob = root_dir / 'objects' / hash
    if blob.exists():
        return hash
    compressed_data=zlib.compress(tree_info.encode('utf-8'))
    blob.write_bytes(compressed_data)
    return hash

def commit(root_dir : Path, commit_message : str):
    #commits the changes in index
    index = Index.from_file(root_dir)
    num_trees = 1
    tree_dic={
        '.': 0
    }
    tree_array: List[Tree] = []
    tree_array.append(Tree(object_file=(root_dir / 'objects' / '...')))
    tree_array[0].name = '.'
    changed = []
    existing_files = 0
    for cur_entry in index.files:
        if cur_entry.changed:
            changed.append([cur_entry.name,cur_entry.exists])
        if not cur_entry.exists: 
            continue
        existing_files+=1
        father = get_folder(cur_entry.name)
        num = -1
        if father in tree_dic:
            num=tree_dic[father]
        else:
            tree_dic[father]=num_trees
            tree_array.append(Tree(object_file=(root_dir / 'objects' / '...')))
            tree_array[num_trees].name=father
            tree_array[num_trees].father = get_folder(father)
            num=num_trees
            num_trees+=1
        tree_array[num].num_files+=1
        tree_array[num].files.append(File_entry(name=cur_entry.name,hash=cur_entry.hash))
        while True:
            father = get_folder(father)
            if father in tree_dic: break
            tree_dic[father]=num_trees
            tree_array.append(Tree(object_file=(root_dir / 'objects' / '...')))
            tree_array[num_trees].name=father
            tree_array[num_trees].father = get_folder(father)
            num_trees+=1
    index.number_of_files = existing_files
    copy_ogindex_files : List[File_entry] = index.files.copy()
    index.files.clear()
    for cur_entry in copy_ogindex_files:
        if not cur_entry.exists: 
            continue
        index.files.append(File_entry(cur_entry.name,cur_entry.hash,True,True,False))
    index.number_of_trees = num_trees
    root_tree = ''
    for cur_key, cur_num in sorted(tree_dic.items(),reverse=True):
        cur_tree = tree_array[cur_num]
        cur_tree.write_to_file(fix=True)
        if cur_tree.father=='':
            root_tree = cur_tree.hash
            continue
        par_num = tree_dic[cur_tree.father]
        tree_array[par_num].num_trees+=1
        tree_array[par_num].trees.append(File_entry(name=cur_tree.name,hash=cur_tree.hash))
    index.trees.clear()
    for cur_key, cur_num in sorted(tree_dic.items()):
        cur_tree = tree_array[cur_num]
        index.trees.append(File_entry(name=cur_key,hash=cur_tree.hash))
    index.write_to_file()
    head_file = Pit_file(root_dir / 'HEAD', is_compr=False)
    cur_branch = head_file.get_value_text()
    branch_head = Pit_file(root_dir / 'refs' / 'heads' / cur_branch,is_compr=False)
    previous_commit = branch_head.get_value_text()
    commit_info = commit_message+'\x1e'+previous_commit+'\x1e'+root_tree+'\x1e'
    commit_info+=str(len(changed))+'\x1e'
    for ch in changed:
        commit_info+=ch[0]+'\x1d'+str(ch[1])+'\x1e'
    commit_hash = create_filecompr_from_text_old(root_dir=root_dir,tree_info=commit_info)
    branch_head.write_value_from_text(commit_hash)

def log(root_dir : Path) -> str:
    #returns information for all previous commits in current branch
    head_file = root_dir / 'HEAD'
    with head_file.open('rb') as head_opened:
        cur_branch = head_opened.read()
    cur_branch = cur_branch.decode('utf-8')
    branch_head = root_dir / 'refs' / 'heads' / cur_branch
    with branch_head.open('rb') as branch_head_opened:
        last_commit = branch_head_opened.read()
    last_commit = last_commit.decode('utf-8')
    log_text = ''
    while last_commit!='-':
        commit_file = root_dir / 'objects' / last_commit
        with commit_file.open('rb') as commit_file_opened:
            commit_compressed = commit_file_opened.read()
        commit_text = zlib.decompress(commit_compressed).decode('utf-8')
        commit_info = commit_text.split('\x1e')
        commit_info.pop()
        log_text+='Commit name:'+last_commit+'\n'
        log_text+='Commit message:'+commit_info[0]+'\n'
        changed = 0
        removed = 0
        for i in range(4,len(commit_info)):
            spl = commit_info[i].split('\x1d')
            if spl[1]=='True': changed+=1
            else: removed+=1
        log_text+='Changed '+str(changed)+' files.\n'
        log_text+='Removed '+str(removed)+' files.\n'
        log_text+='\n\n'
        last_commit=commit_info[1]
    return log_text

class UnableToRetrieve(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

def find_file(root_dir : Path, cur_tree : str, file_name : str):
    tree = Tree.from_file(root_dir / 'objects' / cur_tree)
    if get_folder(file_name)==tree.name:
        #this means we are searching for the file itself in the list of files
        for cur_entry in tree.files:
            if cur_entry.name!=file_name: continue
            file = Pit_file(file_object=root_dir / 'objects' / cur_entry.hash, is_compr=True)
            file_bytes = file.get_value_bytes()
            return file_bytes
        return False
    else:
        #this means we are searching for a folder inside the list of folders
        for cur_entry in tree.trees:
            if file_name.startswith(cur_entry.name):
                return find_file(root_dir,cur_entry.hash,file_name)
        return False

def create_file(file : Path, bytes : bytes):
    unexist = []
    copy = file.parent
    while not copy.exists():
        unexist.append(copy)
        copy = copy.parent
    unexist.reverse()
    for un in unexist:
        un.mkdir()
    file.write_bytes(bytes)

def retrieve(root_dir : Path, commit_name : str, file_name : str, create : bool, create_place : Path) -> bytes:
    #finds the file with file_name and the version it had after commit_name
    #if create is true, it creates the file in create_place
    #else it just returns the value as bits
    head_file = Pit_file(root_dir / 'HEAD')
    cur_branch = head_file.get_value_text()
    branch_head = Pit_file(root_dir / 'refs' / 'heads' / cur_branch)
    last_commit = branch_head.get_value_text()
    if commit_name=='last': commit_name=last_commit
    while last_commit!=commit_name:
        if last_commit=='-':
            raise UnableToRetrieve('There is no commit called '+commit_name+' in '+cur_branch+' branch.\n')
        commit_file = root_dir / 'objects' / last_commit
        with commit_file.open('rb') as commit_file_opened:
            commit_compressed = commit_file_opened.read()
        commit_text = zlib.decompress(commit_compressed).decode('utf-8')
        commit_info = commit_text.split('\x1e')
        last_commit = commit_info[1]
    commit_file = root_dir / 'objects' / last_commit
    with commit_file.open('rb') as commit_file_opened:
        commit_compressed = commit_file_opened.read()
    commit_text = zlib.decompress(commit_compressed).decode('utf-8')
    commit_info = commit_text.split('\x1e')
    cur_tree = commit_info[2]
    file_content = find_file(root_dir,cur_tree,file_name)
    if file_content == False:
        raise UnableToRetrieve('There is no file '+file_name+' in the repository of commit '+commit_name+'.\n')
    if create: create_file(file=create_place,bytes=file_content)
    return file_content

class UncommitedChanges(Exception):
    def __init__(self, message):
        self.message=message
        super().__init__(message)

class IndexChanges():
    exists : bool
    new : bool
    name : str
    blob : str
    type : int
    old_blob : str

    def __init__(self,exists : bool, new : bool, name : str, blob : str, type : int, old_blob : str):
        self.exists = exists
        self.new = new
        self.name = name
        self.blob = blob
        self.type = type
        self.old_blob = old_blob

def complete_add_tree(root_dir : Path, new_tree : str) -> List[IndexChanges]:
    #iterates through the entire tree and adds IndexChanges for creation for every file
    with (root_dir / 'objects' / new_tree).open('rb') as new_opened:
        info = ( ( zlib.decompress( new_opened.read() ) ).decode('utf-8') ).split('\x1e')
    changes = [IndexChanges(True,True,info[0],new_tree,1,'')]
    num_files = int(info[1])
    for i in range(2,2+num_files):
        spl = info[i].split('\x1d')
        changes.append(IndexChanges(True,True,spl[0],spl[1],0,''))
    num_folders = int(info[2+num_files])
    for i in range(3+num_files,3+num_files+num_folders):
        spl = info[i].split('\x1d')
        new_changes = complete_add_tree(root_dir,spl[1])
        for change in new_changes: changes.append(change)
    return changes

def complete_delete_tree(root_dir : Path , old_tree : str) -> List[IndexChanges]:
    #iterates through the entire tree and adds IndexChanges for deletion for every file
    with (root_dir / 'objects' / old_tree).open('rb') as old_opened:
        info = ( ( zlib.decompress( old_opened.read() ) ).decode('utf-8') ).split('\x1e')   
    changes = [IndexChanges(False,False,info[0],old_tree,1,'')]
    num_files = int(info[1])
    for i in range(2,2+num_files):
        spl = info[i].split('\x1d')
        changes.append(IndexChanges(False,False,spl[0],spl[1],0,spl[1]))
    num_folders = int(info[2+num_files])
    for i in range(3+num_files,3+num_files+num_folders):
        spl = info[i].split('\x1d')
        new_changes = complete_delete_tree(root_dir,spl[1])
        for change in new_changes: changes.append(change)
    return changes

def fix_tree(root_dir : Path, new_tree : str, old_tree : str) -> List[IndexChanges]:
    #returns the changes needed to sync new_tree and old_tree
    with (root_dir / 'objects' / new_tree).open('rb') as new_opened:
        new_info = ( ( zlib.decompress( new_opened.read() ) ).decode('utf-8') ).split('\x1e')
    with (root_dir / 'objects' / old_tree).open('rb') as old_opened:
        old_info = ( ( zlib.decompress( old_opened.read() ) ).decode('utf-8') ).split('\x1e')   
    file_dic = {}
    folder_dic = {}
    changes = [IndexChanges(True,False,new_info[0],new_tree,1,'')]
    old_files = int(old_info[1])
    new_files = int(new_info[1])
    for i in range(2,2+old_files):
        spl = old_info[i].split('\x1d')
        file_dic[spl[0]]=spl[1]
    for i in range(2,2+new_files):
        spl = new_info[i].split('\x1d')
        if spl[0] in file_dic:
            #its in the dictionary
            if spl[1]!=file_dic[spl[0]]:
                #its changed
                changes.append(IndexChanges(True,False,spl[0],spl[1],0,file_dic[spl[0]]))
            file_dic.pop(spl[0])
        else:
            #its not so its new
            changes.append(IndexChanges(True,True,spl[0],spl[1],0,''))
    for left in file_dic:
        #all of these were in old but not in new
        changes.append(IndexChanges(False,False,left,file_dic[left],0,file_dic[left]))
    old_folders = int(old_info[2+old_files])
    new_folders = int(new_info[2+new_files])
    for i in range(3+old_files,3+old_files+old_folders):
        spl = old_info[i].split('\x1d')
        folder_dic[spl[0]]=spl[1]
    for i in range(3+new_files,3+new_files+new_folders):
        spl = new_info[i].split('\x1d')
        if spl[0] in folder_dic:
            #its in the dic
            if spl[1]!=folder_dic[spl[0]]:
                #there are changes in the folder
                new_changes = fix_tree(root_dir,spl[1],folder_dic[spl[0]])
                for change in new_changes: changes.append(change)
            folder_dic.pop(spl[0])
        else:
            new_changes = complete_add_tree(root_dir,spl[1])
            for change in new_changes: changes.append(change)
    for left in folder_dic:
        #all of those folders dont exist anymore
        new_changes = complete_delete_tree(root_dir,folder_dic[left])
        for change in new_changes: changes.append(change)
    return changes

def checkout(root_dir : Path, branch_name : str) -> bool:
    #switches to another branch, if it doesnt exist it creates it
    #returns False when it creates a new branch, and True when it changes to an existing one
    index = Index.from_file(root_dir)
    for cur_file in index.files:
        if cur_file.changed:
            raise UncommitedChanges('Please commit all changes before switching branches.')
    head_file = Pit_file(root_dir / 'HEAD')
    cur_branch = head_file.get_value_text()
    if cur_branch==branch_name: return True
    refs_heads = root_dir / 'refs' / 'heads'
    last_commit = '-1'
    for file in refs_heads.iterdir():
        if file.name == branch_name:
            with file.open('rb') as file_opened:
                last_commit = file_opened.read()
            break
    if last_commit=='-1':
        #branch does not exist and we need to create it
        cur_branch_file = Pit_file(refs_heads / cur_branch)
        cur_commit = cur_branch_file.get_value_text()
        new_branch = Pit_file(refs_heads / branch_name)
        new_branch.write_value_from_text(cur_commit)
        head_file.write_value_from_text(branch_name)
        return False
    #branch exists so we need to actually perform changes
    changes = []
    last_commit = last_commit.decode('utf-8')
    commit_file = root_dir / 'objects' / last_commit
    with commit_file.open('rb') as commit_opened:
        commit_compr = commit_opened.read()
    commit_decomp = zlib.decompress(commit_compr)
    commit_text = commit_decomp.decode('utf-8')
    commit_info = commit_text.split('\x1e')
    new_tree = commit_info[2]
    old_tree = index.trees[0].hash
    if old_tree==new_tree:
        #there arent any changes between the two branches, so we can just change
        cur_branch_file = Pit_file(refs_heads / cur_branch)
        cur_commit = cur_branch_file.get_value_text()
        new_branch = Pit_file(refs_heads / branch_name)
        new_branch.write_value_from_text(cur_commit)
        head_file.write_value_from_text(branch_name)
        return True
    changes = fix_tree(root_dir,new_tree,old_tree)
    for change in changes:
        if change.type == 1: continue
        cur_file = (root_dir.parent) / change.name
        if change.exists and (not change.new):
            #we have to check that the value in the folder is the same as in the old repo
            if (not cur_file.exists()):
                raise UncommitedChanges('There are conflicting changes, not added to index')
            if change.old_blob != sha1_file(cur_file):
                raise UncommitedChanges('There are conflicting changes, not added to index')
        elif change.exists and change.new:
            if cur_file.exists():
                print(str(cur_file))
                raise UncommitedChanges('There are conflicting changes, not added to index')
        else:
            if (not cur_file.exists()):
                raise UncommitedChanges('There are conflicting changes, not added to index')
            if change.old_blob != sha1_file(cur_file):
                raise UncommitedChanges('There are conflicting changes, not added to index')
    for_deletion = {}
    for_change = {}
    for change in changes:
        #print(change.name+' '+change.blob+' '+str(change.exists)+' '+str(change.new)+' '+str(change.type)+' '+str(change.old_blob))
        if change.exists: continue
        for_deletion[ change.name ] = 1
    for change in changes:
        if not change.exists: continue
        if change.new: continue
        for_change[change.name] = change.blob
    new_index = Index(root_dir)
    for cur_file in index.files:
        if cur_file.name in for_deletion: continue
        elif cur_file.name in for_change:
            new_index.files.append(File_entry(name=cur_file.name,hash=for_change[cur_file.name],has_bools=True,exists=True,changed=False))
        else:
            new_index.files.append(File_entry(name=cur_file.name,hash=cur_file.hash,has_bools=True,exists=True,changed=False))
    for change in changes:
        if change.type==1: continue
        if not change.new: continue
        new_index.files.append(File_entry(name=change.name,hash=change.blob,has_bools=True,exists=True,changed=False))
    new_index.number_of_files = len(new_index.files)
    for cur_tree in index.trees:
        if cur_tree.name in for_deletion: continue
        elif cur_tree.name in for_change:
            new_index.trees.append(File_entry(cur_tree.name,for_change[cur_tree.name]))
        else:
            new_index.trees.append(File_entry(cur_tree.name,cur_tree.hash))
    for change in changes:
        if change.type==0: continue
        if not change.new: continue
        new_index.trees.append(File_entry(change.name,change.blob))
    new_index.number_of_trees = len(new_index.trees)
    for change in changes:
        if change.type==1: continue
        cur_file = (root_dir.parent) / change.name
        if not change.exists:
            cur_file.unlink()
        else:
            with (root_dir / 'objects' / change.blob).open('rb') as file_opened:
                file_compressed = file_opened.read()
            file_bytes = zlib.decompress(file_compressed)
            create_file(cur_file,file_bytes)
    for change in changes:
        if change.type==0: continue
        if change.exists: continue
        cur_folder = (root_dir.parent) / change.name
        cname = change.name
        while True:
            if cname == '.': break
            cur_folder = (root_dir.parent) / cname
            is_empty = not any(cur_folder.iterdir())
            if is_empty:
                cur_folder.rmdir()
            else: break
            cname = get_folder(cname)
    new_index.write_to_file(sort_files=True,sort_trees=True)
    head_file.write_value_from_text(branch_name)
    return True

def list_files_in_dir(root_dir : Path, folder_dir : Path, folder_name : str, project_name : str) -> list:
    if folder_dir.resolve().is_relative_to(root_dir.resolve()): return []
    #returns a list of all the files in a directory with their blobs
    answer = []
    for child in folder_dir.iterdir():
        child_name = str(child)
        child_name = child_name.removeprefix(project_name+'/')
        if child.is_dir():
            new = list_files_in_dir(root_dir,child,child_name,project_name)
            for nnew in new: answer.append(nnew)
        else:
            hash = create_blob(root_dir,child)
            answer.append([child_name,hash])
    return answer

def add_folder(root_dir : Path, folder_dir : Path):
    if folder_dir.resolve().is_relative_to(root_dir.resolve()): return
    #adds the contents of an entire folder to the index
    #also checks for removed material, and flags it removed
    project_dir = root_dir.parent
    index = Index.from_file(root_dir)
    folder_name = str(folder_dir)
    name_dir = str(project_dir)
    if (folder_name!=name_dir):
        folder_name = folder_name.removeprefix(str(project_dir)+'/')
    else:
        folder_name = ''
    list_files = list_files_in_dir(root_dir,folder_dir,folder_name,str(project_dir))
    begin = index.find_file_in_index(folder_name)+1
    end = begin
    for i in range(begin,index.number_of_files+1):
        if i==index.number_of_files:
            end=i
            break
        if index.files[i].name.startswith(folder_name): continue
        end=i
        break
    new_files_dic = {}
    for file in list_files:
        new_files_dic[file[0]]=file[1]
    new_index_folder : List[File_entry] = []
    for cur_file in index.files[begin:end]:
        if cur_file.name in new_files_dic:
            if cur_file.hash == new_files_dic[cur_file.name]:
                if cur_file.exists: new_index_folder.append(cur_file)
                else: new_index_folder.append(File_entry(cur_file.name,cur_file.hash,True,True,True))
            else:
                new_index_folder.append(File_entry(cur_file.name,new_files_dic[cur_file.name],True,True,True))
            new_files_dic.pop(cur_file.name)
        else:
            new_index_folder.append(File_entry(cur_file.name,'...',True,False,True))
    for left_file in new_files_dic:
        #these files are completely new
        new_index_folder.append(File_entry(left_file,new_files_dic[left_file],True,True,True))
    new_index_folder.sort(key=lambda x:x.name)
    index.add_file_list_by_position(begin,end,new_entries=new_index_folder)
    index.write_to_file()

def status(root_dir : Path, file : Path):
    #returns the status of a file (untracked,changed but not commited, staged)
    project_dir = root_dir.parent
    index = Index.from_file(root_dir)
    file_name = str(file)
    name_dir = str(project_dir)
    if name_dir=='.': name_dir=''
    file_name = file_name.removeprefix(str(project_dir)+'/')
    position = index.find_file_in_index(file_name)
    cur_entry = index.files[position]
    if cur_entry.name!=file_name:
        return 'Untracked'
    if not file.exists():
        if not cur_entry.exists:
            return 'Staged'
        return 'Changed'
    hash = sha1_file(file)
    if hash!=cur_entry.hash:
        return 'Changed'
    if cur_entry.changed:
        return 'Staged'
    return 'Unchanged'

def show_index(root_dir : Path):
    index_file = root_dir / 'index'
    with index_file.open('rb') as index_opened:
        index_compressed = index_opened.read()    
    index_content = zlib.decompress(index_compressed)
    index_text = index_content.decode('utf-8')
    forprint = ''
    for ch in index_text:
        if ch=='\x1e': forprint+='\n'
        elif ch=='\x1d': forprint+=' '
        else: forprint+=ch
    return forprint

class NonExistentTree(Exception):
    def __init__(self, message):
        self.message=message
        super().__init__(message)

def print_tree(root_dir : Path, tree_name : str):
    tree_obj = (root_dir / 'objects' / tree_name)
    with (tree_obj.open('rb')) as tree_opened:
        tree_compr = tree_opened.read()
    tree_bytes = zlib.decompress(tree_compr)
    tree_text = tree_bytes.decode('utf-8')
    tree_info = tree_text.split('\x1e')
    answer = []
    if tree_info[0]!='.': 
        answer.append(tree_info[0]+":")
    num_files = int(tree_info[1])
    for line in tree_info[2:2+num_files]:
        spl = line.split('\x1d')
        if tree_info[0]!='.': answer.append(' '+spl[0])
        else: answer.append(spl[0])
    num_folders = int(tree_info[2+num_files])
    for line in tree_info[3+num_files:3+num_files+num_folders]:
        spl = line.split('\x1d')
        cur_ans = print_tree(root_dir,spl[1])
        for new_line in cur_ans:
            if tree_info[0]!='.': answer.append(' '+new_line)
            else: answer.append(new_line)
    return answer

def ls_tree(root_dir : Path, commit_name : str):
    #returns how the directory looks in the given commit
    head_file = root_dir / 'HEAD'
    with head_file.open('rb') as head_opened:
        cur_branch = head_opened.read()
    cur_branch = cur_branch.decode('utf-8')
    branch_head = root_dir / 'refs' / 'heads' / cur_branch
    with branch_head.open('rb') as branch_head_opened:
        last_commit = branch_head_opened.read()
    last_commit = last_commit.decode('utf-8')
    if commit_name=='last': commit_name=last_commit
    commit_obj = root_dir / 'objects' / commit_name
    if not commit_obj.exists():
        raise NonExistentTree("The commit does not exist")
    with (commit_obj.open('rb')) as commit_opened:
        commit_compr = commit_opened.read()
    commit_bytes = zlib.decompress(commit_compr)
    commit_text = commit_bytes.decode('utf-8')
    commit_info = commit_text.split('\x1e')
    if len(commit_info)<4:
        raise NonExistentTree("The commit does not exist")
    result = print_tree(root_dir,commit_info[2])
    text_result = ''
    for line in result:
        text_result+=line
        text_result+='\n'
    return text_result

def branch_list(root_dir : Path):
    head_file = root_dir / 'HEAD'
    with head_file.open('rb') as head_opened:
        cur_branch = head_opened.read()
    cur_branch = cur_branch.decode('utf-8')
    print_text = ""
    refs_heads = root_dir / 'refs' / 'heads'
    last_commit = '-1'
    for file in refs_heads.iterdir():
        if file.name == cur_branch:
            print_text+='\033[32m'+file.name+'\033[0m *\n'
        else: print_text+=file.name+'\n'
    return print_text

class NonExistentBranch(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)

def get_file_decompr(file : Path):
    with file.open('rb') as opened:
        compressed = opened.read()
    decompressed = zlib.decompress(compressed)
    raw_text = decompressed.decode('utf-8')
    answer = raw_text.split('\x1e')
    return answer

def find_common_ancestor(object_folder : Path, commit1 : str, commit2 : str):
    dict = {
        commit1 : 1
    }
    commit1_file = object_folder / commit1
    commit1_info = get_file_decompr(commit1_file)
    father = commit1_info[1]
    while True:
        dict[father]=1
        if father == '-': break
        father_file = object_folder / father
        with father_file.open('rb') as opened1:
            father_info = (zlib.decompress(opened1.read()).decode('utf-8')).split('\x1e')
        father = father_info[1]
    if commit2 in dict:
        return commit2
    commit2_file = object_folder / commit2
    commit2_info = get_file_decompr(commit2_file)
    father = commit2_info[1]
    while True:
        if father in dict: return father
        father_file = object_folder / father
        with father_file.open('rb') as opened3:
            father_info = (zlib.decompress(opened3.read()).decode('utf-8')).split('\x1e')
        father = father_info[1]

def fast_forward_merge(root_dir : Path, branch_name : str, cur_branch_file, commit_them : str):
    try:
        checkout(root_dir,branch_name)
    except UncommitedChanges as error:
        raise error
    cur_branch_file.write_text(commit_them)

def find_all_changes(object_dir : Path, lca_tree : str, us_tree : str, them_tree : str):
    if lca_tree!='...': lca_info = get_file_decompr(object_dir / lca_tree)
    else: lca_info = ['none','0','0']
    if us_tree!='...': us_info= get_file_decompr(object_dir / us_tree)
    else: us_info = ['none','0','0']
    if them_tree!='...': them_info = get_file_decompr(object_dir / them_tree)
    else: them_info = ['none','0','0']
    lca_files = {}
    lca_folders = {}
    lca_num_files = int(lca_info[1])
    lca_num_folders = int(lca_info[2+lca_num_files])
    for line in lca_info[2:2+lca_num_files]:
        spl = line.split('\x1d')
        lca_files[spl[0]]=spl[1]
    for line in lca_info[3+lca_num_files:3+lca_num_files+lca_num_folders]:
        spl = line.split('\x1d')
        lca_folders[spl[0]]=spl[1]
    us_files = {}
    us_folders = {}
    us_num_files = int(us_info[1])
    us_num_folders = int(us_info[2+us_num_files])
    for line in us_info[2:2+us_num_files]:
        spl = line.split('\x1d')
        us_files[spl[0]]=spl[1]
    for line in us_info[3+us_num_files:3+us_num_files+us_num_folders]:
        spl = line.split('\x1d')
        us_folders[spl[0]]=spl[1]
    changes = []
    them_num_files = int(them_info[1])
    them_num_folders = int(them_info[2+them_num_files])
    for line in them_info[2:2+them_num_files]:
        spl = line.split('\x1d')
        if spl[0] not in us_files:
            if spl[0] in lca_files:
                changes.append([spl[0],lca_files[spl[0]],'...',spl[1]])
            else:
                changes.append([spl[0],'...','...',spl[1]])
        else:
            if spl[1] != us_files[spl[0]]:
                if spl[0] in lca_files:
                    changes.append([spl[0],lca_files[spl[0]],us_files[spl[0]],spl[1]])
                else:
                    changes.append([spl[0],'...',us_files[spl[0]],spl[1]])
            us_files.pop(spl[0])
    for key, value in us_files.items():
        if key in lca_files:
            changes.append([key,lca_files[key],value,'...'])
        else:
            changes.append([key,'...',value,'...'])
    for line in them_info[3+them_num_files:3+them_num_files+them_num_folders]:
        spl = line.split('\x1d')
        if spl[0] not in us_folders:
            if spl[0] in lca_folders:
                new_changes = find_all_changes(object_dir,lca_folders[spl[0]],'...',spl[1])
            else:
                new_changes = find_all_changes(object_dir,'...','...',spl[1])
        else:
            if spl[1] != us_folders[spl[0]]:
                if spl[0] in lca_folders:
                    new_changes = find_all_changes(object_dir,lca_folders[spl[0]],us_folders[spl[0]],spl[1])
                else:
                    new_changes = find_all_changes(object_dir,'...',us_folders[spl[0]],spl[1])
            else:
                new_changes = []
            us_folders.pop(spl[0])
        for change in new_changes:
            changes.append(change)
    for key, value in us_folders.items():
        if key in lca_folders:
            new_changes = find_all_changes(object_dir,lca_folders[key],value,'...')
        else:
            new_changes = find_all_changes(object_dir,'...',value,'...')
        for change in new_changes:
            changes.append(change)
    return changes

class ConflictingChanges(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)

def merge(root_dir : Path, branch_name : str, ask_for_comm_name : bool = True):
    #merges branch with branch_name to the current branch
    index = Index.from_file(root_dir)
    for cur_entry in index.files:
        if cur_entry.changed:
            raise UncommitedChanges('Please commit all changes before merging branches.')
    head_file = root_dir / 'HEAD'
    with head_file.open('rb') as head_opened:
        cur_branch = head_opened.read()
    cur_branch = cur_branch.decode('utf-8')
    if cur_branch==branch_name: return False
    refs_heads = root_dir / 'refs' / 'heads'
    last_commit_them = '-1'
    for file in refs_heads.iterdir():
        if file.name == branch_name:
            with file.open('rb') as file_opened:
                last_commit_them = file_opened.read()
    cur_branch_file = refs_heads / cur_branch
    with cur_branch_file.open('rb') as cur_opened:
        last_commit_us = cur_opened.read()
    if last_commit_them=='-1':
        #branch does not exist
        raise NonExistentBranch('Branch '+branch_name+' does not exist.')
    last_commit_us = last_commit_us.decode('utf-8')
    last_commit_them = last_commit_them.decode('utf-8')
    object_folder = root_dir / 'objects'
    lca = find_common_ancestor(object_folder,last_commit_us,last_commit_them)
    if lca == last_commit_them:
        return 0
    if lca == last_commit_us:
        try:
            fast_forward_merge(root_dir,branch_name,cur_branch_file,last_commit_them)
        except UncommitedChanges as error:
            raise UncommitedChanges(error.message)
        return 1
    #here we have to do a 3-way merge
    #first I want a list of all files that are different in us and them
    #then i have to retrieve what they are in the lca commit
    commit1_file = root_dir / 'objects' / last_commit_us
    commit_us_tree = (get_file_decompr(commit1_file))[2]
    commit2_file = root_dir / 'objects' / last_commit_them
    commit_them_tree = (get_file_decompr(commit2_file))[2]
    commit3_file = root_dir / 'objects' / lca
    lca_tree = (get_file_decompr(commit3_file))[2]
    if ask_for_comm_name: new_merge_commit = input('Feed forward merge cannot be performed. Enter commit message for 3-way-merge:\n')
    else: new_merge_commit = f'Merge commit for the temperary {cur_branch} with {branch_name}' 
    all_changes = find_all_changes(object_dir=(root_dir / 'objects'),lca_tree=lca_tree,us_tree=commit_us_tree,them_tree=commit_them_tree)
    project_dir_name = str(root_dir.parent)
    do_change = []
    for change in all_changes:
        if change[1]!=change[2] and change[1]!=change[3]:
            raise ConflictingChanges('There are conflicting changes between the branches.')
        elif change[1]==change[2]:
            cur_file = Path(project_dir_name+'/'+change[0])
            if cur_file.exists():
                cur_hash = sha1_file(cur_file)
                if cur_hash!=change[2]:
                    raise ConflictingChanges('There are conflicting changes in the current branch, not added to index.')
            else:
                if change[2]!='...':
                    raise ConflictingChanges('There are conflicting changes in the current branch, not added to index.')
            do_change.append([change[0],change[3]])
    index.add_file_list_general(do_change)
    print(index.turn_to_text())
    index.write_to_file()
    for change in do_change:
        file_obj = Path(project_dir_name+'/'+change[0])
        if (change[1]=='...'):
            file_obj.unlink()
            cname = get_folder(change[0])
            while True:
                if cname == '.': break
                cur_folder = (root_dir.parent) / cname
                is_empty = not any(cur_folder.iterdir())
                if is_empty:
                    cur_folder.rmdir()
                else: break
                cname = get_folder(cname)
        else:
            print(change[0])
            with (root_dir / 'objects' / change[1]).open('rb') as file_opened:
                file_compressed = file_opened.read()
            file_bytes = zlib.decompress(file_compressed)
            create_file(file_obj,file_bytes)
    commit(root_dir,new_merge_commit)
    return 2

def iterate_tree(root_dir : Path, main_tree : str):
    if main_tree=='-':
        return []
    tree_info = get_file_decompr(root_dir / 'objects' / main_tree)
    ans = [ [tree_info[0],main_tree,False] ]
    num_files = int(tree_info[1])
    for line in tree_info[2:2+num_files]:
        spl = line.split('\x1d')
        ans.append([spl[0],spl[1],True])
    num_folders = int(tree_info[2+num_files])
    for line in tree_info[3+num_files:3+num_files+num_folders]:
        spl = line.split('\x1d')
        ans_child = iterate_tree(root_dir,spl[1])
        for new_ans in ans_child:
            ans.append(new_ans)
    return ans

def put_content_after_clone(root_dir : Path):
    project_dir = root_dir.parent
    refs_heads = root_dir / 'refs' / 'heads' / 'Main'
    with refs_heads.open('rb') as opened:
        refs_heads_text = (opened.read()).decode('utf-8')
    last_commit = root_dir / 'objects' / refs_heads_text
    head_file = root_dir / 'HEAD'
    head_file.write_text('Main')
    contents = List[list]
    index = Index(root_dir)
    if refs_heads_text != '-':
        commit_info = get_file_decompr(last_commit)
        main_tree = commit_info[2]
        contents = iterate_tree(root_dir, main_tree)
    for content in contents:
        if content[2]:
            index.files.append(File_entry(name=content[0],hash=content[1],has_bools=True,exists=True,changed=False))
            blob_file = Pit_file(file_object=root_dir / 'objects' / content[1],is_compr=True)
            new_file = project_dir / content[0]
            create_file(new_file,blob_file.get_value_bytes())
        else:
            index.trees.append(File_entry(name=content[0],hash=content[1]))
    index.number_of_files = len(index.files)
    index.number_of_trees = len(index.trees)
    index.write_to_file(sort_files=True,sort_trees=True)