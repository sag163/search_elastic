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
                requests.get(BASE_URL)
                print('Сервер отвечает'*100)
                return func(*args, **kwargs)
            except:
                if i == 0:
                    print('запускаю Сервер'*100)
                    os.system('docker run -d -p 9200:9200 -e "discovery.type=single-node"\
                        docker.elastic.co/elasticsearch/elasticsearch:7.7.0')
                    time.sleep(18)
                else:
                    return 'Нет соединения с elasticsearch'
    return check
