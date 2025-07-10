async def resolve_user(context, chat_id, username_or_id):
    if username_or_id.startswith("@"):
        try:
            member = await context.bot.get_chat_member(chat_id, username_or_id)
            return member.user.id
        except Exception as e:
            return None
    else:
        try:
            return int(username_or_id)
        except:
            return None
