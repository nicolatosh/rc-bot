from __future__ import annotations

class Monologue:

    text: str = ""
    url: str = ""

    def __init__(self, text, url):
        self.text = text
        self.url = url

    @classmethod
    def from_dict(cls, monologue: dict) -> Monologue:
        return Monologue(monologue['text'], monologue['url'])

    def to_dict(self) -> dict:
        return {"text": self.text, "url": self.url}

    def __eq__(self, __value):
        return __value.text == self.text and __value.url == self.url

    def __repr__(self):
        return "Item(%s, %s)" % (self.text, self.url)

    def __hash__(self):
        return hash(self.__repr__())