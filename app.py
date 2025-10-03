import os, base64, email, re, nltk, pandas as pd
from flask import Flask, render_template_string
from bs4 import BeautifulSoup
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import google.auth.transport.requests
import google.oauth2.credentials
import json

# Flask app
app = Flask(__name__)

# Download nltk data if needed
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    tokens = text.split()
    tokens = [stemmer.stem(word) for word in tokens if word not in stop_words]
    return ' '.join(tokens)

# Simple training dataset (demo)
train_data = {
    "text": [
        "Congratulations you won free lottery claim now",
        "Urgent verify your bank account immediately",
        "Meeting scheduled tomorrow at 5pm",
        "Project deadline is next week",
        "Win a free iPhone click here"
    ],
    "label": [1,1,0,0,1]  # 1=spam, 0=ham
}
df_train = pd.DataFrame(train_data)
tfidf = TfidfVectorizer()
X_train = tfidf.fit_transform(df_train["text"])
y_train = df_train["label"]
model = MultinomialNB()
model.fit(X_train, y_train)

# Gmail auth
def authenticate_gmail():
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    if os.path.exists('token.json'):
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file('token.json', scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            creds_json = os.environ.get("GOOGLE_CREDENTIALS")
            if creds_json:
                with open("credentials.json", "w") as f:
                    f.write(creds_json)
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', scopes)
                creds = flow.run_local_server(port=0)
                with open('token.json','w') as token:
                    token.write(creds.to_json())
    return creds

# Get email body
def get_email_body(raw_email_string):
    msg = email.message_from_string(raw_email_string)
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    body = part.get_payload(decode=True).decode()
                    break
                except: pass
            if ctype == 'text/html' and 'attachment' not in cdispo:
                try:
                    html_body = part.get_payload(decode=True).decode()
                    soup = BeautifulSoup(html_body, 'html.parser')
                    body = soup.get_text()
                except: pass
    elif msg.get_content_type() == 'text/plain':
        try: body = msg.get_payload(decode=True).decode()
        except: pass
    elif msg.get_content_type() == 'text/html':
        try:
            html_body = msg.get_payload(decode=True).decode()
            soup = BeautifulSoup(html_body, 'html.parser')
            body = soup.get_text()
        except: pass
    return body

@app.route('/')
def home():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    emails = []
    if messages:
        for message in messages[:10]:
            try:
                msg = service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
                msg_str = base64.urlsafe_b64decode(msg['raw']).decode('utf-8')
                body = get_email_body(msg_str)
                processed = preprocess_text(body)
                pred = model.predict(tfidf.transform([processed]))[0]
                emails.append({
                    "id": message['id'],
                    "body": body[:300],
                    "prediction": "Spam 🚫" if pred==1 else "Ham ✅"
                })
            except Exception as e:
                emails.append({"id": message['id'], "body": "Error reading email", "prediction": "Unknown"})
    TEMPLATE = """
    <html><head><title>Gmail Spam Detector</title></head>
    <body><h2>📧 Gmail Spam Detector</h2>
    {% for mail in emails %}
      <div style="border:1px solid #ccc;padding:10px;margin:10px;">
        <p><b>ID:</b> {{mail.id}}</p>
        <p><b>Body:</b> {{mail.body}}</p>
        <p><b>Prediction:</b> {{mail.prediction}}</p>
      </div>
    {% endfor %}
    </body></html>
    """
    return render_template_string(TEMPLATE, emails=emails)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
