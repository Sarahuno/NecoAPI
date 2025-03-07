from PyAPIx import app

@app.route('/')
def home(server, client_socket, path):
    return "Welcome to the homepage!"

@app.route('/data', methods=['POST'])
def data(server, client_socket, path):
    data = server.extract_body(client_socket)
    return f"Received POST data: {data}"

# PHP route example
@app.route('/index.php')
def php_example(server, client_socket, path):
    return server.execute_php(path)

app.start()
