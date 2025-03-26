from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
from dotenv import load_dotenv
import os
import json

app = Flask(__name__)
load_dotenv()

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = MessagingApi(channel_access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()
    if "我想預約" in user_text:
        user_id = event.source.user_id
        reserve_time = user_text.replace("我想預約", "").strip()

        # 儲存預約紀錄
        with open("bookings.json", "r", encoding="utf-8") as f:
            bookings = json.load(f)

        if reserve_time not in bookings:
            bookings[reserve_time] = []

        if user_id not in bookings[reserve_time]:
            bookings[reserve_time].append(user_id)

        with open("bookings.json", "w", encoding="utf-8") as f:
            json.dump(bookings, f, ensure_ascii=False, indent=2)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"預約成功：{reserve_time}")]
            )
        )
    elif "預約體驗" in user_text:
        # 回傳過濾掉已預約時間的 Flex Message
        with open("flex_booking.json", "r", encoding="utf-8") as f:
            flex_data = json.load(f)

        with open("bookings.json", "r", encoding="utf-8") as f:
            bookings = json.load(f)

        for bubble in flex_data["contents"]:
            btns = bubble["body"]["contents"][3]["contents"]
            bubble["body"]["contents"][3]["contents"] = [
                b for b in btns if b["action"]["text"].replace("我想預約", "").strip() not in bookings
            ]

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[{
                    "type": "flex",
                    "altText": "預約體驗",
                    "contents": flex_data
                }]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)