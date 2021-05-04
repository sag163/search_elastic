import requests
import os
import time


BASE_URL = 'http://127.0.0.1:9200'


def check_connection_elasticsearch(func):
    '''Проверка стостояние соединения с elasticsearch, при отсутствии соединения
    выполниться 1 попытка запуска сервера'''
    def check(*args, **kwargs):
        for i in range(2):
            try:
                if requests.get(BASE_URL).status_code == 200:
                    print('Сервер отвечает')
                    return func(*args, **kwargs)
            except Exception as e:
                print(e)
                if i == 0:
                    print('запускаю Сервер'*10)
                    os.system('docker run -d -p 9200:9200 -e "discovery.type=single-node"\
                        docker.elastic.co/elasticsearch/elasticsearch:7.7.0')
                    time.sleep(18)
                else:
                    return 'Нет соединения с elasticsearch'
    return check




list1 = ['h', 'u', 'g', 'c']

list2 = ['h', 't', '3', 'c']

list3 = []

for i in list1:
    if i in list2:
        list3.append([i, 2])
        list2.pop(list2.index(i))
     
print(list3 + list2)