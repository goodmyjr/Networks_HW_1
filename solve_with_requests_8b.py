import io
import requests
from bs4 import BeautifulSoup

ID = "94428029cc39b8c513aa88ffbef44b82"
URL = "http://hw1.alexbers.com"

session = requests.Session()


def parse_html_address(text):
    """Достает адрес, куда отправить запрос"""
    soup = BeautifulSoup(text, "html.parser")
    return soup.find("code").text


def parse_html_table(text):
    """Парсит html-таблицу"""
    soup = BeautifulSoup(text, "html.parser")
    result: dict[str, str] = {}
    rows_text = []

    for table in soup.find("table").find_all("code"):
        rows_text.append(table.text)

    for i in range(0, len(rows_text), 2):
        result[rows_text[i]] = rows_text[i + 1]

    return result


def parse_html_link(text):
    """Достает ссылку из тега <a href=>"""
    soup = BeautifulSoup(text, "html.parser")
    return soup.find("a").get("href")


response = session.get(URL, cookies={"user": ID})
result_html = response.content.decode()
requests_count = 0

while response.status_code == 200:
    requests_count += 1
    print(f"Шаг: {requests_count}")

    headers = {}
    data = {}
    cookies = {}
    parameters = {}

    if "Запрос должен иметь следующие заголовки:" in result_html:
        headers = parse_html_table(result_html[result_html.find("Запрос должен иметь следующие заголовки:"):])
    if "Запрос должен иметь следующие данные формы:" in result_html:
        data = parse_html_table(result_html[result_html.find("Запрос должен иметь следующие данные формы:"):])
    if "В запросе должны быть выставлены cookie:" in result_html:
        cookies = parse_html_table(result_html[result_html.find("В запросе должны быть выставлены cookie:"):])
    if "При переходе выставьте следующие параметры запроса, указанные в таблице:" in result_html:
        parameters = parse_html_table(result_html[result_html.find("При переходе выставьте следующие параметры запроса, указанные в таблице:"):])

    cookies["user"] = ID

    match result_html:
        case _ if "Отправьте GET-запрос" in result_html:
            address = parse_html_address(result_html[result_html.find("Отправьте GET-запрос"):])
            response = session.get(URL + address, cookies=cookies, params=parameters, headers=headers)
        case _ if "Отправьте POST-запрос" in result_html:
            address = parse_html_address(result_html[result_html.find("Отправьте POST-запрос"):])
            response = session.post(URL + address, cookies=cookies, params=parameters, headers=headers, data=data)
        case _ if "Загрузите файлы по адресу" in result_html:
            address = parse_html_address(result_html[result_html.find("Загрузите файлы по адресу"):])
            files = parse_html_table(result_html[result_html.find("Загрузите файлы по адресу"):])
            files_to_send = [('file', (name, io.BytesIO(content.encode('utf-8')), 'text/plain')) for name, content in files.items()]
            response = session.post(URL + address, cookies=cookies, files=files_to_send)
        case _ if "Перейдите по" in result_html:
            link = parse_html_link(result_html[result_html.find("Перейдите по"):])
            response = session.get(URL + link, cookies=cookies, params=parameters, headers=headers)
        case _:
            break

    result_html = response.content.decode()

print(result_html)
print(f"Всего запросов: {requests_count}")