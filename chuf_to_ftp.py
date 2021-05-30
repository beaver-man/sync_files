# Утилита для проверка файлов в ключевой папке на локальном ресурсе, на удалённом ресурсе.
# Сопоставление этой информации и загрузка на удалённый ресурс файлов с локального ресурса.
# Создаётся локальный файл с названием файлов, размерами, папками и хэшем локальных файлов
# Скачмваеися файл с ftp сервера со списком путей файлов на сервере ftp (он включается там по крону)
# Сравнивается эта информация, создаётся список таких файлов.
# Файлы картинок загружаются по ftp на сервер

from ftplib import FTP  # library for ftp upload, walking (checking) and download
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


def ftp_upload(ftp_obj, ftp_path, local_path, ftype='TXT'):
    """
    function to upload files to ftp server
    @param ftp_obj: ftp object
    @param local_path: full path of uploading file
    @param ftp_path: full path of uploading file on ftp
    @param ftype: type of uploading file (txt - default),
    """
    if ftype == 'TXT' or ftype == 'XML':
        with open(local_path) as fobj:
            ftp_obj.storlines('STOR ' + ftp_path, fobj)
    else:
        with open(local_path, 'rb') as fobj:
            ftp_obj.storbinary('STOR ' + ftp_path, fobj, 1024)


def check_create_folder(ftp_obj, list_folder):
    """
    check existing of folder on ftp server
    @param ftp_obj: ftp object
    @param list_folder: string of folders from '/' checking for existing (like 'folder1/subfolder')
    """
    path = list_folder.split('/')
    checking_path_ftp = path[0]
    checking_path = checking_path_ftp
    for i in range(1, len(path)):
        checking_path += '/' + path[i]
        # print('Searching', checking_path, 'in', ftp.nlst(checking_path_ftp))
        if len(ftp.nlst(checking_path_ftp)) <= 0:
            # folder is not existing. create it.
            ftp_obj.mkd(checking_path_ftp)
            # print('Create', checking_path_ftp)
        if not (checking_path in ftp.nlst(checking_path_ftp)):
            # folder is not existing. create it
            ftp_obj.mkd(checking_path)
            # print('Create ', checking_path, ' in ', checking_path_ftp)
        checking_path_ftp += '/' + path[i]


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
            root_dir = root_dir.replace('\\', '/')
            for file_n in el_tree[2]:
                # filter of pictures files
                if not is_it_picture(os.path.splitext(file_n)[1]):
                    continue
                q += 1
                """ !!! to do new HASH !!!!
                """
                hash_object = hashlib.md5((root_dir + file_n).encode()).hexdigest()
                line_to_file.append([root_dir, file_n, hash_object, os.path.getsize(el_tree[0] + '\\' + file_n)])
        json.dump(line_to_file, f_sec)
    return q


if __name__ == '__main__':
    config = first_init()                  # initialization of config data
    FTP_SERVER = config.get('ftp', 'server')
    FTP_USER = config.get('ftp', 'user')
    FTP_PASSWORD = config.get('ftp', 'pwd')
    FTP_DIR = config.get('ftp', 'dir_to_sync_ftp')
    LOCAL_DIR = config.get('local', 'dir_to_sync_local')
    LOCAL_SEC_FILE = config.get('local', 'dirs_files_secure_name')
    FTP_SEC_FILE = config.get('ftp', 'ftp_files_secure_name')
    calc_time = timeit.default_timer()
    print('Mapping {} files, in {:0.3f} sec.'.format(make_tree_files(LOCAL_DIR, LOCAL_SEC_FILE),
                                                     (timeit.default_timer() - calc_time)))
    # 1. create ftp object
    ftp = FTP(FTP_SERVER)
    ftp.login(FTP_USER, FTP_PASSWORD)
    ftp.cwd(FTP_DIR)
    # Download file of list of pictures from ftp server
    with open('temp.txt', 'wb') as f:
        ftp.retrbinary("RETR " + FTP_DIR + FTP_SEC_FILE, f.write)
    # make the list of ftp pictures
    with open('temp.txt') as f:
        list_files_ftp = json.load(f)
    # remove temp file
    os.remove('temp.txt')
    # make the list of local pictures
    with open(LOCAL_DIR + LOCAL_SEC_FILE) as f:
        list_files_local = json.load(f)
    # compare files of pictures in ftp and local versions
    add_pictures = []
    for el in list_files_local:
        if el not in list_files_ftp:
            add_pictures.append(el)
    for el in add_pictures:
        file_name = LOCAL_DIR + el[0].replace('/', '\\') + '\\' + el[1]
        # checking folder or creating non existing folder
        if len(ftp.nlst(el[0])) <= 0:
            check_create_folder(ftp, el[0])
        # Upload file file_name to ftp server to full_path_ftp
        full_path_ftp = FTP_DIR + el[0] + '/' + el[1]
        ftp_upload(ftp, full_path_ftp, file_name, ftype='PIC')
        print('written {0}'.format(full_path_ftp))
    ftp.close()
