from pathlib import Path
import hashlib
import zlib
from logic_classes import (
    Pit_file,
    Index,
    File_entry,
    Tree,
    Commit,
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
    compressor = zlib.compressobj()
    with file.open('rb') as f_in, blob.open('wb') as b_out:
        while chunk := f_in.read(8192):
            compressed_chunk = compressor.compress(chunk)
            if compressed_chunk:
                b_out.write(compressed_chunk)
        b_out.write(compressor.flush())
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
    Main_tree = Tree(objects_folder / '...')
    Main_tree.name = '.'
    Main_tree.write_to_file(fix=True)
    First_commit = Commit(object_file=(objects_folder / '...'),message='Created repository!',head_tree=Main_tree.hash,father='-')
    First_commit.write_to_file(fix=True)
    Main_commit = refs_heads_folder / 'Main'
    Main_commit.write_text(First_commit.hash)
    index_file = Index(dot_pit_folder)
    index_file.number_of_trees = 1
    index_file.trees.append(File_entry(name='.',hash=Main_tree.hash))
    index_file.write_to_file()
    return True

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
            cur_file_entry = index.files[position]
            if cur_file_entry.hash==hash:
                #means nothing was changed, so we shouldnt change nothing
                return
            #here the file was actually changed
            index.files[position].hash = hash
            index.files[position].changed = True
        index.write_to_file()    
    else:
        #means file was deleted
        #we want to change exist property to false and changed property to true
        if index.number_of_files == 0: return # there arent blobs, so 
        position = index.find_file_in_index(file_name)
        if position==-1: return #the file wasnt in the index, so no need to do anything
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

def commit(root_dir : Path, commit_message : str) -> str:
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
    changed_file_entry : List[File_entry] = []
    for ch in changed:
        changed_file_entry.append(File_entry(name=ch[0],only_exists=True,exists=ch[1]))
    new_commit = Commit(object_file=(root_dir / 'objects' / '...'),
                        message=commit_message,
                        head_tree=root_tree,
                        num_changes=len(changed),
                        changes=changed_file_entry,
                        father=previous_commit)
    new_commit.write_to_file(fix=True)
    branch_head.write_value_from_text(new_commit.hash)
    return new_commit.hash

def log(root_dir : Path) -> str:
    #returns information for all previous commits in current branch
    head_file = Pit_file(file_object=(root_dir / 'HEAD'))
    cur_branch = head_file.get_value_text()
    branch_head = Pit_file(root_dir / 'refs' / 'heads' / cur_branch)
    last_commit = branch_head.get_value_text()
    log_text = ''
    while last_commit!='-':
        cur_commit = Commit.from_file(object_file=(root_dir / 'objects' / last_commit))
        log_text+='Commit name:'+last_commit+'\n'
        log_text+='Commit message:'+cur_commit.message+'\n'
        changed = 0
        removed = 0
        for cur_entry in cur_commit.changes:
            if cur_entry.exists: changed+=1
            else: removed+=1
        log_text+='Changed '+str(changed)+' files.\n'
        log_text+='Removed '+str(removed)+' files.\n'
        log_text+='\n\n'
        last_commit=cur_commit.get_father()
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
            return cur_entry.hash
        return False
    else:
        #this means we are searching for a folder inside the list of folders
        for cur_entry in tree.trees:
            if file_name.startswith(cur_entry.name):
                return find_file(root_dir,cur_entry.hash,file_name)
        return False

def create_file(file : Path, blob : Path):
    unexist = []
    copy = file.parent
    while not copy.exists():
        unexist.append(copy)
        copy = copy.parent
    unexist.reverse()
    for un in unexist:
        un.mkdir()
    decompressor = zlib.decompressobj()
    with blob.open('rb') as b_in, file.open('wb') as f_out:
        while chunk := b_in.read(8192):
            decompressed_chunk = decompressor.decompress(chunk)
            if decompressed_chunk:
                f_out.write(decompressed_chunk)
        f_out.write(decompressor.flush())

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
        cur_commit = Commit.from_file(object_file=(root_dir / 'objects' / last_commit))
        last_commit = cur_commit.get_father()
    last_commit_file = Commit.from_file(object_file=(root_dir / 'objects' / last_commit))
    cur_tree = last_commit_file.head_tree
    file_hash = find_file(root_dir,cur_tree,file_name)
    if file_hash == False:
        raise UnableToRetrieve('There is no file '+file_name+' in the repository of commit '+commit_name+'.\n')
    if create: create_file(file=create_place,blob=(root_dir / 'objects' / file_hash))
    else:
        blob_obj = root_dir / 'objects' / file_hash
        if blob_obj.stat().st_size > 300:
            raise UnableToRetrieve(f'File {file_name} is too big to print as text\n')
        with blob_obj.open('rb') as opened:
            bytes1 = opened.read()
        bytes_dec = zlib.decompress(bytes1)
        return bytes_dec

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
    tree_struct = Tree.from_file(object_file=(root_dir / 'objects' / new_tree))
    changes = [IndexChanges(True, True, tree_struct.name, new_tree, 1, '')]
    for cur_entry in tree_struct.files:
        changes.append(IndexChanges(True, True, cur_entry.name, cur_entry.hash, 0, ''))
    for cur_entry in tree_struct.trees:
        changes.extend(complete_add_tree(root_dir, cur_entry.hash))
    return changes

def complete_delete_tree(root_dir : Path , old_tree : str) -> List[IndexChanges]:
    #iterates through the entire tree and adds IndexChanges for deletion for every file
    tree_struct = Tree.from_file(object_file=(root_dir / 'objects' / old_tree))
    changes = [IndexChanges(False, False, tree_struct.name, old_tree, 1, '')]
    for cur_entry in tree_struct.files:
        changes.append(IndexChanges(False, False, cur_entry.name, cur_entry.hash, 0, cur_entry.hash))
    for cur_entry in tree_struct.trees:
        changes.extend(complete_delete_tree(root_dir, cur_entry.hash))
    return changes

def fix_tree(root_dir : Path, new_tree : str, old_tree : str) -> List[IndexChanges]:
    #returns the changes needed to sync new_tree and old_tree
    new_tree_struct = Tree.from_file(object_file=(root_dir / 'objects' / new_tree)) 
    old_tree_struct = Tree.from_file(object_file=(root_dir / 'objects' / old_tree)) 
    file_dic = {}
    folder_dic = {}
    changes = [IndexChanges(True,False,new_tree_struct.name,new_tree,1,'')]
    for cur_entry in old_tree_struct.files:
        file_dic[cur_entry.name]=cur_entry.hash
    for cur_entry in new_tree_struct.files:
        if cur_entry.name in file_dic:
            #its in the dictionary
            if cur_entry.hash!=file_dic[cur_entry.name]:
                #its changed
                changes.append(IndexChanges(True,False,cur_entry.name,cur_entry.hash,0,file_dic[ cur_entry.name ]))
            file_dic.pop(cur_entry.name)
        else:
            #its not so its new
            changes.append(IndexChanges(True,True,cur_entry.name,cur_entry.hash,0,''))
    for left in file_dic:
        #all of these were in old but not in new
        changes.append(IndexChanges(False,False,left,file_dic[left],0,file_dic[left]))
    for cur_entry in old_tree_struct.trees:
        folder_dic[cur_entry.name]=cur_entry.hash
    for cur_entry in new_tree_struct.trees:
        if cur_entry.name in folder_dic:
            #its in the dic
            if cur_entry.hash!=folder_dic[cur_entry.name]:
                #there are changes in the folder
                new_changes = fix_tree(root_dir,cur_entry.hash,folder_dic[cur_entry.name])
                for change in new_changes: changes.append(change)
            folder_dic.pop(cur_entry.name)
        else:
            new_changes = complete_add_tree(root_dir,cur_entry.hash)
            for change in new_changes: changes.append(change)
    for left in folder_dic:
        #all of those folders dont exist anymore
        new_changes = complete_delete_tree(root_dir,folder_dic[left])
        changes.extend(new_changes)
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
    if last_commit!='-':
        commit_obj = Commit.from_file(root_dir / 'objects' / last_commit)
        new_tree = commit_obj.head_tree
    else:
        new_tree = '-'
    old_tree = index.trees[0].hash
    if old_tree==new_tree:
        #there arent any changes between the two branches, so we can just change
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
            create_file(cur_file,root_dir / 'objects' / change.blob)
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
    if index.number_of_files == 0:
        return 'Untracked'
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
    tree_struct = Tree.from_file(object_file=(root_dir / 'objects' / tree_name))
    answer = []
    if tree_struct.name != '.':
        answer.append(tree_struct.name + ":")
    for cur_file in tree_struct.files:
        if tree_struct.name != '.': answer.append(' ' + cur_file.name)
        else: answer.append(cur_file.name)
    for cur_tree in tree_struct.trees:
        cur_ans = print_tree(root_dir, cur_tree.hash)
        for new_line in cur_ans:
            if tree_struct.name != '.': answer.append(' ' + new_line)
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
    commit_file = root_dir / 'objects' / commit_name
    if not commit_file.exists():
        raise NonExistentTree("The commit does not exist")
    commit_object = Commit.from_file(commit_file)
    result = print_tree(root_dir,commit_object.head_tree)
    text_result = ''
    for line in result:
        text_result+=line
        text_result+='\n'
    return text_result

def branch_list(root_dir : Path):
    head_file = Pit_file(root_dir / 'HEAD')
    cur_branch = head_file.get_value_text()
    print_text = ""
    refs_heads = root_dir / 'refs' / 'heads'
    for file in refs_heads.iterdir():
        if file.name == cur_branch:
            print_text+='\033[32m'+file.name+'\033[0m *\n'
        else: print_text+=file.name+'\n'
    return print_text

class NonExistentBranch(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)

def find_common_ancestor(object_folder : Path, commit1 : str, commit2 : str):
    dict = {
        commit1 : 1
    }
    commit1_file = object_folder / commit1
    commit1_obj = Commit.from_file(commit1_file)
    father = commit1_obj.get_father()
    while True:
        dict[father]=1
        if father == '-': break
        father_file = object_folder / father
        father_commit = Commit.from_file(father_file)
        if father_commit.brother is not None: dict[father_commit.brother] = 1
        #print(father_commit.brother)
        father = father_commit.get_father()
    if commit2 in dict:
        return commit2
    commit2_file = object_folder / commit2
    commit2_obj = Commit.from_file(commit2_file)
    father = commit2_obj.get_father()
    while True:
        if father in dict: return father
        father_file = object_folder / father
        father_commit = Commit.from_file(father_file)
        if (father_commit.brother is not None) and father_commit.brother in dict: return father
        father = father_commit.get_father()

def fast_forward_merge(root_dir : Path, branch_name : str, cur_branch_file : Pit_file, commit_them : str):
    try:
        checkout(root_dir,branch_name)
    except UncommitedChanges as error:
        raise error
    cur_branch_file.write_value_from_text(commit_them)

def find_all_changes(object_dir : Path, lca_tree : str, us_tree : str, them_tree : str):
    def load_tree_maps(tree_hash: str):
        if tree_hash == '...':
            return {}, {}
        tree = Tree.from_file(object_file=(object_dir / tree_hash))
        files = {entry.name: entry.hash for entry in tree.files}
        folders = {entry.name: entry.hash for entry in tree.trees}
        return files, folders
    lca_files, lca_folders = load_tree_maps(lca_tree)
    us_files, us_folders = load_tree_maps(us_tree)
    them_files, them_folders = load_tree_maps(them_tree)
    changes = []
    for name, them_hash in them_files.items():
        if name not in us_files:
            if name in lca_files:
                changes.append([name, lca_files[name], '...', them_hash])
            else:
                changes.append([name, '...', '...', them_hash])
        else:
            if them_hash != us_files[name]:
                if name in lca_files:
                    changes.append([name, lca_files[name], us_files[name], them_hash])
                else:
                    changes.append([name, '...', us_files[name], them_hash])
            us_files.pop(name)
    for name, us_hash in us_files.items():
        if name in lca_files:
            changes.append([name, lca_files[name], us_hash, '...'])
        else:
            changes.append([name, '...', us_hash, '...'])
    for name, them_hash in them_folders.items():
        if name not in us_folders:
            if name in lca_folders:
                new_changes = find_all_changes(object_dir, lca_folders[name], '...', them_hash)
            else:
                new_changes = find_all_changes(object_dir, '...', '...', them_hash)
        else:
            if them_hash != us_folders[name]:
                if name in lca_folders:
                    new_changes = find_all_changes(object_dir, lca_folders[name], us_folders[name], them_hash)
                else:
                    new_changes = find_all_changes(object_dir, '...', us_folders[name], them_hash)
            else:
                new_changes = []
            us_folders.pop(name)
        changes.extend(new_changes)
    for name, us_hash in us_folders.items():
        if name in lca_folders:
            new_changes = find_all_changes(object_dir, lca_folders[name], us_hash, '...')
        else:
            new_changes = find_all_changes(object_dir, '...', us_hash, '...')
        changes.extend(new_changes)
    return changes

class ConflictingChanges(Exception):
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)

def merge(root_dir : Path, branch_name : str, ask_for_comm_name : bool = True, create_brother : bool = False):
    #merges branch with branch_name to the current branch
    index = Index.from_file(root_dir)
    for cur_entry in index.files:
        if cur_entry.changed:
            raise UncommitedChanges('Please commit all changes before merging branches.')
    head_file = Pit_file(root_dir / 'HEAD')
    cur_branch = head_file.get_value_text()
    if cur_branch==branch_name: return False
    refs_heads = root_dir / 'refs' / 'heads'
    last_commit_them = '-1'
    for file in refs_heads.iterdir():
        if file.name == branch_name:
            them_file = Pit_file(file)
            last_commit_them = them_file.get_value_text()
    cur_branch_file = Pit_file(refs_heads / cur_branch)
    last_commit_us = cur_branch_file.get_value_text()
    object_folder = root_dir / 'objects'
    if last_commit_them=='-1':
        #branch does not exist
        raise NonExistentBranch('Branch '+branch_name+' does not exist.')
    commit1_file = Commit.from_file(object_folder / last_commit_us)
    commit2_file = Commit.from_file(object_folder / last_commit_them)
    if commit1_file.brother == commit2_file.hash:
        return False
    if commit2_file.brother == commit1_file.hash:
        return False
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
    commit_us_tree = commit1_file.head_tree
    commit_them_tree = commit2_file.head_tree
    commit3_file = Commit.from_file(object_folder / lca)
    lca_tree = commit3_file.head_tree
    if ask_for_comm_name: new_merge_commit = input('Feed forward merge cannot be performed. Enter commit message for 3-way-merge:\n')
    else: new_merge_commit = f'Merge commit for the temperary {cur_branch} with {branch_name}' 
    all_changes = find_all_changes(object_dir=object_folder,lca_tree=lca_tree,us_tree=commit_us_tree,them_tree=commit_them_tree)
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
            #print(change[0])
            create_file(file_obj,root_dir / 'objects' / change[1])
    commit_hash = commit(root_dir,new_merge_commit)
    og_commit = Commit.from_file(root_dir / 'objects' / commit_hash)
    if create_brother:
        new_commit_changes : List[File_entry] = []
        for change in all_changes:
            if change[1]==change[3]:
                if change[2]=='...':
                    new_commit_changes.append(File_entry(name=change[0],only_exists=True,exists=False))
                else:
                    new_commit_changes.append(File_entry(name=change[0],only_exists=True,exists=True))
        new_commit = Commit(object_file=(root_dir / 'objects' / '...'), 
                            message=new_merge_commit,
                            head_tree=og_commit.head_tree,
                            num_changes=len(new_commit_changes),
                            changes=new_commit_changes,
                            father=last_commit_them,
                            brother=commit_hash)
        new_commit.write_to_file(fix=True)
        them_file.write_value_from_text(new_commit.hash)
    return 2

def iterate_tree(root_dir : Path, main_tree : str):
    if main_tree == '-':
        return []
    tree_struct = Tree.from_file(object_file=(root_dir / 'objects' / main_tree))
    ans = [[tree_struct.name, main_tree, False]]
    for cur_file in tree_struct.files:
        ans.append([cur_file.name, cur_file.hash, True])
    for cur_tree in tree_struct.trees:
        ans.extend(iterate_tree(root_dir, cur_tree.hash))
    return ans

def put_content_after_clone(root_dir : Path):
    project_dir = root_dir.parent
    refs_heads = Pit_file(root_dir / 'refs' / 'heads' / 'Main')
    refs_heads_text = refs_heads.get_value_text()
    if refs_heads_text == '-':
        objects_folder = root_dir / 'objects'
        Main_tree = Tree(objects_folder / '...')
        Main_tree.name = '.'
        Main_tree.write_to_file(fix=True)
        First_commit = Commit(object_file=(objects_folder / '...'),message='Created repository!',head_tree=Main_tree.hash,father='-')
        First_commit.write_to_file(fix=True)
        last_commit = First_commit
        refs_heads.write_value_from_text(last_commit.hash)
    else:
        last_commit_file = root_dir / 'objects' / refs_heads_text
        last_commit = Commit.from_file(last_commit_file)
    head_file = root_dir / 'HEAD'
    head_file.write_text('Main')
    contents : List[list] = []
    index = Index(root_dir)
    if refs_heads_text != '-':
        main_tree = last_commit.head_tree
        contents = iterate_tree(root_dir, main_tree)
    for content in contents:
        if content[2]:
            index.files.append(File_entry(name=content[0],hash=content[1],has_bools=True,exists=True,changed=False))
            new_file = project_dir / content[0]
            create_file(new_file,root_dir / 'objects' / content[1])
        else:
            index.trees.append(File_entry(name=content[0],hash=content[1]))
    index.number_of_files = len(index.files)
    index.number_of_trees = len(index.trees)
    if index.number_of_trees == 0:
        index.number_of_trees = 1
        index.trees.append(File_entry(name='.',hash=Main_tree.hash))
    index.write_to_file(sort_files=True,sort_trees=True)
    