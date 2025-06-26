"""app.py"""
import html

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters, ContextTypes
import logging

from const import DbType
from credentials import BOT_TOKEN, BOT_USERNAME
from updater import update_monologues_by_page
from search import search_monologue
import re

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def welcome(update: Update, callback: CallbackContext):
    await update.effective_chat.send_message("Benvenuto artista!")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Comando sconosciuto")


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    res = update_monologues_by_page(DbType.MALE)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sto aggiornando i monologhi, torna più tardi")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # creating string
    search_string = ""
    for elem in context.args:
        search_string = search_string + elem

    res = search_monologue(DbType.MALE, search_string)
    if len(res):
        text = f"<b>Trovato {len(res)} monologhi:</b>\n"
        for elem in res:
            text = text + "<b>Nome:</b> " + elem["text"] + "\n"
            text = text + "<b>Url:</b> <a href=\"" + elem["url"] + "\">" + elem["url"] + "</a>\n"
    else:
        text = "Mmm sembra che non ci sia nulla"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML)

if __name__ == '__main__':
    # when we run the script we want to first create the bot from the token:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    ### BOT COMMANDS
    # - START - welcome message
    application.add_handler(CommandHandler('start', welcome))
    # - UPDATE - update monologues
    application.add_handler(CommandHandler("update", update))
    # - SEARCH - search monologue by content
    application.add_handler(CommandHandler("search", search))
    # on non command i.e message - error
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, error))

    # and send the bot on its way!
    print(f"Your bot is listening! Navigate to http://t.me/{BOT_USERNAME} to interact with it!")
    application.run_polling()

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
