import flask
from flask import request
import os
from bot import Bot, QuoteBot, ImageProcessingBot

app = flask.Flask(__name__)

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']


@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


if __name__ == "__main__":
    #adding this so that i can see the tests there might be a problem i cant pus any more 
    #bot = Bot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)
    #bot = QuoteBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)
    bot = ImageProcessingBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)

    app.run(host='0.0.0.0', port=8443,ssl_context=('/home/ubuntu/YOURPUBLIC.pem','/home/ubuntu/YOURPRIVATE.key'))
