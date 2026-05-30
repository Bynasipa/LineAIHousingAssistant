import os
import random
import logging
import traceback

print("🔥 THIS IS THE ACTIVE FILE")

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request

from linebot.v3.webhook import WebhookParser

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest,
    ImageMessage,
    FlexMessage,
    FlexContainer
)

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    PostbackEvent
)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- APP ----------------
app = Flask(__name__)

# ---------------- ENV ----------------
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# ---------------- STATE ----------------
user_state = {}

def get_user(user_id):
    if user_id not in user_state:
        user_state[user_id] = {}
    return user_state[user_id]

# ---------------- CALLBACK ----------------

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature")

    print("🔥 CALLBACK HIT")

    try:
        events = parser.parse(body, signature)

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            for event in events:

                print("EVENT TYPE:", type(event))

                if isinstance(event, MessageEvent):
                    handle_message(line_bot_api, event)

                elif isinstance(event, FollowEvent):
                    handle_follow(line_bot_api, event)

                elif isinstance(event, PostbackEvent):
                    print("POSTBACK:", event.postback.data)
                    handle_postback(line_bot_api, event)

    except Exception as e:
        print("ERROR:", e)
        print(traceback.format_exc())

    return "OK"

# ---------------- MESSAGE ----------------
def handle_message(line_bot_api, event):
    text = event.message.text.lower().strip()

    print("EVENT WORKS:", text)

    if text == "start":
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="Bot started ✅")]
            )
        )
        return

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="Hello from bot 👋")]
        )
    )

# ---------------- FOLLOW ----------------
def handle_follow(line_bot_api, event):
    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="👋 Thanks for adding me!")]
        )
    )

# ---------------- POSTBACK (ИСПРАВЛЕНО) ----------------
def handle_postback(line_bot_api, event):

    data = event.postback.data
    user_id = event.source.user_id
    user = get_user(user_id)

    print("POSTBACK:", data)

    # -------- ASSISTANT --------
    if data.startswith("assistant_"):

        user["assistant_type"] = data.split("_")[1]

        flex = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "🏙 Step 1: Choose city"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "action": {"type": "postback", "label": "🏙 Austin", "data": "city_austin"}}
                ]
            }
        }

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[FlexMessage(alt_text="City", contents=FlexContainer.from_dict(flex))]
            )
        )
        return

    # -------- CITY --------
    if data.startswith("city_"):

        flex = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [{"type": "text", "text": "📍 Step 2: Choose area"}]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "action": {"type": "postback", "label": "📍 Downtown", "data": "area_downtown"}}
                ]
            }
        }

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[FlexMessage(alt_text="Area", contents=FlexContainer.from_dict(flex))]
            )
        )
        return

    # -------- AREA --------
    if data.startswith("area_"):

        flex = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [{"type": "text", "text": "💳 Step 3: Payment method"}]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "button", "action": {"type": "postback", "label": "🏦 Mortgage", "data": "payment_mortgage"}}
                ]
            }
        }

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[FlexMessage(alt_text="Payment", contents=FlexContainer.from_dict(flex))]
            )
        )
        return

    # -------- PAYMENT --------
    if data.startswith("payment_"):

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="🏙 I found 3 apartments in Downtown Austin")]
            )
        )

        return

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))