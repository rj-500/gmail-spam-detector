# 📧 Gmail Spam Detection App

A Flask web app that connects to Gmail, fetches your inbox emails, and classifies them as **Spam 🚫** or **Ham ✅**.

## 🚀 Features
- Gmail API integration
- Preprocessing with NLTK
- Spam detection using Naive Bayes + TF-IDF
- Flask web UI
- Deployable on **Render** with one click

## 🖥️ Local Setup
```bash
pip install -r requirements.txt
python app.py
```
Visit `http://127.0.0.1:5000`

## 🌍 One-Click Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Environment Variables on Render
- `GOOGLE_CREDENTIALS` = contents of your Gmail API `credentials.json` (paste the JSON string)

## ⚠️ Notes
- Run once locally to generate `token.json` and commit it, so Render won’t ask for login again.
- First 10 emails in inbox will be displayed.
