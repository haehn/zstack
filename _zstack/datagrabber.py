import os
import glob
import pyopencl as cl
from jsonloader import JSONLoader
from powertrain import Powertrain

class DataGrabber:

  def __init__(self):

    self._sections = None

  def run(self, input_dir):

    downsampler = Powertrain(True)
    downsampler.program = """
    const sampler_t sampler = CLK_NORMALIZED_COORDS_TRUE | 
      CLK_FILTER_LINEAR | CLK_ADDRESS_CLAMP_TO_EDGE;

    __kernel void downsample(__read_only image2d_t sourceImage, __write_only image2d_t targetImage)
    {

      int w = get_image_width(targetImage);
      int h = get_image_height(targetImage);

      int outX = get_global_id(0);
      int outY = get_global_id(1);
      int2 posOut = {outX, outY};

      float inX = outX / (float) w;
      float inY = outY / (float) h;
      float2 posIn = {inX, inY};

      float4 pixel = read_imagef(sourceImage, sampler, posIn);
      write_imagef(targetImage, posOut, pixel);

    }
    """


    #
    # we are looking for JSON files in the input directory
    #
    json_files = glob.glob(os.path.join(input_dir, '*.json'))

    sections = {}

    for f in json_files:

      section = os.path.basename(f)

      loader = JSONLoader(f)
      loaded_section = loader.load()
      loaded_section._downsampler = downsampler

      sections[section] = loaded_section

      print 'Found section ' + section + ' with ' + str(len(loaded_section._tiles)) + ' tiles.'




    # load data 
    for s in sections:
      sections[s].load(input_dir)

    # create mipmap
    for s in sections:
      sections[s].createMipMap(downsampler)

    self._sections = sections

    # print sections["0"]
    # tile = self.getSection(0,5)
    # print tile.shape


  def getSection(self, id, zoomlevel):
    '''
    '''
    # stitch
    tile = self._sections[self._sections.keys()[id]]._tiles[0]._mipmap.get(zoomlevel)

    return tile
    