import os
if os.path.exists(".env"):
    # if we see the .env file, load it
    from dotenv import load_dotenv
    load_dotenv()

BLOG_BASE_URL = "https://www.recitazionecinematografica.com/"
FEMALE_MONOLOGUES = "https://www.recitazionecinematografica.com/category/monologhi-femminili"
MALE_MONOLOGUES = "https://www.recitazionecinematografica.com/category/monologhi-maschili"
TELEGRAM_URL = "https://api.telegram.org/bot{token}".format(token=os.getenv('BOT_TOKEN'))
WEBHOOK_URL = "https://telegram-bot.vercel.app/rc-bot"