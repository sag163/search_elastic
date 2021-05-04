import os
from pathlib import Path
from pwd import getpwuid
import time
import sys
from datetime import datetime as dt
import re

LVL_LOG = {
        0: 'INFORMATION',
        1: 'ERROR_READ__TO_FILE',
        2: 'SUCCESS_READ__TO_FILE',
        3: 'ERROR_WRITE__TO_ELASTICSEARCH',
        4: 'SUCCESS_WRITE__TO_ELASTICSEARCH',
        5: 'ERROR_READ_ERROR__TO_ELASTICSEARCH',
        6: 'SUCCESS_READ_ERROR__TO_ELASTICSEARCH',
    }



def check_extension(name_file: str) -> bool:
    '''Проверка допустимого расширения файла'''
    extensions = ('.doc', '.docx', '.xls', '.xlsx', '.pdf', '.txt', '.csv', '.fb2',)
    extension = Path(name_file).suffix
    if extension in extensions:
        return True
    writelog(str(name_file), 1, text_error='Расширение файла не поддерживается')
    return False


def get_file_ownership(filename):
    '''Получение информации о файле: дата_время последнего изменения, автор файла'''
    time_modification_file = time.ctime(os.path.getmtime(filename))
    author = getpwuid(os.stat(filename).st_uid).pw_name
    name = os.path.basename(filename)
    
    return [author, time_modification_file, name]


def writelog(message: str, lvl: int,  text_error = '') -> None:
    '''Функция для записи логов при чтении файлов, записи в elasticsearch и поиске в elasticsearch'''

    log = dt.now().strftime("%d.%m.%Y  %H:%M:%S") + '  ' + message + ' ' + LVL_LOG[lvl] + \
            '  ' + text_error + '\n'
    try:
        log_file = open('logs/LOG_READ__TO_FILE', 'a')
        log_file.write(log)
        log_file.close()
    except OSError:
        pass



# string = '/home/zhirnov-sa/Документы/документооборот/search_elastic/test_book/1 Отбор.fb2'

# base=os.path.basename(string)
# name = os.path.splitext(base)
# print(base)
# print(name[0])
# name_file = re.compile(r'/.* + .)')
# mo = (name_file.search(string))
# print(mo.group(0))




