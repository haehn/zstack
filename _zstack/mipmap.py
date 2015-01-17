import numpy as np
import pyopencl as cl

class MipMap(object):

  def __init__(self, image):
    '''
    '''
    self._levels = [image]
    self._width = image.shape[0]

    # count zoom levels
    k = 0
    width = self._width
    while width >= 512:
      width /= 2
      k += 1


    self._max_level = k


  def create(self, downsampler):
    '''
    '''
    width = self._width

    mf = cl.mem_flags
    image_format = cl.ImageFormat(cl.channel_order.R, cl.channel_type.UNSIGNED_INT8)
    in_img = cl.Image(downsampler.context, mf.READ_ONLY | mf.USE_HOST_PTR, image_format, hostbuf=self._levels[0])

    for l in range(self._max_level):

      width /= 2

      out_buffer = np.zeros(shape=(width, width), dtype=np.uint8)
      out_img = cl.Image(downsampler.context, mf.READ_WRITE, image_format, (out_buffer.shape))

      downsampler.program.downsample(downsampler.queue, out_buffer.shape, None, in_img, out_img)

      cl.enqueue_read_image(downsampler.queue, out_img, (0,0), out_buffer.shape, out_buffer).wait()

      self._levels.append(out_buffer)
      in_img = out_img

    # print self._levels

  def get(self, level):
    '''
    '''

    return self._levels[level]
