import os
import shutil
import time
import hashlib
import logging
import sys


'''
This step will configure the program to log operations to the logs file.
Also, log them to console output
# Console logs are option (change option to True)
For this, we will use the built-in library
'''

#Setting up logs for both outputs
def set_logging(log_file):
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s : %(message)s",
        handlers = [    
            logging.FileHandler(log_file), #Logging to the file
            logging.StreamHandler() #Logging to the console
        ]
    )

#Log file operations to both a log file and the console.
def logging_message(message):
    logging.info(message)
    #print(message)


'''
Comparing and synchronization of the folders
Will use, as sugested MD5 algorithm
'''

#Check modifications on files that are common to both directories
#For this, as said above, will use the checksum from MD5
#If the checksums are not the same for these files, they are different
def get_checksum_md5(path):
    hash_result = hashlib.md5()

    #divides the files in blocks to perform the checksum
    with open(path,"rb") as file:
        for block in iter(lambda: file.read(4096), b""): #reading in block minimizes memory usage, being more resource efficient
            hash_result.update(block)

    #returns the checksum
    return hash_result.hexdigest()


#Start by getting the contents of both
#So we make a function to get the contents of a directory
def get_dir_contents(path):
    
    #Will use the set container for storage of all files and directories within the folder as it is easier for camparision
    contents = set()

    for dir_path, dir_names, file_names in os.walk(path):
        
        file_paths = dir_names + file_names
        #Getting the full path, relative to the root directory
        for name in file_paths:
            relative_path = os.path.relpath(os.path.join(dir_path,name),path)
            contents.add(relative_path)
    
    #returns the contents of the path
    return contents

def sync_folders(source_dir,replica_dir):

     #Check that replica exists
    os.makedirs(replica_dir, exist_ok=True)

    #Gets the source path, directories inside source directory and files within
    for dir_path, dir_names, file_names in os.walk(source_dir):
        relative_path = os.path.relpath(dir_path, source_dir)
        replica_root = os.path.join(replica_dir,relative_path)
        
        #Ensure directories exist in replica
        if not os.path.exists(replica_root):
            os.makedirs(replica_root, exist_ok = True)
            logging_message(f"Directory {replica_root} does not exist... Creating {replica_root}")

        

        #Check for each file in the source directory
        for file_name in file_names:
            source_file = os.path.join(dir_path, file_name)
            replica_file = os.path.join(replica_root, file_name)

            #If the file does not exist inside the replica folder or if it is not the same as the one in source, copy it, removing the one is replica, if it applys
            if not os.path.exists(replica_file):
                shutil.copy2(source_file, replica_file)
                logging_message(f"File does not exist on replica folder... Copying file: {source_file} -> {replica_file}")
            elif get_checksum_md5(source_file) != get_checksum_md5(replica_file):
                shutil.copy2(source_file, replica_file)
                logging_message(f"File is not the same in replica folder... Modifying file: {source_file} -> {replica_file}")

    #Check for each file in the replica directory   
    for replica_root, rep_dirs, rep_file_names in os.walk(replica_dir):
        relative_path = os.path.relpath(replica_root, replica_dir)
        source_root = os.path.join(source_dir, relative_path)    
        
        #for each file in replica's files
        for file_name in rep_file_names:
            source_file = os.path.join(source_root, file_name)
            replica_file = os.path.join(replica_root, file_name)

            #If the file does not exist in source directory
            #We will remove it
            if not os.path.exists(source_file):
                os.remove(replica_file)
                logging_message(f"File {replica_file} does not exist on source folder... Deleting file in replica folder..")
        
        #for each directory in replica's directories
        for directory in rep_dirs:
            replica_subdirectory = os.path.join(replica_root, directory)
            source_subdir = os.path.join(source_dir, directory)

            #If the directory does not exist in source directory
            #We will remove it
            if not os.path.exists(source_subdir):
                shutil.rmtree(replica_subdirectory)
                logging_message(f"Directory {replica_subdirectory} does not exist on source folder... Deleting directory in replica folder...")


'''
Implementing the periodic synchronization give in the arguments of the program
'''

def main(source_dir, replica_dir, interval, logs_dir):

    set_logging(logs_dir)

    while True:
        sync_folders(source_dir,replica_dir)
        logging_message(f"Sychronization Complete! Next synchronization will occur in {interval} seconds")
        time.sleep(interval)


if __name__ == "__main__":

    '''
    The arguments for the source and replica directory
    as well as the synchronization intervals and the log file path
    will be recieved from command-line.
    With this, we need to setup sys.argv to receive them and we 
    need to ensure that exactly 4 arguments (this ones) are passed
    After this, we need to validate the arguments and check if, at least, the source directory exists as the others can be created
    '''

    #Checking number of arguments
    if len(sys.argv) != 5:
        print("Wrong Number of Arguments!\nUsage: python synchronize.py <source_directory> <replica_directory> <synchro_interval_secs> <logs_directory>")
        sys.exit(1)
    #And saving them
    source_dir = sys.argv[1]
    replica_dir = sys.argv[2]
    interval = int(sys.argv[3])
    logs_dir = sys.argv[4]

    #Check existance of source file directory
    if not (os.path.isdir(source_dir)):
        print(f"Error: Provided Source directory {"source_dir"} does not exist.")
        sys.exit(1)

    main(source_dir, replica_dir, interval, logs_dir)

