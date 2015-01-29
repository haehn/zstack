import os
import glob
import numpy as np
import pyopencl as cl
import cv2

from jsonloader import JSONLoader
from powertrain import Powertrain

class DataGrabber:

  def __init__(self):

    self._cache = {}

    self._sections = None

  def run(self, input_dir):

    downsampler = Powertrain(True)
    downsampler.program = """
__kernel void ds(__global const uchar *img_g,
                 const int width,
                 const int height,
                 const int out_width,
                 const int out_height,                 
                 __global uchar *out_g) {
  int gid = get_global_id(0);

  int col = gid % width;
  int row = gid / width;

  if ((col >= width) || (row >= height)) {
    return;
  }  


  if (col < 0) {
    return;
  }

  int new_row = row/2;
  int new_col = col/2;

  if ((new_col >= out_width) || (new_row >= out_height)) {
    return;
  }

  if (new_col < 0) {
    return;
  }  

  int k = new_row*out_width + new_col;

  if (row % 2 == 0 && col % 2 == 0) {

    uchar c = img_g[gid];
    uchar r = img_g[gid+1];
    uchar b = img_g[gid+width];
    uchar b_r = img_g[gid+width+1];

    uchar val = (c + r + b + b_r) / 4;

    //out_g[k] = img_g[gid];
    out_g[k] = val;
  }
}

__kernel void transform(__global const uchar *img_g,
                        const int width,
                        const int height,
                        const float angle,
                        const float Tx,
                        const float Ty,
                        const int out_width,
                        const int out_height,
                        __global uchar *out_g) {
  int gid = get_global_id(0);

  int col = gid % width;
  int row = gid / width;

  if ((col >= width) || (row >= height)) {
    return;
  }

  if (col < 0) {
    return;
  }

  // 
  float c = cos(angle);
  float s = sin(angle);

  // new position
  int new_col = c * col - s * row + Tx;
  int new_row = s * col + c * row + Ty;

  if ((new_col >= out_width) || (new_row >= out_height)) {
    return;
  }

  if (new_col < 0) {
    return;
  }  

  int k = new_row*out_width + new_col;

  out_g[k] = img_g[gid];

}

__kernel void stitch(__global uchar *out_g,
                        const int out_width,
                        const int out_height,
                        const int tile_offset_x,
                        const int tile_offset_y,
                        const int tile_width,
                        const int tile_height,
                        __global const uchar *tile_g) {

  // id inside output
  int gid = get_global_id(0);

  if (gid >= out_width*out_height)
    return;

  // col + row inside output
  int col = gid % out_width;
  int row = gid / out_width;

  // do nothing until we reach the hotspot
  if (col < tile_offset_x) {
    return;
  }

  if (row < tile_offset_y) {
    return;
  }

  // we are in the hotspot
  int tile_col = col - tile_offset_x;
  int tile_row = row - tile_offset_y;

  if (tile_col > tile_width) {
    return;
  }

  if (tile_row > tile_height) {
    return;
  }


  int k = tile_row*tile_width + tile_col;

  if (tile_g[k] == 0) {
    return;
  }

  out_g[gid] = tile_g[k];


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



    # sections['W02_Sec001_Montage_montaged.json'] = sections['W02_Sec001_Montage_montaged.json']

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

    self._downsampler = downsampler


  def getSection(self, id, zoomlevel):
    '''
    '''
    # stitch

    if zoomlevel in self._cache:
      # print 'CACHE HIT'
      return self._cache[zoomlevel]

    print 'CACHING', zoomlevel

    width = 0
    height = 0

    #
    # note: running twice through all tiles is faster than resizing the output array
    #

    for t in self._sections[id]._tiles:
      pixels = t._mipmap.get(zoomlevel)
      # print pixels, pixels.shape
      tile_width = pixels.shape[0]
      tile_height = pixels.shape[1]
      transforms = t._transforms
      offset_x, offset_y = (transforms[0].x, transforms[0].y)
      # print 'offsets', offset_x, offset_y
      k = 0
      while k < zoomlevel:
        offset_x /= 2
        offset_y /= 2
        k += 1    

      # print 'adj. offsets', offset_x
      width = max(width, tile_width+offset_x)
      height = max(height, tile_height+offset_y)

    width = int(width)
    height = int(height)

    # this is out stitched tile array
    output = np.zeros((height*width), dtype=np.uint8)

    # create output buffer
    downsampler = self._downsampler
    mf = cl.mem_flags
    out_img = cl.Buffer(downsampler.context, mf.READ_WRITE| mf.USE_HOST_PTR, hostbuf=output)



    for t in self._sections[id]._tiles:
      pixels = t._mipmap.get(zoomlevel)
      tile_width = pixels.shape[0]
      tile_height = pixels.shape[1]
      transforms = t._transforms
      offset_x, offset_y = (transforms[0].x, transforms[0].y)
      # print 'offsets', offset_x, offset_y
      k = 0
      while k < zoomlevel:
        offset_x /= 2
        offset_y /= 2
        k += 1

      # create CL buffer
      pixels_seq = pixels.ravel()
      # print pixels_seq.shape, pixels_seq.dtype
      in_img = cl.Buffer(downsampler.context, mf.READ_ONLY | mf.USE_HOST_PTR, hostbuf=pixels_seq)
      # print in_img
      print 'GS',width*height
      downsampler.program.stitch(downsampler.queue,
                                 (width*height,),
                                 None,
                                 out_img,
                                 np.int32(width),
                                 np.int32(height),
                                 np.int32(offset_x),
                                 np.int32(offset_y),                                 
                                 np.int32(tile_width),
                                 np.int32(tile_height), in_img)

      # sys.exit()


      # OPTION 1
      # mask = np.ma.masked_equal(pixels, 0, False)
      # output[offset_y:offset_y+tile_height,offset_x:offset_x+tile_width] = np.where(mask.mask, output[offset_y:offset_y+tile_height,offset_x:offset_x+tile_width], pixels)

      # OPTION 2
      # np.place(output[offset_y:offset_y+tile_height,offset_x:offset_x+tile_width], pixels>0, pixels[pixels>0])

      # OPTION 3
      # output_subarray = output[offset_y:offset_y+tile_height,offset_x:offset_x+tile_width]

      # mask = pixels != 0
      # output_subarray[mask] = pixels[mask]

      # OPTION 4
      # # Create a mask and an inversed mask of the tile we are going to add
      # ret, mask = cv2.threshold(pixels, 1, 255, cv2.THRESH_BINARY)
      # mask_inv = cv2.bitwise_not(mask)

      # # Set the area that is going to be changed in the output image
      # roi = output[
      #     offset_y:offset_y+tile_height,offset_x:offset_x+tile_width
      #     ]

      # # Now black-out the area of the new image in the output image
      # out_bg = cv2.bitwise_and(roi, roi, mask = mask_inv)

      # # Take only the interesting stuff out of the new tile
      # tile_fg = cv2.bitwise_and(pixels, pixels, mask = mask)

      # # Put logo in ROI and modify the main image
      # dst = cv2.add(out_bg, tile_fg)
      # output[
      #   offset_y:offset_y+tile_height,offset_x:offset_x+tile_width
      # ] = dst

    cl.enqueue_copy(downsampler.queue, output, out_img).wait()

    # print output.shape, width, height, output

    output = output.reshape(height, width)
    self._cache[zoomlevel] = output
    print 'DONE', zoomlevel

    return output
