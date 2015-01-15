from transform import Transform

class TranslationModel2D(Transform):

  def __init__(self, dataString):

    super(TranslationModel2D,self).__init__(dataString)

  @property
  def x(self):
    return self._data[0]

  @property
  def y(self):
    return self._data[1]

