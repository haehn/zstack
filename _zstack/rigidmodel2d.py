from transform import Transform

class RigidModel2D(Transform):

  def __init__(self, dataString):

    super(RigidModel2D,self).__init__(dataString)

  @property
  def r(self):
    return self._data[0]

  @property
  def x(self):
    return self._data[1]

  @property
  def y(self):
    return self._data[2]

