from pathlib import Path
import hashlib
import zlib
from typing import List

class Pit_file:
    path_object : Path
    file_name : str
    is_compr : bool

    def __init__(self, file_object : Path, is_compr : bool = False):
        self.path_object = file_object
        self.file_name = str(file_object)
        self.is_compr = is_compr
    def get_value_text(self) -> str:
        if not self.is_compr:
            file_text = self.path_object.read_text()
        else:
            file_compressed = self.path_object.read_bytes()    
            file_content = zlib.decompress(file_compressed)
            file_text = file_content.decode('utf-8')
        return file_text
    def get_value_bytes(self) -> bytes:
        if not self.is_compr:
            file_bytes = self.path_object.read_bytes()
        else:
            file_compressed = self.path_object.read_bytes()    
            file_bytes = zlib.decompress(file_compressed)
        return file_bytes     
    def write_value_from_text(self, text : str):
        if self.is_compr:
            bytes = text.encode('utf-8')
            bytes_compressed = zlib.compress(bytes)
            self.path_object.write_bytes(bytes_compressed)
        else:
            self.path_object.write_text(text)
    def write_value_from_bytes(self, bytes : bytes):
        if self.is_compr:
            bytes_compressed = zlib.compress(bytes)
            self.path_object.write_bytes(bytes_compressed)
        else:
            self.path_object.write_bytes(bytes)
    def sha1(self) -> str:
        hash = hashlib.sha1()
        with self.path_object.open('rb') as curfile:
            chunk = curfile.read()
            if self.is_compr:
                chunk_dec = zlib.decompress(chunk)
                hash.update(chunk_dec)
            else:
                hash.update(chunk)
        return hash.hexdigest()
    
    @classmethod
    def sha1_from_text(cls, text : str) -> str:
        hash = hashlib.sha1()
        hash.update(text.encode('utf-8'))
        return hash.hexdigest()

class File_entry:
    name : str
    hash : str
    has_bools : bool
    exists : bool
    changed : bool
    only_exists : bool

    def __init__(self, name : str, hash : str = '...', has_bools : bool = False, exists : bool = False, changed : bool = False, only_exists : bool = False):
        self.name = name
        self.hash = hash
        self.has_bools = has_bools
        self.exists = exists
        self.changed = changed
        self.only_exists = only_exists
    
    @classmethod
    def from_line(cls, line_text : str, has_bools : bool = False, only_exists : bool = False):
        line_spl = line_text.split('\x1d')
        name = line_spl[0]
        if only_exists:
            if line_spl[1]=='True':
                exists = True
            else:
                exists = False
            return cls(name=name, only_exists=True,exists=exists)
        else:
            hash = line_spl[1]
            if has_bools:
                if line_spl[2]=='True': exists = True
                else: exists = False
                if line_spl[3]=='True': changed = True
                else: changed = False
                return cls(name,hash,has_bools,exists,changed)
            else: return cls(name,hash)
    
    def turn_to_text(self, delimitor : str = '\x1d') -> str:
        if self.only_exists:
            text = self.name+delimitor+str(self.exists)
            return text
        else:
            text = self.name+delimitor+self.hash
            if self.has_bools:
                ex_text = str(self.exists)
                ch_text = str(self.changed)
                text+=delimitor+ex_text+delimitor+ch_text
            return text

class Index(Pit_file):
    number_of_files : int
    number_of_trees : int
    files : List[File_entry]
    trees : List[File_entry]

    def __init__(self, root_dir : Path):
        super().__init__(root_dir / 'index', is_compr = True)
        self.number_of_files = 0
        self.number_of_trees = 0
        self.files = []
        self.trees = []

    @classmethod
    def from_file(cls, root_dir : Path):
        index = cls(root_dir)
        value_text = index.get_value_text()
        value_splitted = value_text.split('\x1e')
        index.number_of_files = int(value_splitted[0])
        for line in value_splitted[1:1+index.number_of_files]:
            index.files.append( File_entry.from_line(line,True) )
        index.number_of_trees = int(value_splitted[1+index.number_of_files])
        for line in value_splitted[2+index.number_of_files:2+index.number_of_files+index.number_of_trees]:
            index.trees.append( File_entry.from_line(line) )
        return index

    def find_file_in_index(self, file_name : str) -> int:
        l = -1
        r = self.number_of_files
        while l<r-1:
            mid=int((l+r)/2)
            if self.files[mid].name <= file_name: l=mid
            else: r=mid
        return l
    
    def add_single_file_by_position(self, position : int, new_entry : File_entry):
        self.number_of_files += 1
        self.files = self.files[:position] + [new_entry] + self.files[position:]

    def add_file_list_by_position(self, begin : int, end : int, new_entries : List[File_entry]):
        self.files = self.files[:begin] + new_entries + self.files[end:]
        self.number_of_files = len(self.files)

    def add_file_list_general(self, do_change : List[ List[ str ] ]):
        do_change.sort(key=lambda x:x[0])
        lst_ch = 0
        new_index_files : List[File_entry] = []
        for change in do_change:
            fdd = self.find_file_in_index(change[0])
            if self.files[fdd].name==change[0]:
                #we have a change in the file
                for cur_entry_old in self.files[lst_ch:fdd]:
                    new_index_files.append(cur_entry_old)
                lst_ch = fdd+1
                if change[1]!='...':
                    #we don't have a deletion, so we have to add the file as existing
                    new_index_files.append(File_entry(name=change[0],hash=change[1],has_bools=True,exists=True,changed=True))
                else:
                    #we have to add it as deleted
                    new_index_files.append(File_entry(name=change[0],hash=change[1],has_bools=True,exists=False,changed=True))
            else:
                #we have a new file
                for cur_entry_old in self.files[lst_ch:fdd+1]:
                    new_index_files.append(cur_entry_old)
                lst_ch = fdd+1
                if change[1]=='...':
                    print('THIS IS A BIG ERROR, IT SHOULD NEVER HAPPEN')
                new_index_files.append(File_entry(name=change[0],hash=change[1],has_bools=True,exists=True,changed=True))
        for cur_entry_old in self.files[lst_ch:]:
            new_index_files.append(cur_entry_old)
        self.number_of_files = len(new_index_files)
        self.files = new_index_files

    def write_to_file(self, sort_files : bool = False , sort_trees : bool = False):
        if sort_files:
            self.files.sort(key=lambda x:x.name)
        if sort_trees:
            self.trees.sort(key=lambda x:x.name)
        index_text = str(self.number_of_files)+'\x1e'
        for file in self.files:
            index_text += file.turn_to_text()+'\x1e'
        index_text += str(self.number_of_trees)+'\x1e'
        for tree in self.trees:
            index_text += tree.turn_to_text()+'\x1e'
        self.write_value_from_text(index_text)

    def turn_to_text(self) -> str:
        index_text = str(self.number_of_files)+'\n'
        for file in self.files:
            index_text += file.turn_to_text(delimitor=' ')+'\n'
        index_text += str(self.number_of_trees)+'\n'
        for tree in self.trees:
            index_text += tree.turn_to_text(delimitor=' ')+'\n'
        return index_text
    
class Tree(Pit_file):
    hash : str
    father : str
    name : str
    num_files : int
    num_trees : int
    files : List[File_entry]
    trees : List[File_entry]

    def __init__(self, object_file : Path):
        super().__init__(file_object=object_file, is_compr=True)
        self.hash = ''
        self.father = ""
        self.name = ""
        self.num_files = 0
        self.files = []
        self.num_trees = 0
        self.trees = [] 
    
    @classmethod
    def from_file(cls, object_file : Path):
        tree = cls(object_file)
        if object_file.name == '-': return tree
        tree_text = tree.get_value_text()
        tree_info = tree_text.split('\x1e')
        tree.name = tree_info[0]
        tree.hash = tree.sha1()
        tree.num_files = int(tree_info[1])
        for line in tree_info[2:2+tree.num_files]:
            spl = line.split('\x1d')
            tree.files.append(File_entry(name=spl[0],hash=spl[1]))
        tree.num_trees = int(tree_info[2+tree.num_files])
        for line in tree_info[3+tree.num_files:3+tree.num_files+tree.num_trees]:
            spl = line.split('\x1d')
            tree.trees.append(File_entry(name=spl[0],hash=spl[1]))
        return tree

    def write_to_file(self, fix = False):
        tree_text = self.name+'\x1e'+str(self.num_files)+'\x1e'
        for cur_file in self.files:
            tree_text += cur_file.turn_to_text()+'\x1e'
        tree_text += str(self.num_trees)+'\x1e'
        for cur_tree in self.trees:
            tree_text += cur_tree.turn_to_text()+'\x1e'
        if fix:
            self.hash = Pit_file.sha1_from_text(tree_text)
            self.path_object = (self.path_object.parent) / self.hash
        self.write_value_from_text(tree_text)

class Commit(Pit_file):
    message : str
    head_tree : str
    num_changes : int
    changes : List[File_entry]
    hash : str
    father : str
    brother : str

    def __init__(self, object_file : Path , message : str = '', head_tree : str = '', num_changes : int = 0, changes : List[File_entry] = None,
                 father : str = '', brother : str = None):
        super().__init__(file_object= object_file, is_compr=True)
        self.hash = ''
        self.message = message
        self.head_tree = head_tree
        self.num_changes = num_changes
        if changes is None:
            self.changes = []
        else:
            self.changes = changes
        self.father = father
        self.brother = brother

    @classmethod
    def from_file(cls, object_file : Path):
        commit = cls(object_file = object_file)
        commit.hash = commit.sha1()
        commit_text = commit.get_value_text()
        commit_info = commit_text.split('\x1e')
        commit.message = commit_info[0]
        commit.father = commit_info[1]
        commit.head_tree = commit_info[2]
        commit.num_changes = int(commit_info[3])
        kolko = 0
        for line in commit_info[4:4+commit.num_changes]:
            spl = line.split('\x1d')
            if spl[1]=='True':
                exists = True
            else: exists = False
            kolko+=1
            commit.changes.append(File_entry(name=spl[0],only_exists=True,exists=exists))
        if commit_info[4+commit.num_changes]!='':
            #there is a brother
            commit.brother = commit_info[-2]
        return commit
    
    def get_father(self) -> str:
        return self.father
    
    def get_brother(self) -> str | None:
        return self.brother
    
    def write_to_file(self, fix = False):
        commit_text = self.message + '\x1e' + self.father + '\x1e' + self.head_tree + '\x1e' + str(self.num_changes) + '\x1e'
        for change in self.changes:
            commit_text += change.turn_to_text()+'\x1e'
        if self.brother is not None:
            commit_text += self.brother + '\x1e'
        if fix:
            self.hash = Pit_file.sha1_from_text(commit_text)
            self.path_object = (self.path_object.parent) / self.hash
        self.write_value_from_text(commit_text)

