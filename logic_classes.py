from pathlib import Path
import hashlib
import zlib
from typing import List

class Pit_file:
    path_object : Path
    file_name : str
    is_compr : bool

    def __init__(self, file_object : Path, is_compr : bool):
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
    def write_value_from_text(self, text : str):
        if self.is_compr:
            bytes = text.encode('utf-8')
            bytes_compressed = zlib.compress(bytes)
            self.path_object.write_bytes(bytes_compressed)
        else:
            self.path_object.write_text(text)

class File_entry:
    name : str
    hash : str
    has_bools : bool
    exists : bool
    changed : bool

    def __init__(self, name : str, hash : str, has_bools : bool = False, exists : bool = False, changed : bool = False):
        self.name = name
        self.hash = hash
        self.has_bools = has_bools
        self.exists = exists
        self.changed = changed
    
    @classmethod
    def from_line(cls, line_text : str, has_bools : bool = False):
        line_spl = line_text.split('\x1d')
        name = line_spl[0]
        hash = line_spl[1]
        if has_bools:
            if line_spl[2]=='True': exists = True
            else: exists = False
            if line_spl[3]=='True': changed = True
            else: changed = False
            return cls(name,hash,has_bools,exists,changed)
        else: return cls(name,hash)
    
    def turn_to_text(self) -> str:
        text = self.name+'\x1d'+self.hash
        if self.has_bools:
            ex_text = str(self.exists)
            ch_text = str(self.changed)
            text+='\x1d'+ex_text+'\x1d'+ch_text
        return text

class Index(Pit_file):
    number_of_files : int
    number_of_trees : int
    files : List[File_entry]
    trees : List[File_entry]

    def __init__(self, root_dir):
        super().__init__(root_dir / 'index', is_compr = True)
        value_text = self.get_value_text()
        value_splitted = value_text.split('\x1e')
        self.number_of_files = int(value_splitted[0])
        self.files = []
        for line in value_splitted[1:1+self.number_of_files]:
            self.files.append( File_entry.from_line(line,True) )
        self.number_of_trees = int(value_splitted[1+self.number_of_files])
        self.trees = []
        for line in value_splitted[2+self.number_of_files:2+self.number_of_files+self.number_of_trees]:
            self.trees.append( File_entry.from_line(line) )

    def find_file_in_index(self, file_name : str) -> int:
        l = -1
        r = self.number_of_files
        while l<r-1:
            mid=int((l+r)/2)
            if self.files[mid].name <= file_name: l=mid
            else: r=mid
        return l
    
    def add_single_file(self, position : int, new_entry : File_entry):
        self.number_of_files += 1
        self.files = self.files[:position] + [new_entry] + self.files[position:]

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
    