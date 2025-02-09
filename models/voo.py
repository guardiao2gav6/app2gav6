class Voo:
  def __init__(self, tripulantes=[],
               descidas=[],
               **kwargs):
    self.tripulantes = tripulantes
    self.descidas = descidas

    for key, value in kwargs.items():
      setattr(self, key, value)

