import cv2
import os

class Tile:
  '''
  '''

  def __init__(self):
    '''
    '''
    self._bbox = None
    self._height = -1
    self._width = -1
    self._layer = -1
    self._maxIntensity = -1
    self._minIntensity = -1
    self._mipmapLevels = None
    self._transforms = None

  def __str__(self):

    return 'Tile, Layer ' + str(self._layer)


  def load(self, prefix):
    '''
    Loads image data from disk.
    '''
    # for l in self._mipmapLevels:

    image = cv2.imread(os.path.join(prefix,self._mipmapLevels["0"]['imageUrl']), cv2.CV_LOAD_IMAGE_GRAYSCALE)

    self._mipmapLevels["0"]['image'] = image


  @staticmethod
  def fromJSON(json):

    new_tile = Tile()
    new_tile._bbox = json['bbox']
    new_tile._height = json['height']
    new_tile._width = json['width']
    new_tile._layer = json['layer']
    new_tile._minIntensity = json['minIntensity']
    new_tile._maxIntensity = json['maxIntensity']
    new_tile._mipmapLevels = json['mipmapLevels']
    new_tile._transforms = json['transforms']

    return new_tile
