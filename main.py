from pathlib import Path
import hashlib
import zlib

def sha1(file):
    #returns sha-1 encryption of file
    hash = hashlib.sha1()
    with file.open('rb') as curfile:
        while chunk := curfile.read(8192):
            hash.update(chunk)
    return hash.hexdigest()

def create_blob(root_dir, file):
    #creates blob in the objects folder
    hash = sha1(file)
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
    HEAD_file = dot_pit_folder / 'HEAD'
    HEAD_file.open('w')
    index_file = dot_pit_folder / 'index'
    compresed_info = zlib.compress(b'0 0')
    index_file.write_bytes(compresed_info)
    return True

def find_index(index,num_blobs,file_name):
    #performs binary search and returns index of first filename in index that is smaller or equal to file_name
    l=0
    r=num_blobs+1
    while l<r-1:
        mid=(l+r)/2
        actual_pos = 1+4*(mid-1)
        if index[actual_pos]<file_name: l=mid
        else: r=mid
    return l

def add_file(root_dir,file):
    #runs command pit add file
    #receives a path object called file and changes the index accordingly
    project_dir = root_dir.parent
    index_file = root_dir / 'index'
    with index_file.open('rb') as index_opened:
        index_compressed = index_opened.read()    
    index_content = zlib.decompress(index_compressed)
    index_text = index_content.decode('utf-8')
    index = index_text.split()
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
            if position==0 or index[position*4+1] != file_name:
                creation = position
        if creation!=-1:
            #this means we have to create the file
            new_index_text = ''
            new_index_text+=str(num_blobs+1)+' '
            for i in range(0,creation):
                new_index_text+=index[i*4+1]+' '
                new_index_text+=index[i*4+2]+' '
                new_index_text+=index[i*4+3]+' '
                new_index_text+=index[i*4+4]+' '
            new_index_text+=file_name+' '
            new_index_text+=hash+' '
            new_index_text+='True '
            new_index_text+='True '
            for i in range(creation,num_blobs):
                new_index_text+=index[i*4+1]+' '
                new_index_text+=index[i*4+2]+' '
                new_index_text+=(index[i*4+3]+' ')
                new_index_text+=(index[i*4+4]+' ')
            for i in range(num_blobs*4+1,len(index)):
                new_index_text+=(index[i]+' ')
            new_index_bytes = new_index_text.encode('utf-8')
            new_index_compressed = zlib.compress(new_index_bytes)
            index_file.write_bytes(new_index_compressed)            
    else:
        #means file was deleted
        #we want to change exist property to false and changed property to true
        if num_blobs == 0: return # there arent blobs, so 
        position = find_index(index,num_blobs,file_name)
        if position==0 or index[(position-1)*4+1] != file_name: return #the file wasnt in the index, so no need to do anything
        #if we are here this means that the file is actually in index and we need to change the information
        if index[(position-1)*4+3] != 'False' and index[(position-1)*4+4]!='True':
            index[(position-1)*4+3] = 'False'
            index[(position-1)*4+4] = 'True'
            new_index_text = ''
            for tex in index: new_index_text+=(tex+' ')
            new_index_bytes = new_index_text.encode('utf-8')
            new_index_compressed = zlib.compress(new_index_bytes)
            index_file.write_bytes(new_index_compressed)

def show_index(root_dir):
    index_file = root_dir / 'index'
    with index_file.open('rb') as index_opened:
        index_compressed = index_opened.read()    
    index_content = zlib.decompress(index_compressed)
    index_text = index_content.decode('utf-8')
    print(index_text)

def main():
    init('')
    root_dir = Path('.pit')
    show_index(root_dir)
    add_file(root_dir,Path('hi.txt'))
    show_index(root_dir)
    # hi = Path('hi.txt')
    # hi_hash = create_blob(root_dir=root_dir,file=hi)
    # hi_blob = root_dir / 'objects' / hi_hash
    # with hi_blob.open('rb') as blob_opened: 
    #     decompress = zlib.decompress( blob_opened.read() )
    # decompress = decompress.decode('utf-8')
    # print(decompress)


if __name__ == '__main__':
    main()