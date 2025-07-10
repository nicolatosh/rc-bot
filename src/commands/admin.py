from telegram import Update
from telegram.ext import ContextTypes

from const import MENU
from roles import is_creator, set_role, is_admin_or_creator, user_roles, save_roles, get_role
from utils.helper import resolve_user


async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    actor_id = update.effective_user.id
    if not is_creator(actor_id):
        await update.message.reply_text("Only the creator can promote.")
        return MENU

    if not context.args:
        await update.message.reply_text("Usage: /promote @username or user_id")
        return MENU

    target_id = await resolve_user(context, update.effective_chat.id, context.args[0])
    if not target_id:
        await update.message.reply_text("Couldn't find user.")
        return MENU

    set_role(target_id, "admin")
    await update.message.reply_text(f"User {target_id} promoted to admin.")
    return MENU

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    actor_id = update.effective_user.id
    if not is_admin_or_creator(actor_id):
        await update.message.reply_text("Only admins can ban users.")
        return MENU

    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return MENU

    target_id = context.args[0]
    user_roles[target_id] = "banned"
    save_roles(user_roles)
    await update.message.reply_text(f"User {target_id} is now banned.")
    return MENU

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    actor_id = update.effective_user.id
    if not is_admin_or_creator(actor_id):
        await update.message.reply_text("Only admins can unban users.")
        return MENU

    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return MENU

    target_id = context.args[0]
    user_roles[target_id] = "user"
    save_roles(user_roles)
    await update.message.reply_text(f"User {target_id} is now unbanned.")
    return MENU

async def admin_feature(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_role(user_id)
    if role == "banned":
        await update.message.reply_text("You are banned.")
        return MENU
    elif role not in ["admin", "creator"]:
        await update.message.reply_text("Admins only.")
        return MENU
    await update.message.reply_text("Admin feature accessed!")
    return MENU

