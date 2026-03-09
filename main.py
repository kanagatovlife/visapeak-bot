import os
import json
import requests
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

INSTANCE_ID = "7103539882"
INSTANCE_TOKEN = "7cc1851a27074212af6f990353419a00530a891c50b141749a"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GREEN_API_URL = "https://7103.api.greenapi.com"

client = OpenAI(api_key=OPENAI_API_KEY)
conversations = {}

SYSTEM_PROMPT = (
    "You are a polite assistant of visa agency VisaPeak.kz in Almaty Kazakhstan. "
    "Always respond in Russian language. Be friendly and professional.\n\n"
    "Your tasks:\n"
    "1. Answer questions about visas (USA, Schengen, UK, Japan, Canada, UAE)\n"
    "2. Learn the client name\n"
    "3. Learn which country visa they need\n"
    "4. Learn their phone number\n"
    "5. When you have all info - say that manager will contact them soon\n\n"
    "Pricing info:\n"
    "- Standard package: help with documents\n"
    "- Money-back guarantee package: if rejected we return money\n"
    "- Installment payment via Kaspi, Halyk, Freedom Bank\n\n"
    "Manager contact: +7 707 111 11 65\n"
    "If you dont know exact answer - say you will check with manager."
)


def send_message(chat_id, message):
    url = "{}/waInstance{}/sendMessage/{}".format(GREEN_API_URL, INSTANCE_ID, INSTANCE_TOKEN)
    payload = {"chatId": chat_id, "message": message}
    resp = requests.post(url, json=payload, timeout=10)
    return resp.json()


def get_gpt_response(user_id, user_message):
    if user_id not in conversations:
        conversations[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    conversations[user_id].append({"role": "user", "content": user_message})
    if len(conversations[user_id]) > 21:
        conversations[user_id] = [conversations[user_id][0]] + conversations[user_id][-20:]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversations[user_id],
        max_tokens=500
    )
    reply = response.choices[0].message.content
    conversations[user_id].append({"role": "assistant", "content": reply})
    return reply


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"status": "no data"}), 200
        if data.get("typeWebhook") != "incomingMessageReceived":
            return jsonify({"status": "ignored"}), 200
        message_data = data.get("messageData", {})
        if message_data.get("typeMessage") != "textMessage":
            return jsonify({"status": "not text"}), 200
        chat_id = data.get("senderData", {}).get("chatId", "")
        text = message_data.get("textMessageData", {}).get("textMessage", "")
        if not chat_id or not text:
            return jsonify({"status": "missing data"}), 200
        reply = get_gpt_response(chat_id, text)
        send_message(chat_id, reply)
        return jsonify({"status": "ok"}), 200
    except Exception:
        return jsonify({"status": "error"}), 500


@app.route("/", methods=["GET"])
def home():
    return "VisaPeak Bot is running!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask, request, jsonify
import requests
from openai import OpenAI
import os

app = Flask(__name__)

INSTANCE_ID = "7103539882"
INSTANCE_TOKEN = "7cc1851a27074212af6f990353419a00530a891c50b141749a"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GREEN_API_URL = "https://7103.api.greenapi.com"

client = OpenAI(api_key=OPENAI_API_KEY)

conversations = {}

SYSTEM_PROMPT = (
    "Ty - vezhlivyy i professionalnyy pomoshchnik vizovogo agentstva VisaPeak.kz (Almaty, Kazakhstan). "
    "Otvechay na russkom yazyke. Bud druzhelyubnym i professionalnym.\n\n"
    "Tvoya zadacha:\n"
    "1. Otvechat na voprosy o vizah (SShA, Shengen, Velikobritaniya, Yaponiya, Kanada, OAE i drugie strany)\n"
    "2. Uznat imya klienta\n"
    "3. Uznat v kakuyu stranu nuzhna viza\n"
    "4. Uznat nomer telefona dlya svyazi\n"
    "5. Kogda sobral vse dannye - soobshchit chto menedzher svyazhetsya v blizhayshee vremya\n\n"
    "Informaciya o cenah:\n"
    "- Standartnyy paket: pomoshch v oformlenii dokumentov\n"
    "- Paket s garantiey vozvrata deneg: esli otkazhuyt - vozvrashchaem dengi\n"
    "- Dostupna oplata v rassrochku cherez Kaspi, Halyk, Freedom Bank\n\n"
    "Kontakt menedzhera: +7 707 111 11 65\n\n"
    "Esli ne znaesh tochnyy otvet - skazhi chto utochnish u menedzhera."
)


def send_message(chat_id, message):
    url = "{}/waInstance{}/sendMessage/{}".format(GREEN_API_URL, INSTANCE_ID, INSTANCE_TOKEN)
    payload = {"chatId": chat_id, "message": message}
    response = requests.post(url, json=payload)
    return response.json()


def get_gpt_response(user_id, user_message):
    if user_id not in conversations:
        conversations[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    conversations[user_id].append({"role": "user", "content": user_message})

    if len(conversations[user_id]) > 21:
        conversations[user_id] = [conversations[user_id][0]] + conversations[user_id][-20:]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversations[user_id],
        max_tokens=500
    )

    assistant_message = response.choices[0].message.content
    conversations[user_id].append({"role": "assistant", "content": assistant_message})
    return assistant_message


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "no data"}), 200
        if data.get("typeWebhook") != "incomingMessageReceived":
            return jsonify({"status": "ignored"}), 200
        message_data = data.get("messageData", {})
        if message_data.get("typeMessage") != "textMessage":
            return jsonify({"status": "not text"}), 200
        chat_id = data.get("senderData", {}).get("chatId")
        text = message_data.get("textMessageData", {}).get("textMessage", "")
        if not chat_id or not text:
            return jsonify({"status": "missing data"}), 200
        reply = get_gpt_response(chat_id, text)
        send_message(chat_id, reply)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error"}), 500


@app.route("/", methods=["GET"])
def home():
    return "VisaPeak Bot is running!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
