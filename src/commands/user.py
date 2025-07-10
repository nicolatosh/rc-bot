from telegram import Update
from telegram.ext import ContextTypes

from roles import user_roles


# Helpers
def get_role(user_id):
    return user_roles.get(str(user_id), "user")

def is_creator(user_id):
    return get_role(user_id) == "creator"

def is_admin_or_creator(user_id):
    return get_role(user_id) in ["admin", "creator"]

async def myrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    role = get_role(user_id)
    await update.message.reply_text(f"Your role is: {role}")


