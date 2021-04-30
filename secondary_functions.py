import os
from pathlib import Path
from pwd import getpwuid
import time


my_filename = 'test_document/Зеленая миля.doc'


def check_extension(name_file: str) -> bool:
    '''Проверка допустимого расширения файла'''
    extensions = ['.doc', '.docx', '.xls', '.xlsx', '.pdf', '.txt', '.csv', ]
    extension = Path(name_file).suffix
    if extension in extensions:
        return True
    return False


def get_file_ownership(filename):
    '''Получение информации'''
    time_modification_file = time.ctime(os.path.getmtime(filename))
    author = getpwuid(os.stat(filename).st_uid).pw_name
    return [author, time_modification_file]
