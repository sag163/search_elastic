from django.shortcuts import render
from django.core.paginator import Paginator
from ..load_file import strict_search, mixed_search, relevant_search


def test_paginator(request, search_word: str, type_search: str, obj_id: str) -> list:
    search_word = ''
    type_search = ''
    obj_id = ''
    if type_search == 'STRICT_SEARCH':
        answer =  strict_search(search_word, obj_id)
    elif type_search == 'RELEVANT_SEARCH':
        answer = relevant_search(search_word, obj_id)
    elif type_search == 'MIXED_SEARCH':
        answer = mixed_search(search_word, obj_id)
    paginator = Paginator(answer, 6)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "index.html",
        {'page': page, 'paginator': paginator},
    )
