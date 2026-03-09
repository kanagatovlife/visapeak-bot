from flask import Flask, request, jsonify
import requests
from openai import OpenAI
import os

app = Flask(__name__)

# Configuration
INSTANCE_ID = "7103539882"
INSTANCE_TOKEN = "7cc1851a27074212af6f990353419a00530a891c50b141749a"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GREEN_API_URL = f"https://7103.api.greenapi.com"

client = OpenAI(api_key=OPENAI_API_KEY)

# Store conversation history per user
conversations = {}

SYSTEM_PROMPT = """Ты — вежливый и профессиональный помощник визового агентства VisaPeak.kz (Алматы, Казахстан).

Твоя задача:
1. Отвечать на вопросы о визах (США, Шенген, Великобритания, Япония, Канада, ОАЭ и другие страны)
2. Узнать имя клиента
3. Узнать в какую страну нужна виза
4. Узнать номер телефона для связи
5. Когда собрал все данные — сообщить что менеджер свяжется в ближайшее время

Информация о ценах:
- Стандартный пакет: помощь в оформлении документов
- Пакет с гарантией возврата денег: если откажут — возвращаем деньги
- Доступна оплата в рассрочку через Kaspi, Halyk, Freedom Bank

Контакт менеджера: +7 707 111 11 65

Отвечай на русском языке. Будь дружелюбным и профессиональным.
Если не знаешь точный ответ — скажи что уточнишь у менеджера."""


def send_message(chat_id, message):
    url = f"{GREEN_API_URL}/waInstance{INSTANCE_ID}/sendMessage/{INSTANCE_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": message
    }
    response = requests.post(url, json=payload)
    return response.json()


def get_gpt_response(user_id, user_message):
    if user_id not in conversations:
        conversations[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    conversations[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    # Keep last 20 messages to avoid token limit
    if len(conversations[user_id]) > 21:
        conversations[user_id] = [conversations[user_id][0]] + conversations[user_id][-20:]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversations[user_id],
        max_tokens=500
    )
    
    assistant_message = response.choices[0].message.content
    conversations[user_id].append({
        "role": "assistant",
        "content": assistant_message
    })
    
    return assistant_message


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        
        if not data:
            return jsonify({"status": "no data"}), 200
        
        # Only process incoming messages
        if data.get("typeWebhook") != "incomingMessageReceived":
            return jsonify({"status": "ignored"}), 200
        
        message_data = data.get("messageData", {})
        msg_type = message_data.get("typeMessage")
        
        # Only handle text messages
        if msg_type != "textMessage":
            return jsonify({"status": "not text"}), 200
        
        chat_id = data.get("senderData", {}).get("chatId")
        text = message_data.get("textMessageData", {}).get("textMessage", "")
        
        if not chat_id or not text:
            return jsonify({"status": "missing data"}), 200
        
        # Get GPT response
        reply = get_gpt_response(chat_id, text)
        
        # Send reply
        send_message(chat_id, reply)
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    return "VisaPeak Bot is running! 🚀"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
