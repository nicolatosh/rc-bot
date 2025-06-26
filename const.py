from enum import Enum


class DbType(Enum):
    FEMALE = "female_monologues"
    MALE = "male_monologues"


URL_BY_TYPE = {
    "FEMALE": "https://www.recitazionecinematografica.com/category/monologhi-femminili",
    "MALE": "https://www.recitazionecinematografica.com/category/monologhi-maschili"
}
