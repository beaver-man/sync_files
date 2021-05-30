# Утилита для формирования json-файла со списком директорий, файлов, их хешей и размеров.

import configparser     # library to import config data from '.ini' files
import os               # library to walk with path of dir
import timeit           # to calc working time
import hashlib          # create hash to compare versions of files
import json             # create json of file to compare and to upload and download


def first_init():
    """
    initialization for global constants for connecting to ftp server
    and another data (path to pictures dir of local)
    return the config information with ConfigParser format
    """
    this_folder = os.path.dirname(os.path.abspath(__file__))  # path to executing dir
    init_file = os.path.join(this_folder, 'config.ini')  # full path to config file
    conf = configparser.ConfigParser()                 # init config parser
    conf.read(init_file, encoding='utf8')              # reading and parsing data from config file
    return conf


def is_it_picture(extension):
    """
    checking the extension of files making json file
    @param: extension of the file
    """
    if extension in ['.pjp', '.png', '.JPG', '.jpeg', '.PNG', '.gif', '.ico', '.jpg', '.GIF']:
        return True
    return False


def make_tree_files(local_directory, local_sec_file):
    """
    function create xml file of pictures
    return quantity of pictures in local_directory (including sub directories)
    @param local_directory: local directory to sync pictures (information from config.ini)
    @param local_sec_file: name of xml file with tree of pictures (information from config.ini)
    """
    tree = os.walk(local_directory)
    sec_file_name = local_directory + local_sec_file
    line_to_file = []
    with open(sec_file_name, 'w') as f_sec:
        q = 0
        for el_tree in tree:
            root_dir = el_tree[0]
            root_dir = root_dir.replace(local_directory, '')
            for file_n in el_tree[2]:
                # filter of pictures files
                if not is_it_picture(os.path.splitext(file_n)[1]):
                    continue
                q += 1
                """ !!! to do new HASH !!!!
                """
                hash_object = hashlib.md5((root_dir + file_n).encode()).hexdigest()
                line_to_file.append([root_dir, file_n, hash_object, os.path.getsize(el_tree[0] + '/' + file_n)])
        json.dump(line_to_file, f_sec)
    return q


if __name__ == '__main__':
    config = first_init()                  # initialization of config data
    FTP_DIR = config.get('ftp', 'dir_to_sync_ftp')
    FTP_SEC_FILE = config.get('ftp', 'ftp_files_secure_name')
    calc_time = timeit.default_timer()
    print('Mapping {} files, in {:0.3f} sec.'.format(make_tree_files(FTP_DIR, FTP_SEC_FILE),
                                                     (timeit.default_timer() - calc_time)))
