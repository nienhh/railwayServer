import os
import json
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# 初始化 LINE Bot
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
line_bot_api = MessagingApi(
    channel_access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)

BOOKING_JSON_PATH = "flex_booking.json"
BOOKED_TIMES = set()


def load_flex():
    with open(BOOKING_JSON_PATH, "r", encoding="utf-8") as f:
        flex = json.load(f)
    # 將已預約的時段移除
    for bubble in flex["contents"]:
        buttons = bubble["body"]["contents"][3]["contents"]
        bubble["body"]["contents"][3]["contents"] = [
            btn for btn in buttons if btn["action"]["text"] not in BOOKED_TIMES
        ]
    return flex


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"LINE Webhook 處理失敗：{e}")
        abort(400)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    msg = event.message.text.strip()
    user_id = event.source.user_id

    # 若使用者傳來 預約體驗 或 預約時段
    if msg in ["預約體驗", "預約時段"]:
        flex = load_flex()
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    FlexMessage(alt_text="請選擇體驗時段", contents=flex)
                ]
            )
        )

    # 若使用者點選了預約時段的文字
    elif msg.startswith("我想預約"):
        BOOKED_TIMES.add(msg)
        print(f"{user_id} 預約了：{msg}")
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"✅ 預約成功：{msg}")]
            )
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
