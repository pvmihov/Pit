from pathlib import Path
import hashlib
import zlib

def sha1_file(file):
    #returns sha-1 encryption of file
    hash = hashlib.sha1()
    with file.open('rb') as curfile:
        while chunk := curfile.read(8192):
            hash.update(chunk)
    return hash.hexdigest()

def create_blob(root_dir, file):
    #creates blob in the objects folder
    hash = sha1_file(file)
    blob = root_dir / 'objects' / hash
    if blob.exists():
        return hash
    open_file = file.open('rb')
    compressed_data = zlib.compress(open_file.read()) #has to be remade for big file openings
    blob.write_bytes(compressed_data)
    return hash

def init(project_dir):
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

def find_index(index,num_blobs,file_name):
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

def add_file(root_dir,file):
    if file.resolve().is_relative_to(root_dir.resolve()): return
    #runs command pit add file
    #receives a path object called file and changes the index accordingly
    project_dir = root_dir.parent
    index_file = root_dir / 'index'
    index = decompress_index(index_file)
    num_blobs = int(index[0])
    file_name = str(file)
    name_dir = str(project_dir)
    if name_dir=='.': name_dir=''
    file_name = file_name.removeprefix(str(project_dir)+'/')
    if file.exists():
        #means file was updated
        hash = create_blob(root_dir,file)
        creation = -1
        if num_blobs == 0:
            #we have to create the file, it is also the first file
            creation = 0
        else: 
            position = find_index(index,num_blobs,file_name)
            if position==0:
                creation = position
            cur_position_split = index[position].split('\x1d')
            if cur_position_split[0]!=file_name: 
                creation = position
        if creation!=-1:
            #this means we have to create the file
            new_index_text = str(num_blobs+1)+'\x1e'
            for i in range(1,creation+1): new_index_text+=(index[i]+'\x1e')
            new_index_text+=(file_name+'\x1d'+hash+'\x1dTrue\x1dTrue\x1e')
            for i in range(creation+1,len(index)): new_index_text+=(index[i]+'\x1e')
            new_index_bytes = new_index_text.encode('utf-8')
            new_index_compressed = zlib.compress(new_index_bytes)
            index_file.write_bytes(new_index_compressed)   
        else:
            #this means file is in the index at line, position
            cur_position_split = index[position].split('\x1d')
            if cur_position_split[1]==hash:
                #means nothing was changed, so we shouldnt change nothing
                return
            #here the file was actually changed
            cur_position_split[1]=hash
            index[position]=cur_position_split[0]+'\x1d'+cur_position_split[1]+'\x1dTrue\x1dTrue'
            new_index_text = ''
            for tex in index: new_index_text+=(tex+'\x1e')
            new_index_bytes = new_index_text.encode('utf-8')
            new_index_compressed = zlib.compress(new_index_bytes)
            index_file.write_bytes(new_index_compressed)
    else:
        #means file was deleted
        #we want to change exist property to false and changed property to true
        if num_blobs == 0: return # there arent blobs, so 
        position = find_index(index,num_blobs,file_name)
        if position==0: return #the file wasnt in the index, so no need to do anything
        cur_position_split = index[position].split('\x1d')
        if cur_position_split[0]!=file_name: return #the file wasnt in the index
        #if we are here this means that the file is actually in index and we need to change the information
        if cur_position_split[2] != 'False' or cur_position_split[2]!='True':
            new_index_text = ''
            index[position]=cur_position_split[0]+'\x1d'+'...'+'\x1d'+'False'+'\x1d'+'True'
            for tex in index: new_index_text+=(tex+'\x1e')
            new_index_bytes = new_index_text.encode('utf-8')
            new_index_compressed = zlib.compress(new_index_bytes)
            index_file.write_bytes(new_index_compressed)

class Tree_node:
    def __init__(self):
        self.hash = ''
        self.father = ""
        self.name = ""
        self.num_files = 0
        self.file_names = []
        self.file_blobs = []
        self.num_trees = 0
        self.tree_names = []
        self.tree_blobs = [] 
        
def get_folder(file_name):
    #receives the name of a file, and returns what folder its in
    slash = -1
    for i in range(0,len(file_name)):
        if file_name[i]=='/': slash=i
    if slash == -1: return '.'
    par_name=''
    for i in range(0,slash): par_name+=file_name[i]
    return par_name

def sha1_text(text):
    #returns sha1 encryption of text
    hash = hashlib.sha1()
    hash.update(text.encode('utf-8'))
    return hash.hexdigest()

def create_tree(root_dir,tree_info):
    hash = sha1_text(tree_info)
    blob = root_dir / 'objects' / hash
    if blob.exists():
        return hash
    compressed_data=zlib.compress(tree_info.encode('utf-8'))
    blob.write_bytes(compressed_data)
    return hash

def commit(root_dir,commit_message):
    #commits the changes in index
    project_dir = root_dir.parent
    index_file = root_dir / 'index'
    index = decompress_index(index_file)
    num_blobs = int(index[0])
    num_trees = 1
    tree_dic={
        '.': 0
    }
    tree_array = []
    tree_array.append(Tree_node())
    tree_array[0].name = '.'
    changed = []
    existing_files = 0
    for i in range(1,num_blobs+1):
        splited = index[i].split('\x1d')
        if splited[3]=='True':
            changed.append([splited[0],splited[2]])
        if splited[2]=='False': 
            continue
        existing_files+=1
        father = get_folder(splited[0])
        num = -1
        if father in tree_dic:
            num=tree_dic[father]
        else:
            tree_dic[father]=num_trees
            tree_array.append(Tree_node())
            tree_array[num_trees].name=father
            tree_array[num_trees].father = get_folder(father)
            num=num_trees
            num_trees+=1
        tree_array[num].num_files+=1
        tree_array[num].file_names.append(splited[0])
        tree_array[num].file_blobs.append(splited[1])
        while True:
            father = get_folder(father)
            if father in tree_dic: break
            tree_dic[father]=num_trees
            tree_array.append(Tree_node())
            tree_array[num_trees].name=father
            tree_array[num_trees].father = get_folder(father)
            num_trees+=1
    new_index = str(existing_files)+'\x1e'
    for i in range(1,num_blobs+1):
        splited = index[i].split('\x1d')
        if splited[2]=='False': 
            continue
        new_index+=splited[0]+'\x1d'+splited[1]+'\x1dTrue\x1dFalse\x1e'
    new_index+=str(num_trees)+'\x1e'
    root_tree = ''
    for cur_key, cur_num in sorted(tree_dic.items(),reverse=True):
        cur_tree = tree_array[cur_num]
        tree_info = cur_tree.name+'\x1e'
        tree_info += str(cur_tree.num_files)+'\x1e'
        for i in range(0,cur_tree.num_files):
            tree_info+= cur_tree.file_names[i]+'\x1d'+cur_tree.file_blobs[i]+'\x1e'
        tree_info += str(cur_tree.num_trees)+'\x1e'
        for i in range(0,cur_tree.num_trees):
            tree_info+= cur_tree.tree_names[i]+'\x1d'+cur_tree.tree_blobs[i]+'\x1e'
        hash = create_tree(root_dir,tree_info)
        cur_tree.hash = hash
        if cur_tree.father=='':
            root_tree = hash
            continue
        par_num = tree_dic[cur_tree.father]
        tree_array[par_num].num_trees+=1
        tree_array[par_num].tree_names.append(cur_tree.name)
        tree_array[par_num].tree_blobs.append(hash)
    for cur_key, cur_num in sorted(tree_dic.items()):
        cur_tree = tree_array[cur_num]
        new_index+=cur_key+'\x1d'+cur_tree.hash+'\x1e'
    new_index_bytes = new_index.encode('utf-8')
    new_index_compressed = zlib.compress(new_index_bytes)
    index_file.write_bytes(new_index_compressed)
    head_file = root_dir / 'HEAD'
    with head_file.open('rb') as head_opened:
        cur_branch = head_opened.read()
    cur_branch = cur_branch.decode('utf-8')
    branch_head = root_dir / 'refs' / 'heads' / cur_branch
    with branch_head.open('rb') as branch_head_opened:
        previous_commit = branch_head_opened.read()
    previous_commit = previous_commit.decode('utf-8')
    commit_info = commit_message+'\x1e'+previous_commit+'\x1e'+root_tree+'\x1e'
    commit_info+=str(len(changed))+'\x1e'
    for ch in changed:
        commit_info+=ch[0]+'\x1d'+ch[1]+'\x1e'
    commit_hash = create_tree(root_dir=root_dir,tree_info=commit_info)
    branch_head.write_text(commit_hash)

def log(root_dir):
    #returns information for all previous commits in current branch
    index_file = root_dir / 'index'
    index = decompress_index(index_file)
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

def find_file(root_dir,cur_tree,file_name):
    tree_file = root_dir / 'objects' / cur_tree
    with tree_file.open('rb') as tree_file_opened:
        tree_compr = tree_file_opened.read()
    tree_text = zlib.decompress(tree_compr).decode('utf-8')
    tree_info = tree_text.split('\x1e')
    tree_info.pop()
    num_files = int(tree_info[1])
    if get_folder(file_name)==tree_info[0]:
        #this means we are searching for the file itself in the list of files
        for i in range(2,2+num_files):
            spl = tree_info[i].split('\x1d')
            if spl[0]!=file_name: continue
            file = root_dir / 'objects' / spl[1]
            with file.open('rb') as file_opened:
                file_compr = file_opened.read()
            file_bytes = zlib.decompress(file_compr)
            return file_bytes
        return False
    else:
        #this means we are searching for a folder inside the list of folders
        num_folders = int(tree_info[2+num_files])
        for i in range(3+num_files,3+num_files+num_folders):
            spl = tree_info[i].split('\x1d')
            if file_name.startswith(spl[0]):
                return find_file(root_dir,spl[1],file_name)
        return False

def create_file(file,bytes):
    unexist = []
    copy = file.parent
    while not copy.exists():
        unexist.append(copy)
        copy = copy.parent
    unexist.reverse()
    for un in unexist:
        un.mkdir()
    file.write_bytes(bytes)

def retrieve(root_dir,commit_name,file_name,create,create_place):
    #finds the file with file_name and the version it had after commit_name
    #if create is true, it creates the file in create_place
    #else it just returns the value as bits
    head_file = root_dir / 'HEAD'
    with head_file.open('rb') as head_opened:
        cur_branch = head_opened.read()
    cur_branch = cur_branch.decode('utf-8')
    branch_head = root_dir / 'refs' / 'heads' / cur_branch
    with branch_head.open('rb') as branch_head_opened:
        last_commit = branch_head_opened.read()
    last_commit = last_commit.decode('utf-8')
    log_text = ''
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
    def __init__(self,exists,new,name,blob,type,old_blob):
        self.exists = exists
        self.new = new
        self.name = name
        self.blob = blob
        self.type = type
        self.old_blob = old_blob

def complete_add_tree(root_dir,new_tree):
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

def complete_delete_tree(root_dir,old_tree):
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

def fix_tree(root_dir,new_tree,old_tree):
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

def checkout(root_dir,branch_name):
    #switches to another branch, if it doesnt exist it creates it
    #returns False when it creates a new branch, and True when it changes to an existing one
    index_file = root_dir / 'index'
    index = decompress_index(index_file)
    num_blobs = int(index[0])
    for i in range(1,1+num_blobs):
        spl = index[i].split('\x1d')
        if spl[3]=='True':
            raise UncommitedChanges('Please commit all changes before switching branches.')
    head_file = root_dir / 'HEAD'
    with head_file.open('rb') as head_opened:
        cur_branch = head_opened.read()
    cur_branch = cur_branch.decode('utf-8')
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
        with (refs_heads / cur_branch).open('rb') as cur_opened:
            cur_bytes = cur_opened.read()
        new_branch = refs_heads / branch_name
        new_branch.write_bytes(cur_bytes)
        head_file.write_text(branch_name)
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
    tr_spl = index[num_blobs+2].split('\x1d')
    old_tree = tr_spl[1]
    if old_tree==new_tree:
        #there arent any changes between the two branches, so we can just change
        with (refs_heads / cur_branch).open('rb') as cur_opened:
            cur_bytes = cur_opened.read()
        new_branch = refs_heads / branch_name
        new_branch.write_bytes(cur_bytes)
        head_file.write_text(branch_name)
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
    new_index_blobs = []
    for i in range(1,1+num_blobs):
        spl = index[i].split('\x1d')
        if spl[0] in for_deletion: continue
        elif spl[0] in for_change:
            new_index_blobs.append([spl[0],for_change[spl[0]]])
        else:
            new_index_blobs.append([spl[0],spl[1]])
    for change in changes:
        if change.type==1: continue
        if not change.new: continue
        new_index_blobs.append([change.name,change.blob])
    new_index_blobs.sort(key=lambda x:x[0])
    num_folders = int(index[1+num_blobs])
    new_index_folders = []
    for i in range(2+num_blobs,2+num_blobs+num_folders):
        spl = index[i].split('\x1d')
        if spl[0] in for_deletion: continue
        elif spl[0] in for_change:
            new_index_folders.append([spl[0],for_change[spl[0]]])
        else:
            new_index_folders.append(spl)
    for change in changes:
        if change.type==0: continue
        if not change.new: continue
        new_index_folders.append([change.name,change.blob])
    new_index_folders.sort(key=lambda x:x[0])
    new_index_text = str(len(new_index_blobs))+'\x1e'
    for new_blob in new_index_blobs:
        new_index_text += new_blob[0]+'\x1d'+new_blob[1]+'\x1dTrue\x1dFalse\x1e'
    new_index_text += str(len(new_index_folders))+'\x1e'
    for new_folder in new_index_folders:
        new_index_text += new_folder[0]+'\x1d'+new_folder[1]+'\x1e'
    for change in changes:
        if change.type==1: continue
        cur_file = (root_dir.parent) / change.name
        if not change.exists:
            cur_file.unlink()
            #print('delete '+str(cur_file.parent)+'/'+cur_file.name)
        else:
            #print('change '+str(cur_file.parent)+'/'+cur_file.name)
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
    new_index_bytes = new_index_text.encode('utf-8')
    new_index_compressed = zlib.compress(new_index_bytes)
    index_file.write_bytes(new_index_compressed)
    head_file.write_text(branch_name)
    return True

def list_files_in_dir(root_dir, folder_dir, folder_name, project_name):
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

def add_folder(root_dir, folder_dir):
    if folder_dir.resolve().is_relative_to(root_dir.resolve()): return
    #adds the contents of an entire folder to the index
    #also checks for removed material, and flags it removed
    project_dir = root_dir.parent
    index_file = root_dir / 'index'
    index = decompress_index(index_file)
    num_blobs = int(index[0])
    folder_name = str(folder_dir)
    name_dir = str(project_dir)
    if name_dir=='.': name_dir=''
    folder_name = folder_name.removeprefix(str(project_dir)+'/')
    list_files = list_files_in_dir(root_dir,folder_dir,folder_name,str(project_dir))
    begin = find_index(index,num_blobs,folder_name)+1
    end = begin
    for i in range(begin,len(index)):
        if i>num_blobs:
            end=i
            break
        if index[i].startswith(folder_name): continue
        end=i
        break
    new_files_dic = {}
    for file in list_files:
        new_files_dic[file[0]]=file[1]
    new_index_stuff = []
    for cur in index[begin:end]:
        spl = cur.split('\x1d')
        if spl[0] in new_files_dic:
            if spl[1] == new_files_dic[spl[0]]:
                if spl[2]=='True': new_index_stuff.append(spl)
                else: new_index_stuff.append([spl[0],spl[1],'True','True'])
            else:
                new_index_stuff.append([spl[0],new_files_dic[spl[0]],'True','True'])
            new_files_dic.pop(spl[0])
        else:
            new_index_stuff.append([spl[0],'...','False','True'])
    for left_file in new_files_dic:
        #these files are completely new
        new_index_stuff.append([left_file,new_files_dic[left_file],'True','True'])
    new_index_stuff.sort(key=lambda x:x[0])
    new_num_blobs = num_blobs - (end-begin) + len(new_index_stuff)
    new_index = str(new_num_blobs)+'\x1e'
    for line in index[1:begin]:
        new_index += line+'\x1e'
    for cur in new_index_stuff:
        new_index += cur[0]+'\x1d'+cur[1]+'\x1d'+cur[2]+'\x1d'+cur[3]+'\x1e'
    for line in index[end:]:
        new_index += line+'\x1e'
    new_index_bytes = new_index.encode('utf-8')
    new_index_compressed = zlib.compress(new_index_bytes)
    index_file.write_bytes(new_index_compressed)

def status(root_dir,file):
    #returns the status of a file (untracked,changed but not commited, staged)
    project_dir = root_dir.parent
    index_file = root_dir / 'index'
    index = decompress_index(index_file)
    num_blobs = int(index[0])
    file_name = str(file)
    name_dir = str(project_dir)
    if name_dir=='.': name_dir=''
    file_name = file_name.removeprefix(str(project_dir)+'/')
    position = find_index(index,num_blobs,file_name)
    split = index[position].split('\x1d')
    if split[0]!=file_name:
        return 'Untracked'
    if not file.exists():
        if split[2]=='False':
            return 'Staged'
        return 'Changed'
    hash = sha1_file(file)
    if hash!=split[1]:
        return 'Changed'
    if split[3]=='True':
        return 'Staged'
    return 'Unchanged'

def show_index(root_dir):
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

def print_tree(root_dir, tree_name):
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

def ls_tree(root_dir, commit_name):
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

def branch_list(root_dir):
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

def find_common_ancestor(refs_heads, commit1, commit2):
    dict = {
        commit1 : 1
    }
    commit1_file = refs_heads / commit1
    with commit1_file.open('rb') as opened:
        commit1_info = (zlib.decompress(opened.read()).decode('utf-8')).split('\x1e')
    father = commit1_info[1]
    while True:
        dict[father]=1
        if father == '-': break
        father_file = refs_heads / father
        with father_file.open('rb') as opened1:
            father_info = (zlib.decompress(opened1.read()).decode('utf-8')).split('\x1e')
        father = father_info[1]
    if commit2 in dict:
        return commit2
    commit2_file = refs_heads / commit2
    with commit2_file.open('rb') as opened2:
        commit2_info = (zlib.decompress(opened2.read()).decode('utf-8')).split('\x1e')
    father = commit2_info[1]
    while True:
        if father in dict: return father
        father_file = refs_heads / father
        with father_file.open('rb') as opened3:
            father_info = (zlib.decompress(opened3.read()).decode('utf-8')).split('\x1e')
        father = father_info[1]

def fast_forward_merge(root_dir, branch_name, cur_branch_file, commit_them):
    try:
        checkout(root_dir,branch_name)
    except UncommitedChanges as error:
        raise UncommitedChanges(error.message)
    cur_branch_file.write_text(commit_them)

def merge(root_dir, branch_name):
    #merges branch with branch_name to the current branch
    index_file = root_dir / 'index'
    index = decompress_index(index_file)
    num_blobs = int(index[0])
    for i in range(1,1+num_blobs):
        spl = index[i].split('\x1d')
        if spl[3]=='True':
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
        return False
    if lca == last_commit_us:
        try:
            fast_forward_merge(root_dir,branch_name,cur_branch_file,last_commit_them)
        except UncommitedChanges as error:
            raise UncommitedChanges(error.message)
        return True
    #here we have to do a 3-way merge