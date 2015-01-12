from tile import Tile

class Section:

  def __init__(self):

    '''
    '''
    self._id = -1
    self._tiles = None

  def __str__(self):
    '''
    '''
    print 'Section ' + str(self._id)

  def load(self, prefix):
    '''
    '''
    for t in self._tiles:
      t.load(prefix)

  @staticmethod
  def fromJSON(json):
    '''
    '''

    new_section = Section()
    loaded_tiles = []

    for t in json:
      loaded_tiles.append(Tile.fromJSON(t))

    new_section._tiles = loaded_tiles

    return new_section

