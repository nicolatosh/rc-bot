"""app3.py"""
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from const import DbType
from credentials import BOT_TOKEN
from updater import update_monologues_by_page
from search import search_monologue
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters, ContextTypes,
    Updater
)

# States for the BOT state machine
START_ROUTES, END_ROUTES = range(2)
MENU, MALE_MONOLOGUES, FEMALE_MONOLOGUES, CONTINUE, END = range(5)

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


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


def main():
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(10)
        .write_timeout(10)
        .concurrent_updates(True)
        .build()
    )

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
    updater = Updater()
    updater.start_webhook(listen="0.0.0.0",
                          port=int(os.environ.get('PORT', 5000)),
                          url_path=telegram_bot_token,
                          webhook_url=+ telegram_bot_token
                          )


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    res = update_monologues_by_page(DbType.MALE)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sto aggiornando i monologhi, torna più tardi")


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
    main()

