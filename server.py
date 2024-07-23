import os.path
import socket
import json
import pathlib


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = self.init_server()

    def init_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen()
        return server_socket

    def connect_client(self):
        self.client_socket, self.client_address = self.socket.accept()
        return self.client_socket, self.client_address

    def reconnect_client(self):
        print("connecting client...")
        self.client_socket, self.client_address = self.connect_client()

    def close_client(self):
        self.client_socket.close()
        self.client_socket, self.client_address = None, None

    def close(self):
        self.socket.close()

    def get_request(self, num_of_bytes=1024):
        print("Getting request")
        data = self.client_socket.recv(num_of_bytes).decode()
        return data

    def send_response(self, data: bytes):
        self.client_socket.send(data)

    def is_client_connected(self):
        return self.client_socket is not None


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


# ================================================================

CONFIG_FILE = "config.json"
config = read_json(CONFIG_FILE)
HTTP_VERSION = config['httpVersion']
ROOT_DIRECTORY = config['rootDirectory']
WELCOME_PAGE = ROOT_DIRECTORY + config['welcomePage']


# ================================================================

def file_exists(file):
    return os.path.isfile(file)


def build_http_response(response_code, content_type, data: bytes):
    response = f"{HTTP_VERSION} {response_code} OK\r\n" \
               f"Content-Length: {len(data)}\r\n" \
               f"Content-Type: {content_type}\r\n" \
               f"\r\n".encode()
    response += data
    return response


def get_file_content(filename):
    with open(filename, 'rb') as file:
        data = file.read()
    return data


def get_file_extension(filename):
    return pathlib.Path(filename).suffix


def get_content_type(file_extension):
    content_type_dict = {
        ".html": "text/html; charset=utf-8",
        ".text": "text/html; charset=utf-8",
        ".jpg": "image/jpeg",
        ".js": "text/javascript; charset=UTF-8",
        ".css": "text/css",
        # ".ico": "   /x-icon"
    }
    return content_type_dict.get(file_extension)


def get_response(request):
    status_code = 200
    request_sections = request.split("\r\n")
    request_line = request_sections[0]
    request_line_sections = request_line.split(" ")

    if len(request_line_sections) != 3:
        status_code = 500
        print(":(")
        return status_code, "Internal server error: Not a proper http request".encode()
    else:
        method, requested_file, protocol = request_line_sections

    if requested_file == "/":
        requested_file = WELCOME_PAGE
    else:
        requested_file = ROOT_DIRECTORY + requested_file

    if not file_exists(requested_file):
        print(":'(", requested_file)
        status_code = 404
        return status_code, "404: File not found!".encode()

    file_content = get_file_content(requested_file)
    file_extension = get_file_extension(requested_file)
    content_type = get_content_type(file_extension)
    response = build_http_response(status_code, content_type, file_content)
    return status_code, response


def main():
    server = Server(host="0.0.0.0", port=80)
    while True:
        server.socket.listen()
        client_socket, client_address = server.connect_client()
        print("Connected:", client_address)

        request = server.get_request()
        print(request)
        status_code, response = get_response(request)

        # print("RESPONSE:", response)
        server.send_response(response)


if __name__ == '__main__':
    main()
