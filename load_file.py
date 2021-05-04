
import requests
import json
import os
from decorators import check_connection_elasticsearch
from secondary_functions import check_extension, get_file_ownership, writelog
import time

BASE_URL = 'http://127.0.0.1:9200'




def read_file(name_file: str) -> dict:
    ''''Чтение содержимого файла'''
    try:
        if check_extension(name_file):
        
            with open(name_file) as f:
                text = f.read()
                if len(text) > 100_000:
                    description = text[:100_000].rstrip()
                else:
                    description = text.rstrip()
                author_date = get_file_ownership(name_file)
                title = author_date[2]
                write_info = {
                    'title': title,
                    'author': author_date[0],
                    'date': author_date[1],
                    'file_link': os.path.abspath(name_file),
                    #нужно записать ссылку файла
                    'description': description
                }
            writelog(title, 2)
            return write_info
    except Exception as error:
        writelog(str(get_file_ownership(name_file)[2]), 1, text_error=str(error))


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
def search_file(data_search: dict) -> list:
    # Если база пустая, то вылетит ошибка 'Нет соединения с elasticsearch'
    '''Обобщеная функция поиска. Вид поиска зависит от входящего словаря data_search. На выходе - список ссылок на найденные файлы'''
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
    list_link.append(f'время поиска {time_search} миллисекунд')
    for link in response.json()['hits']['hits']:
        score = link['_score']
        answer = link['_source']['file_link']
        list_link.append([answer, ['релевантность', score]])
    return list_link


def strict_search(search_word: str) -> list:
    '''функция строго поиска'''
    data_search = {
        "query": {
            "match_phrase": {
                    "description": search_word,               
            }
        }
    }
    return search_file(data_search)


def relevant_search(search_word: str) -> list:
    '''функция релевантного поиска по фразе(с опечатками)'''
    data_search = {
        "query": {
            "multi_match": {
                "query":
                search_word,
                "fuzziness": "auto",
                "fields": "description",
                "analyzer": "standard",
              }
        }
    }
    return search_file(data_search)


def mixed_search(search_word: str) -> list:
    '''Функция поиска по точному и неточному поиску. Возвращается список в котором
    в начале выведены ссылки на файлы из точного поиска,затем из релевантного'''
    mixed_list = []
    strict_search_list = strict_search(search_word)
    relevant_search_list = relevant_search(search_word)

    print(strict_search_list[1])
    for link in strict_search_list:
        if link[0] in relevant_search_list[1]:

            print(relevant_search_list.index(link[0]), link, '/n')

    return((strict_search(search_word) + [111111111111111111111111111111111] + relevant_search(search_word)))


@check_connection_elasticsearch
def create_index(index_name: str) -> None: # Добавить проверку уже созданного индекса
    '''Функция создание индекса и определение анализаторов для
    дальнейшего использования'''
    data_setting = {
        "settings": {
            "analysis": {
                "analyzer": 'russian'}},'''{
                    "my_search_analyzer": {
                        "type": "custom",
                        "tokenizer": "russian",
                        "filter": ["lowercase", "ru_stop", "ru_stemmer", "russian_morphology", "english_morphology"]
                    }
                },
                "filter": {
                    "ru_stop": {
                        "type": "stop",
                        "stopwords": ['он', 'еще', 'где']#"_russian_"
                    },
                    "ru_stemmer": {
                        "type": "stemmer",
                        "language": "russian"
                    }
                }
                
            }
        }'''
    "mappings": {
        index_name: {
            "properties": {
                "title": {"type": "text"},

                # "tags": {
                #     "type": "string",
                #     "index": "not_analyzed"
                # },
                "author": {"type": "text"},
                "date": {"type": "date"},
                "file_link": {"type": "text"},
                "description": {"type": "text", "analyzer": "russian"}
            }
        }
    }
}

    response = requests.put(f'{BASE_URL}/{index_name}')


    print(response.json())


# тестовые документы для отработки поиска
# create_index('blog')
# write_file(read_file('test_document/Список Шиндлера.txt'), 'blog')
# write_file(read_file('test_document/Властелин колец: Возвращение короля.txt'), 'blog')
# write_file(read_file('test_document/Властелин колец: Две крепости.txt'), 'blog')
# write_file(read_file('test_document/Интерстеллар.txt'), 'blog')
# write_file(read_file('test_document/Побег из Шоушенка.txt'), 'blog')
# write_file(read_file('test_document/Зелена;я миля.doc'), 'blog')
# write_file(read_file('test_document/Марк Лутц - Изучаем Python.txt'), 'blog')
# print(relevant_search('космическая'))




# #curl -XPOST 'localhost:9200/_analyze?pretty'  -H 'Content-Type: application/json' -d '{"text" : "Привет как у тебя дела в новом городе to the city", "analyzer": {"default": {"tokenizer": "standard", "filter": ["lowercase", "ru_stop", "ru_stemmer"]}}}'

# {"default": {"tokenizer": "standard", "filter": ["lowercase", "ru_stop", "ru_stemmer"]}}


# тестовые документы для нагрузочного тестирования

# start_time = time.time()
# create_index('blog')
# tree = os.walk("/home/zhirnov-sa/Документы/документооборот/search_elastic/test_book/")
# for files in tree:
#     for name in files[2]:
#         write_file(read_file(files[0]+ name), 'blog')

# print("--- %s seconds ---" % (time.time() - start_time))



start_time = time.time()
#print(relevant_search(''))
#print(strict_search('поезд планета'))
print(mixed_search('мельница'))
print("--- %s seconds ---" % (time.time() - start_time))
