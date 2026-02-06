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
    dot_pit_folder = Path(project_dir) / '.pit'
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
    compresed_info = zlib.compress(b'0\n0\n')
    index_file.write_bytes(compresed_info)
    return True

def find_index(index,num_blobs,file_name):
    #performs binary search and returns index of first filename in index that is smaller or equal to file_name
    l=0
    r=num_blobs+1
    while l<r-1:
        mid=int((l+r)/2)
        splited = index[mid].split()
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
    index = index_text.split('\n')
    index.pop()
    return index

def add_file(root_dir,file):
    #runs command pit add file
    #receives a path object called file and changes the index accordingly
    project_dir = root_dir.parent
    index_file = root_dir / 'index'
    index = decompress_index(index_file)
    num_blobs = int(index[0])
    file_name = str(file)
    name_dir = str(project_dir)
    if name_dir=='.': name_dir=''
    file_name = file_name.removeprefix(str(project_dir))
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
            cur_position_split = index[position].split()
            if cur_position_split[0]!=file_name: 
                creation = position
        if creation!=-1:
            #this means we have to create the file
            new_index_text = str(num_blobs+1)+'\n'
            for i in range(1,creation+1): new_index_text+=(index[i]+'\n')
            new_index_text+=(file_name+' '+hash+' True True\n')
            for i in range(creation+1,len(index)): new_index_text+=(index[i]+'\n')
            new_index_bytes = new_index_text.encode('utf-8')
            new_index_compressed = zlib.compress(new_index_bytes)
            index_file.write_bytes(new_index_compressed)   
        else:
            #this means file is in the index at line, position
            cur_position_split = index[position].split()
            if cur_position_split[1]==hash:
                #means nothing was changed, so we shouldnt change nothing
                return
            #here the file was actually changed
            cur_position_split[1]=hash
            index[position]=cur_position_split[0]+' '+cur_position_split[1]+' True True'
            new_index_text = ''
            for tex in index: new_index_text+=(tex+'\n')
            new_index_bytes = new_index_text.encode('utf-8')
            new_index_compressed = zlib.compress(new_index_bytes)
            index_file.write_bytes(new_index_compressed)
    else:
        #means file was deleted
        #we want to change exist property to false and changed property to true
        if num_blobs == 0: return # there arent blobs, so 
        position = find_index(index,num_blobs,file_name)
        if position==0: return #the file wasnt in the index, so no need to do anything
        cur_position_split = index[position].split()
        if cur_position_split[0]!=file_name: return #the file wasnt in the index
        #if we are here this means that the file is actually in index and we need to change the information
        if cur_position_split[2] != 'False' or cur_position_split[2]!='True':
            new_index_text = ''
            index[position]=cur_position_split[0]+' '+cur_position_split[1]+' '+'False'+' '+'True'
            for tex in index: new_index_text+=(tex+'\n')
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

def commit(root_dir,commit_message): ###there is a huge error in the commit. When a file is added inside more than one folder that doesnt exist, it crashes
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
        splited = index[i].split(' ')
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
    new_index = str(existing_files)+'\n'
    for i in range(1,num_blobs+1):
        splited = index[i].split(' ')
        if splited[2]=='False': 
            continue
        new_index+=splited[0]+' '+splited[1]+' True False\n'
    new_index+=str(num_trees)+'\n'
    root_tree = ''
    for cur_key, cur_num in sorted(tree_dic.items(),reverse=True):
        cur_tree = tree_array[cur_num]
        tree_info = cur_tree.name+'\n'
        tree_info += str(cur_tree.num_files)+'\n'
        for i in range(0,cur_tree.num_files):
            tree_info+= cur_tree.file_names[i]+' '+cur_tree.file_blobs[i]+'\n'
        tree_info += str(cur_tree.num_trees)+'\n'
        for i in range(0,cur_tree.num_trees):
            tree_info+= cur_tree.tree_names[i]+' '+cur_tree.tree_blobs[i]+'\n'
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
        new_index+=cur_key+' '+cur_tree.hash+'\n'
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
    commit_info = commit_message+'\n'+previous_commit+'\n'+root_tree+'\n'
    commit_info+=str(len(changed))+'\n'
    for ch in changed:
        commit_info+=ch[0]+' '+ch[1]+'\n'
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
        commit_info = commit_text.split('\n')
        commit_info.pop()
        log_text+='Commit name:'+last_commit+'\n'
        log_text+='Commit message:'+commit_info[0]+'\n'
        changed = 0
        removed = 0
        for i in range(4,len(commit_info)):
            spl = commit_info[i].split()
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
    tree_info = tree_text.split('\n')
    tree_info.pop()
    num_files = int(tree_info[1])
    if get_folder(file_name)==tree_info[0]:
        #this means we are searching for the file itself in the list of files
        for i in range(2,2+num_files):
            spl = tree_info[i].split()
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
            spl = tree_info[i].split()
            if file_name.startswith(spl[0]):
                return find_file(root_dir,spl[1],file_name)
        return False

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
        commit_info = commit_text.split('\n')
        last_commit = commit_info[1]
    commit_file = root_dir / 'objects' / last_commit
    with commit_file.open('rb') as commit_file_opened:
        commit_compressed = commit_file_opened.read()
    commit_text = zlib.decompress(commit_compressed).decode('utf-8')
    commit_info = commit_text.split('\n')
    cur_tree = commit_info[2]
    file_content = find_file(root_dir,cur_tree,file_name)
    if file_content == False:
        raise UnableToRetrieve('There is no file '+file_name+' in the repository of commit '+commit_name+'.\n')
    if create: create_place.write_bytes(file_content)
    return file_content

class UncommitedChanges(Exception):
    def __init__(self, message):
        self.message=message
        super().__init__(message)

def checkout(root_dir,branch_name):
    #switches to another branch, if it doesnt exist it creates it
    #returns False when it creates a new branch, and True when it changes to an existing one

    index_file = root_dir / 'index'
    index = decompress_index(index_file)
    num_blobs = int(index[0])
    for i in range(1,1+num_blobs):
        spl = index[i].split(' ')
        if spl[3]=='True':
            raise UncommitedChanges('Please commit all changes before switching branches.')
    head_file = root_dir / 'HEAD'
    with head_file.open('rb') as head_opened:
        cur_branch = head_opened.read()
    cur_branch = cur_branch.decode('utf-8')
    if cur_branch==branch_name: return
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
    return True

def show_index(root_dir):
    index_file = root_dir / 'index'
    with index_file.open('rb') as index_opened:
        index_compressed = index_opened.read()    
    index_content = zlib.decompress(index_compressed)
    index_text = index_content.decode('utf-8')
    print(index_text)

def main():
    while True:
        inp = input().split()
        if (inp[1]=='init'): init('')
        elif (inp[1]=='add'): add_file(root_dir=Path('.pit'),file=Path(inp[2]))
        elif (inp[1]=='commit'): commit(root_dir=Path('.pit'),commit_message='no message')
        elif (inp[1]=='show'): show_index(root_dir=Path('.pit'))
        elif (inp[1]=='log'): print(log(root_dir=Path('.pit')))
        elif (inp[1]=='retrieve'):
            create = False
            if len(inp)==5:
                create=True
                create_place = Path(inp[4])
            else:
                create_place = None
            try:
                arg=retrieve(root_dir=Path('.pit'),commit_name=inp[2],file_name=inp[3],create=create,create_place=create_place)
                if create==False:
                    print(arg.decode('utf-8'))
            except UnableToRetrieve as error:
                print(error.message)
        elif (inp[1]=='checkout'):
            try:
                checkout(root_dir=Path('.pit'),branch_name=inp[2])
            except UncommitedChanges as error:
                print(error.message)


if __name__ == '__main__':
    main()