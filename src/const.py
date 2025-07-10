from enum import Enum


class DbType(Enum):
    FEMALE = "female_monologues"
    MALE = "male_monologues"


URL_BY_TYPE = {
    "female_monologues": "https://www.recitazionecinematografica.com/category/monologhi-femminili",
    "male_monologues": "https://www.recitazionecinematografica.com/category/monologhi-maschili"
}

# States for the BOT state machine
START_ROUTES, END_ROUTES = range(2)
MENU, MALE_MONOLOGUES, FEMALE_MONOLOGUES, CONTINUE, END = range(5)
