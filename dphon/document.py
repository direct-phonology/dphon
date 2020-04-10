"""A document is the basic unit of text comparison."""

class Document:
    """Basic documents store their text prior to indexing."""

    _id: int
    text: str

    def __init__(self, _id: int, text: str):
        self._id = _id
        self.text = text

    def __repr__(self) -> str:
        return f"<Document id: {self._id}>"

    def __str__(self) -> str:
        return self.text

    @property
    def id(self) -> int:
        return self._id
