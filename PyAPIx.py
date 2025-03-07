import socket
import threading
import subprocess
import os

PHP_DIR = os.path.join("php", 'php.exe')

class PyAPIx:
    def __init__(self, host='localhost', port=5000, php_executable=PHP_DIR):
        self.host = host
        self.port = port
        self.routes = {}
        self.php_executable = php_executable

    def route(self, path, methods=['GET']):
        def wrapper(func):
            if path not in self.routes:
                self.routes[path] = {}
            for method in methods:
                self.routes[path][method] = func
            return func
        return wrapper

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"Server started on http://{self.host}:{self.port}")
            while True:
                client_socket, _ = server_socket.accept()
                threading.Thread(target=self.handle_request, args=(client_socket,)).start()

    def handle_request(self, client_socket):
        try:
            request = client_socket.recv(1024).decode()
            lines = request.split('\r\n')
            if len(lines) < 1:
                client_socket.close()
                return
            request_line = lines[0]
            method, path, _ = request_line.split()
            if path.endswith('.php'):
                response_body = self.execute_php(path)
                self.send_response(client_socket, "HTTP/1.1 200 OK", response_body, content_type='text/html')
            elif path in self.routes and method in self.routes[path]:
                response_body = self.routes[path][method](self, client_socket, path)
                self.send_response(client_socket, "HTTP/1.1 200 OK", response_body)
            else:
                self.send_response(client_socket, "HTTP/1.1 404 Not Found", f"Path {path} or method {method} not found")
        except Exception as e:
            self.send_response(client_socket, "HTTP/1.1 500 Internal Server Error", str(e))
        finally:
            client_socket.close()

    def send_response(self, client_socket, status_line, body, content_type='text/plain'):
        response = f"{status_line}\r\n"
        response += f"Content-Type: {content_type}; charset=utf-8\r\n"
        response += "Content-Length: " + str(len(body.encode())) + "\r\n"
        response += "Connection: close\r\n"
        response += "\r\n"
        response += body
        client_socket.sendall(response.encode())

    def extract_body(self, client_socket):
        request = client_socket.recv(1024).decode()
        body = request.split('\r\n\r\n', 1)
        return body[1] if len(body) > 1 else ""

    def execute_php(self, path):
        php_file = os.path.join(os.getcwd(), path.lstrip('/'))
        if os.path.exists(php_file):
            try:
                result = subprocess.run([self.php_executable, php_file], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout
                else:
                    return f"<h1>PHP Error:</h1><pre>{result.stderr}</pre>"
            except Exception as e:
                return f"<h1>Error executing PHP:</h1><pre>{str(e)}</pre>"
        return f"<h1>404 Not Found</h1><p>PHP file '{path}' not found.</p>"

app = PyAPIx()