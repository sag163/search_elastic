
import requests
import json
import os
from decorators import check_connection_elasticsearch
from secondary_functions import check_extension, get_file_ownership

BASE_URL = 'http://127.0.0.1:9200'


def read_file(name_file: str) -> dict:
    ''''Чтение содержимого файла'''
    if check_extension(name_file):
        f = open(name_file, 'r')
        author_date = get_file_ownership(name_file)
        write_info = {
            'title': name_file,
            'author': author_date[0],
            'date': author_date[1],
            'file_link': os.path.abspath(name_file),
            # нужно записать ссылку файла
            'description': f.readlines()
        }
        return write_info


@check_connection_elasticsearch
def write_file(write_info: dict, index: str) -> bool:
    '''Функция для записи информации в elasticsearch'''
    url = f'{BASE_URL}/{index}/_doc'
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(
        url,
        data=json.dumps(write_info),
        headers=headers)
    if response.status_code == 201:
        return True
    return False


@check_connection_elasticsearch
def search_file(index: str, search_words: str) -> list:
    # Если база пустая, то вылетит ошибка 'Нет соединения с elasticsearch'
    '''Функция поиска статьи по ключевым словам, с возвращением списка ссылок,
    где храниться документ'''

    data_search = {
        "query": {
            "multi_match": {
                "query":
                search_words,
                "fuzziness": "auto",
                "fields": ["file_link", "description"]
            }
        }
    }

    url = f'{BASE_URL}/_search'
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.get(
        url,
        data=json.dumps(data_search),
        headers=headers)
    list_link = []
    # Добавим в отображение время затраченное на поиск
    time_search = response.json()['took']
    list_link.append(f'время поиска {time_search}миллисекунд')
    for link in response.json()['hits']['hits']:
        score = link['_score']
        answer = link['_source']['file_link']
        list_link.append([answer, ['релевантность', score]])
    return list_link


def strict_search(index: str, search_word: str) -> list:
    '''функция строго поиска'''
    pass


def relevant_search(index: str, search_word: str) -> list:
    '''функция релевантного поиска по фразе(с опечатками)'''
    pass


def create_index(index_name: str) -> None:
    '''создание индексов и определение анализаторов для
    дальнейшего использования'''
    response = requests.post(BASE_URL)
    print(response.json())


write_file(read_file('test_document/Список Шиндлера.txt'), 'test')
write_file(read_file('test_document/Властелин колец: Возвращение короля.txt'), 'test')
write_file(read_file('test_document/Властелин колец: Две крепости.txt'), 'test')
write_file(read_file('test_document/Интерстеллар.txt'), 'test')
write_file(read_file('test_document/Побег из Шоушенка.txt'), 'test')
write_file(read_file('test_document/Зеленая миля.doc'), 'test')

# print(search_file('test', 'тюрьма'))
