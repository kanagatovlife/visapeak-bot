import os
import traceback
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
    "Always respond in Russian language. Be friendly and professional. "
    "Your tasks: ask client name, which country visa they need, their phone number. "
    "When you have all info say manager will contact them soon. "
    "Manager contact: +7 707 111 11 65"
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
        print("Received:", data)
        if not data:
            return jsonify({"status": "no data"}), 200
        if data.get("typeWebhook") != "incomingMessageReceived":
            return jsonify({"status": "ignored"}), 200
        message_data = data.get("messageData", {})
        if message_data.get("typeMessage") != "textMessage":
            return jsonify({"status": "not text"}), 200
        chat_id = data.get("senderData", {}).get("chatId", "")
        text = message_data.get("textMessageData", {}).get("textMessage", "")
        print("chat_id:", chat_id, "text:", text)
        if not chat_id or not text:
            return jsonify({"status": "missing data"}), 200
        reply = get_gpt_response(chat_id, text)
        print("reply length:", len(reply))
        send_message(chat_id, reply)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("ERROR:", traceback.format_exc())
        return jsonify({"status": "error", "msg": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "VisaPeak Bot is running!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
