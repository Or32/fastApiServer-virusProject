import pickle
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from fastapi import UploadFile
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi import FastAPI,  WebSocket, WebSocketDisconnect
import string
import rsa
import logging
from cryptography.fernet import Fernet
import base64
import uvicorn



app = FastAPI()


log = [{'ip': 'example', 'text': 'example', 'predict': 'example'}]


public_key, private_key = rsa.newkeys(2048)

def encrypt_message(message, public_key):
    encrypted_message = rsa.encrypt(message.encode(), public_key)
    return encrypted_message

# Decrypt a message using the private key
def decrypt_message(encrypted_message, private_key):
    decrypted_message = rsa.decrypt(encrypted_message, private_key).decode()
    return decrypted_message


# Encrypt a string

with open("vectorizer (1).pkl", "rb") as file:
    vectorizer = pickle.load(file)

# Load the model
with open("classifierlr.pkl", "rb") as file:
    clf = pickle.load(file)




class WebSocketConnection:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def send_public_key(self):
        print('sending')
        await self.websocket.send_text(public_key.save_pkcs1().decode())

    async def receive_message(self, message: bytes,ip:str):
        decrypted_message = rsa.decrypt(message, private_key).decode()
        print(f"Received message from client: {decrypted_message}")
        text=decrypted_message
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

            # Placeholder prediction

            log.append({"ip": ip, "text": text, "predict": topic})
            return {'topic': topic}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logging.info("waiting")
    await websocket.accept()
    logging.info("connected")
    connection = WebSocketConnection(websocket)

    await connection.send_public_key()

    while True:
        message = await websocket.receive_bytes()
        ip = await websocket.receive_text()
        
        await connection.receive_message(message,ip)
    


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

if __name__ == "__main__":
    print("Waiting for connection...")
    uvicorn.run(app, host="0.0.0.0", port=8000)