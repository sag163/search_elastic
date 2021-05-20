from datetime import date
import requests
import json
import os
from decorators import check_connection_elasticsearch
from secondary_functions import check_extension, get_file_ownership, writelog
import time


BASE_URL = "http://127.0.0.1:9200"


def read_file(name_file: str, token: str) -> dict:
    """'Чтение содержимого файла"""
    try:
        parser = check_extension(name_file)
        if parser is None:
            writelog(
                [get_file_ownership(name_file)[2]],
                1,
                text_error="Расширение файла не поддерживается")
        else:
            description = parser(name_file)
            author_date = get_file_ownership(name_file)
            title = author_date[2]
            write_info = {
                "fileName": title,
                "author": author_date[0],
                "fileLastModified": author_date[1],
                'fileSize': author_date[3],
                'fileType': author_date[4],
                "filePath": os.path.abspath(name_file),
                "description": description,
                'pk': token
            }
            writelog([title], 2)
            return write_info
    except Exception as error:
        writelog(
            [get_file_ownership(name_file)[2]],
            1,
            text_error=str(error)
        )


#@check_connection_elasticsearch
def write_file_to_elastic(name_file: str, index: str, token: str, obj_type_id: str) -> bool:
    """Функция для записи информации в elasticsearch"""
    write_info = read_file(name_file, token)
    try:
        url = f"{BASE_URL}/{index}/_doc/{token}"
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            url,
            data=json.dumps(write_info),
            headers=headers
        )
        print(response.json())
        if response.status_code == 201:
            writelog(write_info["fileName"], 4)
            return True
    except Exception as error:
        writelog([write_info["fileName"]], 3, text_error=str(error))
        return False


@check_connection_elasticsearch
def search_file(data_search: dict, search_word: str, obj_type_id: str) -> dict:
    # Если база пустая, то вылетит ошибка 'Нет соединения с elasticsearch'
    """Обобщеная функция поиска. Вид поиска зависит от входящего словаря
    data_search. На выходе - словарь ссылок на найденные файлы"""
    try:
        url = f"{BASE_URL}/{obj_type_id}/_search"
        headers = {"Content-Type": "application/json"}
        response = requests.get(
            url,
            data=json.dumps(data_search),
            headers=headers
        )
        row_dict = {}
        data = []
        time_search = response.json()["took"]
        count_search_doc = response.json()['hits']['total']['value']
        for link in response.json()["hits"]["hits"]:
            row_dict['pk'] = link["_source"]["pk"]
            row_dict['fileName'] = link["_source"]["fileName"]
            row_dict['fileSize'] = link["_source"]["fileSize"]
            row_dict['fileType'] = link["_source"]["fileType"]
            row_dict['fileLastModified'] = link["_source"]["fileLastModified"]
            row_dict['fileSize'] = link["_source"]["fileSize"]
            row_dict['filePath'] = link["_source"]["filePath"]
            score = link["_score"]
            row_dict['relevance'] = score
            data.append(row_dict)
        writelog(
            [
                f'Запрос: {search_word}',
                f'Время поиска: {time_search}',
                f'Количество найденных документов: {count_search_doc}'
            ],
            6
        )
        return data
    except Exception as error:
        writelog([f'Запрос: {search_word}'], 5, text_error=error)


def strict_search(search_word: str, obj_type_id: str) -> dict:
    """функция строго поиска"""
    data_search = {"query": {"match_phrase": {"description": search_word}}}
    answer_search = search_file(data_search, search_word, obj_type_id)
    return answer_search


def relevant_search(search_word: str, obj_type_id: str) -> dict:
    """функция релевантного поиска по фразе(с опечатками)"""
    data_search = {
        "from": 0, "size": 10,
        "query": {
            "multi_match": {

                "query": search_word,
                "fuzziness": "auto",
                "fields": "description",
            }
        }
    }
    answer_search = search_file(data_search, search_word, obj_type_id)
    return answer_search


def mixed_search(search_word: str, obj_type_id: str) -> dict:
    """Функция поиска по точному и неточному поиску. Возвращается dict
    в котором в начале выведены ссылки на файлы из точного поиска,затем
    из релевантного"""
    strict_search_list = strict_search(search_word, obj_type_id)
    relevant_search_list = relevant_search(search_word, obj_type_id)
    for item_strict in strict_search_list:
        for item_relevant in relevant_search_list:
            if item_strict['pk'] != item_relevant['pk']:
                strict_search_list.append(item_relevant)
            else:
                item_strict['relevance'] += item_relevant['relevance']
    return strict_search_list


# @check_connection_elasticsearch
def create_index(index_name: str, obj_type_id: str) -> None:
    # Добавить проверку уже созданного индекса
    """Функция создание индекса и определение анализаторов для
    дальнейшего использования"""
    data_setting = {
        "settings": {
            "analysis": {
                "analyzer":
                # Настройки анализатора
                {
                    "my_search_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "ru_stop",

                        ],
                    }
                },
                "filter": {
                    "ru_stop": {"type": "stop", "stopwords": "_russian_"},
                },
            }
        },
        "mappings": {
            #obj_type_id: {
                "properties": {
                    "fileName": {"type": "text"},
                    "author": {"type": "text"},
                    "fileLastModified": {"type": "text"},
                    "filePath": {"type": "text"},
                    "description": {
                        "type": "text",
                        "analyzer": "my_search_analyzer"
                        },
                    "pk": {"type": "text"},
                    "fileSize": {"type": "text"},
                }
            #}
        }
    }
    headers = {"Content-Type": "application/json"}
    response = requests.put(
        f"{BASE_URL}/{index_name}",
        headers=headers,
        data=json.dumps(data_setting)
    )
    print(response.json())


@check_connection_elasticsearch
def create_template_index():
    data_setting = {
        "index_patterns": ["*"],
        "settings": {
            "analysis": {
                "analyzer": {
                # Настройки анализатора
                    "my_search_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "ru_stop",
                        ],
                    }
                },
                "filter": {
                    "ru_stop": {"type": "stop", "stopwords": "_russian_"},
                },
            }
        },
        "mappings": {
            #obj_type_id: {
                "properties": {
                    "fileName": {"type": "text"},
                    "author": {"type": "text"},
                    "fileLastModified": {"type": "text"},
                    "filePath": {"type": "text"},
                    "description": {
                        "type": "text",
                        "analyzer": "my_search_analyzer"
                        },
                    "pk": {"type": "text"},
                    "fileSize": {"type": "text"},
                }
            #}
        }
    }
    headers = {"Content-Type": "application/json"}
    response = requests.put(
        f"{BASE_URL}/_template/template_1",
        headers=headers,
        data=json.dumps(data_setting)
    )
    print(response.json())

    # headers = {"Content-Type": "application/json"}
    # response = requests.put(
    #     f"{BASE_URL}/blog",
    #     headers=headers,
    #     #data=json.dumps(data_setting)
    # )
    # print(response.json())


def delete_file_from_elastic(index: str, token: str) -> None:
    '''Функция удаления записи из ElasticSearch'''
    try:
        url = f"{BASE_URL}/{index}/_delete_by_query"
        headers = {"Content-Type": "application/json"}
        data_delete = {
                "query": {
                    "term": {
                        "_id": token
                            }
                        }
                    }
        requests.post(
            url,
            data=json.dumps(data_delete),
            headers=headers
        )
        writelog([f'Index:{index}, token: {token}'], 8)
    except Exception as error:
        writelog([f'Index:{index}, token: {token}'], 7, text_error=error)


def search_to_elastic(search_word: str, type_search: str, obj_type_id: str) -> dict:
    '''Функция поиска записей в ES реализует поиски: строгий,релевантный
    и смешанный'''
    if type_search == 'STRICT_SEARCH':
        return strict_search(search_word, obj_type_id)
    elif type_search == 'RELEVANT_SEARCH':
        return relevant_search(search_word, obj_type_id)
    elif type_search == 'MIXED_SEARCH':
        return mixed_search(search_word, obj_type_id)


def test():
    import random
    #тестовые документы для отработки поиска
    #create_index('blog')
    # # write_file(read_file('test_document/Список Шиндлера.txt'), 'blog')
    # # write_file(read_file(
    # #     'test_document/Властелин колец: Возвращение короля.txt'),
    # #     'blog'
    # #     )
    # # write_file(read_file(
    # #     'test_document/Властелин колец: Две крепости.txt'),
    # #     'blog'
    # #     )
    # # write_file('test_document/Интерстеллар.txt', 'blog')
    # # write_file('test_document/Побег из Шоушенка.txt', 'blog')
    # # write_file('test_document/Зеленая миля.doc', 'blog')
    # # write_file('test_document/Марк Лутц - Изучаем Python.txt', 'blog')
    # # write_file_to_elastic('/home/zhirnov-sa/Документы/документооборот/search_elastic/test_document/pdf/file1.pdf', 'blog')
    # write_file_to_elastic('/home/zhirnov-sa/Документы/документооборот/search_elastic/test_document/exel/test.xlsx', 'blog', '421546123416')
    # write_file('/home/zhirnov-sa/Документы/документооборот/search_elastic/test_document/doc/test_doc.doc', 'blog')
    # write_file('/home/zhirnov-sa/Документы/документооборот/search_elastic/test_document/doc/test_rtf.rtf', 'blog')
    # write_file('/home/zhirnov-sa/Документы/документооборот/search_elastic/test_document/txt/test_txt.txt', 'blog')


    #тестовые документы для нагрузочного тестирования

    # start_time = time.time()
    # # create_index("blog")
    # tree = os.walk(
    #     "/home/zhirnov-sa/Документы/документооборот/search_elastic/test_book/"
    # )
    # for files in tree:
    #     for name in files[2]:
    #         write_file_to_elastic(files[0] + name, 'blog', str(random.randint(0, 100_000)), str(random.randint(0, 100_000)))
    # print("--- %s seconds ---" % (time.time() - start_time))


    # # Тестирование поиска

    # start_time = time.time()
    # # print(relevant_search('Мисси', 'blog6'))
    # print(strict_search('оформлением нашего сайта и благодарим активных пользователей за', 'blog6'))
    # #print(mixed_search("оформлением нашего сайта", 'blog6'))
    # print("--- %s seconds ---" % (time.time() - start_time))


#create_index('blog', 'post')
# create_index('blog', 'post2')
# # create_index('blog', 'post3')
import random
link = '/home/zhirnov-sa/Документы/документооборот/search_elastic/test_document/exel/_tablicy2007_0.xlsx'
write_file_to_elastic(link, 'blog6', str(random.randint(0, 100_000)), str(random.randint(0, 100_000)))

create_template_index()


test()

# qwe = relevant_search('таблицa из космоса', 'blog')
# for i in qwe:
#     print(i)


# def test_search():
#     #data_search = 
#     url = "http://127.0.0.1:9200/_search?scroll=1m{"size":100,"query":{"match":{"message":"foo"}}}"
#         #headers = {"Content-Type": "application/json"}
#     response = requests.get(
#         url,
#         # data=json.dumps(data_search),
#         # headers=headers
#     )
#     print(response.json())
#     row_dict = {}
#     data = []
#     time_search = response.json()["took"]
#     count_search_doc = response.json()['hits']['total']['value']
#     for link in response.json()["hits"]["hits"]:
#         row_dict['pk'] = link["_source"]["pk"]
#         row_dict['fileName'] = link["_source"]["fileName"]
#         row_dict['fileSize'] = link["_source"]["fileSize"]
#         row_dict['fileType'] = link["_source"]["fileType"]
#         row_dict['fileLastModified'] = link["_source"]["fileLastModified"]
#         row_dict['fileSize'] = link["_source"]["fileSize"]
#         row_dict['filePath'] = link["_source"]["filePath"]
#         score = link["_score"]
#         row_dict['relevance'] = score
#         data.append(row_dict)
#     writelog(
#         [
#             f'Запрос: {search_word}',
#             f'Время поиска: {time_search}',
#             f'Количество найденных документов: {count_search_doc}'
#         ],
#         6
#     )
#     return data
# except Exception as error:
#     writelog([f'Запрос: {search_word}'], 5, text_error=error)
