
import pickle
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from fastapi.responses import HTMLResponse
import string
import rsa
import logging
from cryptography.fernet import Fernet
import base64
import socket

# Load the vectorizer
with open("vectorizer (1).pkl", "rb") as file:
    vectorizer = pickle.load(file)

# Load the model
with open("classifierlr.pkl", "rb") as file:
    clf = pickle.load(file)

app = FastAPI()

log = [{'ip': 'example', 'text': 'example', 'predict': 'example'}]

# Generate a secret key
key = Fernet.generate_key()

# Create a Fernet cipher object with the key
cipher = Fernet(key)

# Define a request body schema
class TextInput(BaseModel):
    message: str
    ip: str

@app.on_event("startup")
async def startup_event():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_host = 'localhost'
    server_port = 12345
    server_socket.bind((server_host, server_port))
    server_socket.listen(1)
    print('Server listening on {}:{}'.format(server_host, server_port))

@app.get('/check')
async def get_public_key():
    public_key = base64.urlsafe_b64encode(key).decode()
    return {"public_key": public_key}

@app.post('/predict')
async def predict_topic(input: TextInput):
    text = input.message
    ip = input.ip
    decrypted_bytes = cipher.decrypt(base64.urlsafe_b64decode(text.encode()))
    text = decrypted_bytes.decode()

    print(text)
    if text == "":
        return
    else:
        # Preprocess the text
        tokens = word_tokenize(text.lower())
        stopwords_list = stopwords.words('english') + list(string.punctuation)
        tokens = [token for token in tokens if token not in stopwords_list]
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(token) for token in tokens]
        preprocessed_text = ' '.join(tokens)
        text_vec = vectorizer.transform([preprocessed_text])
        topic = clf.predict(text_vec)[0]

        log.append({"ip": ip, "text": text, "predict": topic})
        return {'topic': topic}

@app.get("/")
async def get_object_list():
    html = """
    <html>
    <head>
        <title>Array of Objects</title>
        <style>
            body {
                font-family: Arial, sans-serif;
            }

            h1 {
                color: #333;
                text-align: center;
            }

            ul {
                list-style-type: none;
                padding: 0;
            }

            li {
                margin-bottom: 20px;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            }

            li p {
                margin: 5px 0;
            }

            .filters {
                margin-bottom: 20px;
            }

            .filters input[type="text"] {
                padding: 5px;
                width: 200px;
            }

            .filters select {
                padding: 5px;
            }
        </style>
    </head>
    <body>
        <h1>admin dashboard</h1>

        <div class="filters">
            <label for="ip_filter">Filter by IP:</label>
            <input type="text" id="ip_filter" onkeyup="filterByIP()" placeholder="Enter IP address">

            <label for="predict_filter">Filter by Prediction:</label>
            <select id="predict_filter" onchange="filterByPrediction()">
                <option value="">All</option>
                <option value="Crime">Crime</option>
                <option value="Science">Science</option>
                <option value="business">Business</option>
                <option value="entertainment">Entertainment</option>
                <option value="food">Food</option>
                <option value="graphics">Graphics</option>
                <option value="historical">Historical</option>
                <option value="medical">Medical</option>
                <option value="politics">Politics</option>
                <option value="space">Space</option>
                <option value="sport">Sport</option>
                <option value="technologie">Technologie</option>
            </select>
        </div>

        <ul id="object_list">
    """

    for obj in log:
        ip = obj["ip"]
        text = obj["text"]
        predict = obj["predict"]

        html += f"<li data-ip='{ip}' data-predict='{predict}'><p>IP: {ip}</p><p>Text: {text}</p><p>Predict: {predict}</p></li>"

    html += """
        </ul>

        <script>
            function filterByIP() {
                const input = document.getElementById('ip_filter');
                const filter = input.value.toUpperCase();
                const list = document.getElementById('object_list');
                const items = list.getElementsByTagName('li');

                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    const ip = item.getAttribute('data-ip');

                    if (ip.toUpperCase().includes(filter)) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                }
            }

            function filterByPrediction() {
                const select = document.getElementById('predict_filter');
                const filter = select.value.toUpperCase();
                const list = document.getElementById('object_list');
                const items = list.getElementsByTagName('li');

                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    const predict = item.getAttribute('data-predict');

                    if (filter === '' || predict.toUpperCase() === filter) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                }
            }
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html, status_code=200)


def handle_client(client_socket):
    while True:
        # Receive data from the client
        data = client_socket.recv(1024).decode('utf-8')
        if not data:
            break

        # Process the data
        text, ip = data.split(';')
        response = predict_topic(TextInput(message=text, ip=ip))

        # Send response back to the client
        client_socket.send(str(response).encode('utf-8'))

    # Close the connection
    client_socket.close()


if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_host = 'localhost'
    server_port = 12345
    server_socket.bind((server_host, server_port))
    server_socket.listen(1)
    print('Server listening on {}:{}'.format(server_host, server_port))

    while True:
        client_socket, client_address = server_socket.accept()
        print('Received connection from {}:{}'.format(client_address[0], client_address[1]))

        # Start a new thread to handle the client request
        threading.Thread(target=handle_client, args=(client_socket,)).start()
