#!/usr/bin/env python
# This program is dedicated to the public domain under the CC0 license.
# pylint: disable=import-error,unused-argument
"""
Simple example of a bot that uses a custom webhook setup and handles custom updates.
For the custom webhook setup, the libraries `flask`, `asgiref` and `uvicorn` are used. Please
install them as `pip install flask[async]~=2.3.2 uvicorn~=0.23.2 asgiref~=3.7.2`.
Note that any other `asyncio` based web server framework can be used for a custom webhook setup
just as well.

Usage:
Set bot Token, URL, admin CHAT_ID and PORT after the imports.
You may also need to change the `listen` value in the uvicorn configuration to match your setup.
Press Ctrl-C on the command line or send a signal to the process to stop the bot.
"""
import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import Optional
import uvicorn
from asgiref.wsgi import WsgiToAsgi

from flask import Flask, Response, abort, make_response, request

from const import DbType
from links import WEBHOOK_URL

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters, ContextTypes,
    ExtBot,
    TypeHandler
)

from search import search_monologue

# States for the BOT state machine
START_ROUTES, END_ROUTES = range(2)
MENU, MALE_MONOLOGUES, FEMALE_MONOLOGUES, CONTINUE, END = range(5)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
app = Flask(__name__)



# Define configuration constants
ADMIN_CHAT_ID = 123456
from credentials import BOT_TOKEN, BOT_USERNAME, PORT

@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""

    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    """
    Custom CallbackContext class that makes `user_data` available for updates of type
    `WebhookUpdate`.
    """

    @classmethod
    def from_update(
        cls,
        update: object,
        application: "Application",
    ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


"""Set up PTB application and a web application for handling the incoming requests."""
context_types = ContextTypes(context=CustomContext)
# Here we set updater to None because we want our custom webhook server to handle the updates
# and hence we don't need an Updater instance
application = (
    Application.builder().token(BOT_TOKEN).updater(None).context_types(context_types).build()
)


@app.post("/telegram")  # type: ignore[misc]
async def telegram() -> Response:
    """Handle incoming Telegram updates by putting them into the `update_queue`"""
    await application.update_queue.put(Update.de_json(data=request.json, bot=application.bot))
    return Response(status=HTTPStatus.OK)


@app.route("/submitpayload", methods=["GET", "POST"])  # type: ignore[misc]
async def custom_updates() -> Response:
    """
    Handle incoming webhook updates by also putting them into the `update_queue` if
    the required parameters were passed correctly.
    """
    try:
        user_id = int(request.args["user_id"])
        payload = request.args["payload"]
    except KeyError:
        abort(
            HTTPStatus.BAD_REQUEST,
            "Please pass both `user_id` and `payload` as query parameters.",
        )
    except ValueError:
        abort(HTTPStatus.BAD_REQUEST, "The `user_id` must be a string!")

    await application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
    return Response(status=HTTPStatus.OK)


@app.get("/healthcheck")  # type: ignore[misc]
async def health() -> Response:
    """For the health endpoint, reply with a simple plain text message."""
    response = make_response("The bot is still running fine :)", HTTPStatus.OK)
    response.mimetype = "text/plain"
    return response

async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Maschili", callback_data=str(MALE_MONOLOGUES))],
        [InlineKeyboardButton("Femminili", callback_data=str(FEMALE_MONOLOGUES))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Unofficial RC Bot\n Ciao artista! Quale tipologia di monologhi vuoi cercare?", reply_markup=reply_markup
    )
    return MENU


async def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == str(MALE_MONOLOGUES):
        await query.edit_message_text(text="Bene! inserisci delle parole per la tua ricerca")
        return MALE_MONOLOGUES
    elif query.data == str(FEMALE_MONOLOGUES):
        await query.edit_message_text(text="Bene! cerchiamo monologhi femminili")
        return FEMALE_MONOLOGUES
    elif query.data == str(CONTINUE):
        await start_over(update, context)
    elif query.data == str(END):
        await query.edit_message_text(text=f"Ciao {query.from_user.first_name}, a presto!")
        return ConversationHandler.END
    else:
        await query.edit_message_text(text="Operazione non disponibile")
        return MENU


async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """New search for monologues"""
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("Maschili", callback_data=str(MALE_MONOLOGUES))],
        [InlineKeyboardButton("Femminili", callback_data=str(FEMALE_MONOLOGUES))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Bene! continuiamo la ricerca", reply_markup=reply_markup
    )
    return MENU


async def webhook_update(update: WebhookUpdate, context: CustomContext) -> None:
    """Handle custom updates."""
    chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
    payloads = context.user_data.setdefault("payloads", [])
    payloads.append(update.payload)
    combined_payloads = "</code>\n• <code>".join(payloads)
    text = (
        f"The user {chat_member.user.mention_html()} has sent a new payload. "
        f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode=ParseMode.HTML)

async def main() -> None:

    # ConversationHandler to handle the state machine
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(button)],
            MALE_MONOLOGUES: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_male)],
            FEMALE_MONOLOGUES: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_female)],
            CONTINUE: [CallbackQueryHandler(start_over)],
            END: [CallbackQueryHandler(button)]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.add_handler(TypeHandler(type=WebhookUpdate, callback=webhook_update))

    # Pass webhook settings to telegram
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/telegram", allowed_updates=Update.ALL_TYPES)

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(app),
            port=PORT,
            use_colors=False
        )
    )

    # Run application and webserver together
    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()

async def search_male(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key_list = [sub for sub in update.message.text.split()]
    text = search(search_str=key_list, db_type=DbType.MALE)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML)

    keyboard = [
        [
            InlineKeyboardButton("Continua", callback_data=str(CONTINUE)),
            InlineKeyboardButton("Esci", callback_data=str(END)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Che si fa?", reply_markup=reply_markup)
    return MENU


async def search_female(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key_list = [sub for sub in update.message.text.split()]
    text = search(search_str=key_list, db_type=DbType.FEMALE)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML)

    return MENU


def search(search_str: list[str], db_type: DbType) -> Optional[str]:

    # creating string
    search_string = ""
    for elem in search_str:
        search_string = search_string + elem

    res = search_monologue(db_type, search_string)
    result_size = len(res)
    if result_size:
        if result_size > 1:
            text = f"<b>Trovato {len(res)} monologhi:</b>\n"
        else:
            text = "<b>Trovato un solo monologo</b>\n"
        for elem in res:
            text = text + "<b>Nome:</b> " + elem["text"] + "\n"
            text = text + "<b>Url:</b> <a href=\"" + elem["url"] + "\">" + elem["url"] + "</a>\n"
    else:
        text = "Mmm sembra che non ci sia nulla"
    return text


if __name__ == "__main__":
    asyncio.run(main())
