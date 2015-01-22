from tile import Tile

class Section:

  def __init__(self):

    '''
    '''
    self._id = -1
    self._tiles = None
    self._downsampler = None
    self._zoomlevels = None

  def __str__(self):
    '''
    '''
    print 'Section ' + str(self._id)

  def load(self, prefix):
    '''
    '''
    for t in self._tiles:
      t.load(prefix)

  def createMipMap(self, downsampler):
    '''
    '''
    for t in self._tiles:
      # print 'new_tile'
      t._mipmap.create(downsampler)

  @staticmethod
  def fromJSON(json):
    '''
    '''

    new_section = Section()
    loaded_tiles = []

    for t in json:
      new_tile = Tile.fromJSON(t)
      new_tile._section = new_section
      loaded_tiles.append(new_tile)

    new_section._tiles = loaded_tiles

    return new_section

