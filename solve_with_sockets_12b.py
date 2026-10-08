import socket
from bs4 import BeautifulSoup
from urllib.parse import urlencode

HOST = "hw1.alexbers.com"
ID = "94428029cc39b8c513aa88ffbef44b82"


class Response:
    def __init__(self, raw_data: str):
        if "\r\n\r\n" in raw_data:
            headers, self.content = raw_data.split("\r\n\r\n", 1)
        else:
            headers, self.content = raw_data, raw_data

        lines = headers.split("\r\n")

        if lines and lines[0].startswith("HTTP/"):
            parts = lines[0].split(" ")
            self.status_code = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 200
        else:
            self.status_code = 200


class Client:
    def __init__(self, host: str, port: int = 80):
        self.host = host
        self.port = port

    def get(self, address: str = "/", cookies: dict = None, params: dict = None, headers: dict = None) -> Response:
        cookies_str, headers_str, params_str = self._prepare_components(cookies, params, headers)

        request = (
            f"GET {address}{params_str} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Cookie: {cookies_str}\r\n"
            f"{headers_str}"
            f"Connection: close\r\n"
            f"\r\n"
        )

        return self._send_or_receive(request.encode("utf-8"))

    def post(self, address: str = "/", cookies: dict = None, params: dict = None, headers: dict = None, data: dict = None) -> Response:
        cookies_str, headers_str, params_str = self._prepare_components(cookies, params, headers)
        data = data or {}
        body_bytes = urlencode(data).encode("utf-8")

        request = (
            f"POST {address}{params_str} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Cookie: {cookies_str}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"  
            f"{headers_str}"
            f"Content-Length: {len(body_bytes)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )

        return self._send_or_receive(request.encode("utf-8") + body_bytes)

    def post_files(self, address: str = "/", cookies: dict = None, files: dict = None) -> Response:
        cookies_str, _, _ = self._prepare_components(cookies)
        files = files or {}
        boundary = "Boundary"
        body_bytes = b""

        for name, content in files.items():
            content_bytes = content.encode("utf-8")
            body_bytes += (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
                f"Content-Type: text/plain\r\n"
                f"\r\n"
            ).encode("utf-8")

            body_bytes += content_bytes + b"\r\n"

        body_bytes += f"--{boundary}--\r\n".encode("utf-8")

        request = (
            f"POST {address} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Cookie: {cookies_str}\r\n"
            f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
            f"Content-Length: {len(body_bytes)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        return self._send_or_receive(request.encode("utf-8") + body_bytes)

    def _send_or_receive(self, request_bytes: bytes) -> Response:
        with socket.socket() as sock:
            sock.connect((self.host, self.port))
            sock.sendall(request_bytes)

            raw_response = b""

            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                raw_response += chunk

        return Response(raw_response.decode("utf-8", errors="replace"))

    def _prepare_components(self, cookies: dict = None, params: dict = None, headers: dict = None) -> tuple[str, str, str]:
        cookies = cookies or {}
        params = params or {}
        headers = headers or {}

        cookies_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        headers_str = "".join(f"{k}: {v}\r\n" for k, v in headers.items())
        params_str = "?" + urlencode(params) if params else ""

        return cookies_str, headers_str, params_str


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


client = Client(HOST, 80)
response = client.get(cookies={"user": ID})
result_html = response.content
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
            response = client.get(address=address, cookies=cookies, params=parameters, headers=headers)
        case _ if "Отправьте POST-запрос" in result_html:
            address = parse_html_address(result_html[result_html.find("Отправьте POST-запрос"):])
            response = client.post(address=address, cookies=cookies, params=parameters, headers=headers, data=data)
        case _ if "Загрузите файлы по адресу" in result_html:
            address = parse_html_address(result_html[result_html.find("Загрузите файлы по адресу"):])
            files = parse_html_table(result_html[result_html.find("Загрузите файлы по адресу"):])
            response = client.post_files(address=address, cookies=cookies, files=files)
        case _ if "Перейдите по" in result_html:
            link = parse_html_link(result_html[result_html.find("Перейдите по"):])
            response = client.get(address=link, cookies=cookies, params=parameters, headers=headers)
        case _:
            break

    result_html = response.content

print(result_html)
print(f"Всего запросов: {requests_count}")