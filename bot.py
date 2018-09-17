# -*- coding: utf-8 -*-
import logging
import os
import re
import requests
import vk_api as vk
import telebot as tg

# Configure Telebot
tg_token = os.environ['TELEGRAM_TOKEN']
proxy = os.environ['PROXY_LINK']
if proxy:
    tg.apihelper.proxy = {'https': proxy}
bot = tg.TeleBot(tg_token)
tg.logger.setLevel(logging.DEBUG)

app_id = os.environ['VK_CLIENT_ID']
vk_sessions = dict()


class VkSession(object):
    cid = 0
    token = ''
    chats = list()

    def __init__(self, cid, vk_token, chats=[]):
        self.token = vk_token
        self.chats = chats
        vk_sessions[cid] = self

    def get_vk_api(self):
        vk_session = vk.VkApi(token=self.token, app_id=app_id)
        vk_api = vk_session.get_api()
        try:
            vk_api.account.getProfileInfo()
            return vk_api
        except vk.ApiError as e:
            bot.send_message(self.cid, e)
            print(e)
            return False


@bot.message_handler(commands=['auth'])
def auth(m):
    """Handles VK authentication"""

    cid = m.chat.id

    # Check if already authorized
    if cid in vk_sessions:
        vk_api = vk_sessions[cid].get_vk_api()
        user = vk_api.account.getProfileInfo()
        str = 'Already authorized: '+user['first_name']+' '+user['last_name']
        bot.send_message(cid, str)
        return

    # If not, send an auth link
    params = {
        'client_id': app_id,
        'redirect_uri': 'https://oauth.vk.com/blank.html',
        'scope': 4096 + 2,
        'v': '5.84',
        'display': 'page',
        'response_type': 'token',
        'revoke': 1,
        }
    res = requests.get('https://oauth.vk.com/authorize', params=params)

    str = "Authorize here and send back the access token: \n"+res.url
    r = bot.send_message(cid, str)
    # And wait for answer
    bot.register_next_step_handler(r, get_vk_token)


def get_vk_token(m):
    """Gets and parses an access token from user's message"""

    cid = m.chat.id
    vk_token = None

    text = m.text

    # Parses token itself or redirect link
    token_match = re.match(r"^\w{85}$", text)
    link_match = re.search(r"^https?://.*access_token=(\w{85}).*$", text)
    if token_match:
        bot.send_message(cid, "Received a token: "+text)
        vk_token = text
    elif link_match:
        bot.send_message(cid, "Received a token: "+link_match.group(1))
        vk_token = link_match.group(1)
    else:
        bot.send_message(cid, "Wrong token, try again.")

    # Create new session if successfully received a token
    if vk_token:
        VkSession(cid, vk_token)
        vk_api = vk_sessions[cid].get_vk_api()
        user = vk_api.account.getProfileInfo()
        str = 'Authorized: '+user['first_name']+' '+user['last_name']
        bot.send_message(cid, str)


@bot.message_handler(commands=['start', 'help'])
def start(m):
    bot.reply_to(m, "I'm a bot!")


@bot.message_handler(commands=['hello'])
def hello(m):
    bot.send_message(m.chat.id, f"Hello, {m.from_user.first_name}")


bot.enable_save_next_step_handlers(delay=0)
bot.load_next_step_handlers()

bot.polling()
