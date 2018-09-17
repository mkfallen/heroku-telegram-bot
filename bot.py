# -*- coding: utf-8 -*-
import logging
import os
import re
import requests
import vk_api as vk
import telebot as tg

tg_token = os.environ['TELEGRAM_TOKEN']
proxy = os.environ['PROXY_LINK']
app_id = os.environ['VK_CLIENT_ID']
sessions = dict()

if proxy:
    tg.apihelper.proxy = {'https': proxy}

bot = tg.TeleBot(tg_token)
tg.logger.setLevel(logging.DEBUG)


def get_user_input(chat_id, text):
    bot.send_message(chat_id, text)

    updates = bot.get_updates(timeout=20)
    return updates


@bot.message_handler(commands=['auth'])
def auth(m):
    if m.chat.id in sessions:
        vk_api = get_vk_api(m.chat.id, sessions[m.chat.id])
        user = vk_api.account.getProfileInfo()
        str = 'Already authorized: '+user['first_name']+' '+user['last_name']
        bot.send_message(m.chat.id, str)
        return

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

    r = bot.send_message(m.chat.id, str)
    bot.register_next_step_handler(r, get_vk_token)


def get_vk_token(m):
    vk_token = None
    text = m.text
    token_match = re.match(r"^\w{85}$", text)
    link_match = re.search(r"^https?://.*access_token=(\w{85}).*$", text)
    if token_match:
        bot.send_message(m.chat.id, "Received a token: "+text)
        vk_token = text
    elif link_match:
        bot.send_message(m.chat.id, "Received a token: "+link_match.group(1))
        vk_token = link_match.group(1)
    else:
        bot.send_message(m.chat.id, "Wrong token.")

    if vk_token:
        vk_api = get_vk_api(m.chat.id, vk_token)
        user = vk_api.account.getProfileInfo()
        str = 'Authorized: '+user['first_name']+' '+user['last_name']
        bot.send_message(m.chat.id, str)


def get_vk_api(cid, vk_token):
    session = vk.VkApi(token=vk_token, app_id=app_id)
    vk_api = session.get_api()
    try:
        sessions[cid] = vk_token
        return vk_api
    except vk.ApiError as e:
        bot.send_message(cid, e)
        print(e)


@bot.message_handler(commands=['start', 'help'])
def start(m):
    bot.reply_to(m, "I'm a bot!")


@bot.message_handler(commands=['hello'])
def hello(m):
    bot.send_message(m.chat.id, f"Hello, {m.from_user.first_name}")


# bot.enable_save_next_step_handlers(delay=0)
# bot.load_next_step_handlers()

bot.polling()
