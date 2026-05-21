import os
import json
import logging
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN', '')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET', '')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

KEYWORDS = ['chaweng', 'chaweng project', 'chaweng bot']
DATA_FILE = 'chaweng_data.json'

def load_data():
      if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                              return json.load(f)
                      return {'messages': [], 'keyword_count': {}}

  def save_data(data):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
                  json.dump(data, f, ensure_ascii=False, indent=2)

    def detect_keywords(text):
          found = []
          text_lower = text.lower()
          for kw in KEYWORDS:
                    if kw.lower() in text_lower:
                                  found.append(kw)
                          return found

@app.route('/health', methods=['GET'])
def health():
      return {'status': 'ok', 'bot': 'chaweng-line-bot', 'time': str(datetime.now())}, 200

@app.route('/data', methods=['GET'])
def get_data():
      data = load_data()
      return data, 200

@app.route('/stats', methods=['GET'])
def get_stats():
      data = load_data()
      return {
          'total_messages': len(data.get('messages', [])),
          'keyword_count': data.get('keyword_count', {}),
          'keywords_tracked': KEYWORDS
      }, 200

@app.route('/callback', methods=['POST'])
def callback():
      signature = request.headers.get('X-Line-Signature', '')
      body = request.get_data(as_text=True)
      logger.info('Request body: ' + body)
      try:
                handler.handle(body, signature)
except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
      user_id = event.source.user_id
      text = event.message.text
      timestamp = str(datetime.now())
      found_keywords = detect_keywords(text)

    data = load_data()
    entry = {
              'user_id': user_id,
              'message': text,
              'timestamp': timestamp,
              'keywords': found_keywords
    }
    data['messages'].append(entry)

    for kw in found_keywords:
              data['keyword_count'][kw] = data['keyword_count'].get(kw, 0) + 1

    save_data(data)

    if found_keywords:
              reply = 'Keywords detected: ' + ', '.join(found_keywords) + ' - saved to Chaweng database!'
else:
          reply = 'Message received: ' + text

    line_bot_api.reply_message(
              event.reply_token,
              TextSendMessage(text=reply)
    )

if __name__ == '__main__':
      port = int(os.environ.get('PORT', 5000))
      app.run(host='0.0.0.0', port=port)
