import uvicorn
import fastapi
from fastapi.responses import HTMLResponse
import pickle
import regex
import pandas as pd
from pydantic import BaseModel
import json


from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords 
from nltk.tokenize import WordPunctTokenizer
from string import punctuation
from nltk.stem import WordNetLemmatizer


loaded_model = pickle.load(open('finalized_model7 (1).sav', 'rb'))


data = pickle.load(open('data.pkl', 'rb'))

wordnet_lemmatizer = WordNetLemmatizer()

stop = stopwords.words('english')

for punct in punctuation:
    stop.append(punct)

def filter_text(text, stop_words):
    word_tokens = WordPunctTokenizer().tokenize(text.lower())
    filtered_text = [regex.sub(u'\p{^Latin}', u'', w) for w in word_tokens if w.isalpha() and len(w) > 3]
    filtered_text = [wordnet_lemmatizer.lemmatize(w, pos="v") for w in filtered_text if not w in stop_words] 
    return " ".join(filtered_text)



def predict_from_text(model, text):
 
    text = filter_text(text, stop)
    tfidf = TfidfVectorizer(lowercase=False)
    fitted_vectorizer= tfidf.fit(data['filtered_text'])
    test_vec = fitted_vectorizer.transform([text])
    cat = ['Crime','Science','business','entertainment','food','graphics','historical','medical','politics','space','sport','technologie']
    code = [0,1,2,3,4,5,6,7,8,9,10,11]
    dic = dict([(code[x], cat[x])for x in range(12)])
    prediction = dic[model.predict(test_vec)[0]]
    
    return  prediction

app = fastapi.FastAPI()


def generate_html_response():
    html_content = """
  <html>
<head>
  <title>Array of Objects</title>
</head>
<body>
  <h1>List of Objects</h1>
  <ul>
    <!-- Loop through the array of objects -->
    <?php foreach ($log as $object): ?>
      <li>
        <!-- Access properties of the object -->
        <p>IP: <?php echo $object->ip; ?></p>
        <p>Text: <?php echo $object->text; ?></p>
        <p>Predict: <?php echo $object->predict; ?></p>
      </li>
    <?php endforeach; ?>
  </ul>
</body>
</html>

    """
    return HTMLResponse(content=html_content, status_code=200)



class Item(BaseModel):
    text: str
    ip: str
  







@app.post("/user/")
async def create_item(item: Item):
    y = item.json()
    x = json.loads(y)   
    if x["text"]!=  "":
        texts= [x["text"]]
        predictions = pd.Series(texts).apply(lambda x : predict_from_text(loaded_model, x))
        print('IP:' +x["text"] +':')  
        print('IP:' +x["ip"] +':')
        predict = predictions
        print(predict)
        log.append({"ip":x["ip"], "text": x["text"], "predict":predict[0] })
        print(log)

    
    
    
    return log
  
  

@app.get("/")
def read_root():
    print(log)
    return generate_html_response()

    




log = [{'ip': 'example', 'text': 'example', 'predict': 'example'}]

@app.get("/object-list")
def get_object_list():

  html ="""
  <html>
  <head>
    <title>Array of Objects</title>
  </head>
  <body>
    <h1>List of Objects</h1>
    <ul>
  """


  for obj in log:

    ip = obj["ip"]
    text = obj["text"]
    predict = obj["predict"]


    html += f"<li><p>IP: {ip}</p><p>Text: {text}</p><p>Predict: {predict}</p></li>"


  html += "</ul></body></html>"


  return HTMLResponse(content=html, status_code=200)