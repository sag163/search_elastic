import os
from pathlib import Path
from pwd import getpwuid
from datetime import datetime as dt
import datetime
from datetime import datetime
import getpass

from parser import (
    parser_default,
    parser_xlxs,
    parser_xlx,
    parser_doc,
    parser_rtf,
)


LVL_LOG = {
    0: ["INFORMATION", 'INFO'],
    1: ["ERROR", 'LOG_READ__TO_FILE'],
    2: ["SUCCESS", 'LOG_READ__TO_FILE'],
    3: ["ERROR", 'LOG_WRITE__TO_FILE'],
    4: ["SUCCESS", 'LOG_WRITE__TO_FILE'],
    5: ["ERROR", 'LOG_READ__TO_ES'],
    6: ["SUCCESS", 'LOG_READ__TO_ES'],
    7: ["ERROR", 'LOG_DELETE__TO_ES'],
    8: ["SUCCESS", 'LOG_DELETE__TO_ES']
}


EXTENSIONS = {
    ".doc": parser_doc,
    ".docx": parser_doc,
    ".xls": parser_xlx,
    ".xlsx": parser_xlxs,
    ".pdf": parser_doc,
    ".txt": parser_default,
    ".csv": parser_default,
    ".fb2": parser_default,
    ".rtf": parser_rtf,
}


def check_extension(name_file: str):
    """Проверка допустимого расширения файла"""
    extension = Path(name_file).suffix
    if extension in EXTENSIONS:
        return EXTENSIONS[extension]
    writelog(str(name_file), 1, text_error="Расширение файла не\
    поддерживается")
    return None


def get_file_ownership(filename: str) -> list:
    """Получение информации о файле: дата_время последнего изменения,
    автор файла, имя файла"""
    unix_time = os.path.getatime(filename)
    fileLastModified = datetime.utcfromtimestamp(unix_time).\
        strftime('%d-%m-%Y %H:%M:%S')
    author = getpwuid(os.stat(filename).st_uid).pw_name
    fileName = os.path.basename(filename)
    fileSize = os.path.getsize(filename)
    fileType = os.path.splitext(filename)[1]
    return [author, fileLastModified, fileName, fileSize, fileType]


def writelog(message: list, lvl: int, text_error="нет") -> None:
    """Функция для записи логов при чтении/удаление файлов, записи/поиске
    в elasticsearch"""
    name_file_log = LVL_LOG[lvl][1]
    time = dt.now().strftime("%d.%m.%Y  %H:%M:%S")
    log = f'{time}, текст: {message} Статус: {LVL_LOG[lvl][0]},\
        Запрос выполнил: {getpass.getuser()}........... \
            Ошибка: {text_error} "\n"'
    try:
        log_file = open(f"logs/{name_file_log}", "a")
        log_file.write(log)
        log_file.close()
    except OSError:
        pass
