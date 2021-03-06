"""! @brief Парсер html страницы расписания."""
##
# @file html_parser.py
#
# @brief Парсинг файлов расписания.
#
# @section description_html_parser Описание
# Предоставление методов для удобного парсинга страницы с расписанием
#
# @section libraries_html_parser Модули
# - requests
#   - Получение содержимого с html документа.
# - bs4
#   - Парсинг html документа
#
# @section notes_html_parser Заметки
# - @maybe_next_time используется для обозначения методов,
#       которые могут получить новый функционал в будущем
#
# @section list_of_changes_html-parser Список изменений
#   - Файл создан Савинов В.В. 14/04/2022
#   - Добавлена doxygen документация Нестеренко А.И. 14/04/2022
#   - Добавлены методы Нестеренко А.И. 14/04/2022:
#       - check_response
#
# @section author_html_parser Авторы
# - Савинов В.В.
# - Нестеренко А.И.
#
# Copyright (c) 2022 ИРИБ.  All rights reserved.


from xmlrpc.client import Boolean
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
import system
import utils

BASE_URL = 'https://www.sevsu.ru'
URL = 'https://www.sevsu.ru/univers/shedule'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0'}


def get_base_block(url: str, headers: dict) -> ResultSet:
    """! Get base div with all institutes

    Этот метод используется для получения базового блока div с расписанями
    (Берет только первый блок для студентов ОФО).

    @maybe_next_time Получение расписания не только для ОФО,
    но и для ЗФО

    @param url  Ссылка на страницу расписания СевГУ
    @param headers  Настройки браузера

    @return Все блоки институтов с классом "su-spoiler"
    """
    html = requests.get(url=url, headers=headers)
    if not check_response(html.status_code):
        return None
    soup = BeautifulSoup(html.text, "lxml")
    return soup.find("div", class_="su-column-content").find_all("div", class_="su-spoiler")


def get_institute_name(soup: Tag) -> str:
    """! Get institution name
    
    Этот метод используется для получения названия института

    @param soup Объект Tag, полученный путем разбиения базового блока на
    блоки отдельных институтов.

    @return Название института
    """
    return soup.find('h3').text


def get_files_url(soup: Tag) -> list:
    """! Get links to files with xls & xlsx extension

    Этот метод берет используется для получения ссылок на все
    расписания в блоке института.
    
    @param soup Объект Tag, полученный путем разбиения базового блока на
    блоки отдельных институтов

    @return Список ссылок на файлы (без корневого адресса)
    """
    links = soup.find("div", class_="su-clearfix").find_all("a")
    links = [link.get("href") for link in links]
    links = [link for link in links if utils.get_extension(link) == 'xls' or utils.get_extension(link) == 'xlsx']
    return links


def get_semester_index(soup: Tag) -> list:
    """! Get index of 1 & 2 semester
    
    Этот метод используется для получения индексов параграфов с
    названиями семетров

    @param soup Объект Tag, полученный путем разбиения базового блока на
    блоки отдельных институтов

    @return список индексов:\n
        Если 2 элемента в списке, то [0] - первый семестр [1] - второй семестр\n
        Если 1 элемент в списке, то [0] - второй семестр\n
        Если 0 элементов в списке, то расписаний для этого института нет
    """
    indexes = [paragraph.text.replace('\xa0', ' ').lower() for paragraph in soup.find_all('p')]
    indexes = [index for index in range(len(indexes)) if 'семестр' in indexes[index]]
    return indexes


def get_schedule_from_first_semester(soup: Tag) -> list:
    """! Get shedule for 1 semester 
    
    Этот метод используется для получения расписания института на 1 семестр
    
    @param soup Объект Tag, полученный путем разбиения базового блока на
    блоки отдельных институтов

    @return Список ссылок расписания института на 1 семестр, если таковых нет
    будет возвращен пустой список
    """
    indexes = get_semester_index(soup)
    if len(indexes) == 2:
        return get_files_url(soup)[:indexes[-1] - indexes[0] - 1]
    return []


def get_schedule_from_second_semester(soup: Tag) -> list:
    """! Get shedule for 2 semester 
    
    Этот метод используется для получения расписания института на 2 семестр
    
    @param soup Объект Tag, полученный путем разбиения базового блока на
    блоки отдельных институтов

    @return Список ссылок расписания института на 2 семестр, если таковых нет
    будет возвращен пустой список
    """
    indexes = get_semester_index(soup)
    if len(indexes) == 2:
        return get_files_url(soup)[indexes[-1] - 1:]
    elif len(indexes) == 1:
        return get_files_url(soup)[indexes[0] + 1:]
    return []


def check_response(response: int) -> Boolean:
    """! Check if SevSU server is responsing

    Этот метод используется для проверки работоспособности сайта

    @param response Код ответа от сервера

    @return Возвращает True если ошибок с ответом от сервера нет
    """
    return True if response == 200 else False


def main():
    """! Function to test and debug code

    Эта функция используется для отладки написанного кода
    """
    base = get_base_block(URL, HEADERS)
    if base == None:
        return None
    system.make_directory('General')
    for tag in base:
        if utils.get_current_semester() == 1:
            name = get_institute_name(tag)
            a = [BASE_URL + link for link in get_schedule_from_first_semester(tag)]
        else:
            name = get_institute_name(tag)
            a = [BASE_URL + link for link in get_schedule_from_second_semester(tag)]
        if a:
            for index, item in enumerate(a):
                path = utils.transliteration_to_en_from_ru(name)
                system.save_file(path, str(index), item, utils.get_extension(item))


if __name__ == '__main__':
    main()
