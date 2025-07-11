import datetime
import html
import json
import logging
import traceback
from time import sleep
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.constants import ParseMode
from const import DbType, MALE_MONOLOGUES, FEMALE_MONOLOGUES, MENU, CONTINUE, END
from env import BOT_TOKEN, DEVELOPER_CHAT_ID
from updater import update_monologues
from search import search_monologue
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters, ContextTypes
)
from commands import promote
from conversation import ConversationText, ConversationType

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("httpx")


# Loading conversations
conversation = ConversationText()


async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Maschili", callback_data=str(MALE_MONOLOGUES))],
        [InlineKeyboardButton("Femminili", callback_data=str(FEMALE_MONOLOGUES))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(conversation.type(ConversationType.WELCOME).random().get(), reply_markup=reply_markup
    )
    return MENU


async def menu_handler(update: Update, context: CallbackContext) -> int:
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
        await query.edit_message_text(text=conversation.type(ConversationType.CONTINUE_NO).random().get())
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
    await query.edit_message_text(conversation.type(ConversationType.CONTINUE_YES).random().get(), reply_markup=reply_markup
    )
    return MENU

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )

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
        entry_points=[CommandHandler("start", start),
                      CommandHandler("update", update),
                      CommandHandler("promote", promote)],
        states={
            MENU: [CallbackQueryHandler(menu_handler)],
            MALE_MONOLOGUES: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_male)],
            FEMALE_MONOLOGUES: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_female)],
            CONTINUE: [CallbackQueryHandler(start_over)],
            END: [CallbackQueryHandler(menu_handler)]
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Manually triggers update of monologues.
    Calls the task "update_monologues".
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Get the chat member status of the user
    member = await context.bot.get_chat_member(chat_id, user_id)

    # Check if user is admin or creator
    if member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:

        await context.bot.send_message(chat_id=update.effective_chat.id, text="Sto aggiornando i monologhi, torna più tardi")
        update_monologues.delay(DbType.MALE)
        update_monologues.apply_async(countdown=3600)

    else:
        await update.message.reply_text("Comando riservato per utenti amministratori")


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
    await update.message.reply_text(conversation.type(ConversationType.CONTINUE_QUESTION).random().get(), reply_markup=reply_markup)
    return MENU


async def search_female(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key_list = [sub for sub in update.message.text.split()]
    text = search(search_str=key_list, db_type=DbType.FEMALE)
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


def search(search_str: list[str], db_type: DbType) -> Optional[str]:

    found_monologues = set()
    for elem in search_str:
        res = search_monologue(db_type, elem)
        found_monologues.update(res)

    result_size = len(found_monologues)

    # Prevent returning too many elements
    # Telegram API has a limit of 4096 in message size
    # User may have searched a two letter string like "ab"
    text = ""
    if result_size:
        if result_size == 0:
            text = "Mmm sembra che non ci sia nulla"
        elif result_size == 1:
            monologue = found_monologues.pop()
            text = "<b>Trovato un solo monologo</b>\n"
            text = text + "<b>Nome:</b> " + monologue.text + "\n"
            text = text + "<b>Url:</b> <a href=\"" + monologue.url + "\">" + monologue.url + "</a>\n"
        else:
            # Limiting answers
            if result_size > 10:
                limited_response = [found_monologues.pop() for _ in range(10)]
                found_monologues = limited_response

                full_search_string = ""
                for elem in search_str:
                    full_search_string += f"{elem} "

                if len(full_search_string) <= 3:
                    text = "<i>Attenzione: la tua chiave di ricerca è corta.\nAlcuni risultati potrebbero essere troncati.</i>\n"

            text = text + f"<b>Trovati {result_size} monologhi:</b>\n"
            for monologue in found_monologues:
                text = text + "<b>Nome:</b> " + monologue.text + "\n"
                text = text + "<b>Url:</b> <a href=\"" + monologue.url + "\">" + monologue.url + "</a>\n"
    else:
        text = "Mmm sembra che non ci sia nulla"
    return text


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            logger.error(e)
            with open("../logs.txt", "a") as f:
                f.write(str(datetime.datetime.now()) + " " + str(e))
            logger.info("Exception - restarting bot in 5 seconds...")
            sleep(5)
