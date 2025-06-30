from enum import Enum


class DbType(Enum):
    FEMALE = "female_monologues"
    MALE = "male_monologues"


URL_BY_TYPE = {
    "female_monologues": "https://www.recitazionecinematografica.com/category/monologhi-femminili",
    "male_monologues": "https://www.recitazionecinematografica.com/category/monologhi-maschili"
}
