import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.constants import ParseMode
from const import DbType, MALE_MONOLOGUES, FEMALE_MONOLOGUES, MENU, CONTINUE, END
from env import BOT_TOKEN
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
        f"Benvenuto {update.effective_user.first_name}! Quale tipologia di monologhi vuoi cercare?", reply_markup=reply_markup
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

    found_monologues = set()
    for elem in search_str:
        res = search_monologue(db_type, elem)
        found_monologues.update(res)

    result_size = len(found_monologues)
    if result_size:
        if result_size > 1:
            text = f"<b>Trovato {result_size} monologhi:</b>\n"
        else:
            text = "<b>Trovato un solo monologo</b>\n"
        for monologue in found_monologues:
            text = text + "<b>Nome:</b> " + monologue.text + "\n"
            text = text + "<b>Url:</b> <a href=\"" + monologue.url + "\">" + monologue.url + "</a>\n"
    else:
        text = "Mmm sembra che non ci sia nulla"
    return text


if __name__ == "__main__":
    main()
