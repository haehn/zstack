import numpy as np
import pyopencl as cl
import sys

class MipMap(object):

  def __init__(self, image, transforms):
    '''
    '''
    self._original = image
    self._transforms = transforms

    self._levels = []
    self._width = image.shape[0]
    self._height = image.shape[1]

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
    height = self._height

    mf = cl.mem_flags
    image_format = cl.ImageFormat(cl.channel_order.R, cl.channel_type.UNSIGNED_INT8)
    in_img = cl.Image(downsampler.context, mf.READ_ONLY | mf.USE_HOST_PTR, image_format, hostbuf=self._original)

    transform = self._transforms[1]
    c = np.cos(transform.r)
    s = np.sin(transform.r)

    points = [[0, 0], [0, height - 1], [width - 1, 0], [width - 1, height - 1]]
    min_x, min_y, max_x, max_y = [ sys.maxint, sys.maxint, -sys.maxint, -sys.maxint ]
    for point in points:
        new_x = c * point[0] - s * point[1] + transform.x
        new_y = s * point[0] + c * point[1] + transform.y
        min_x = min(min_x, new_x)
        min_y = min(min_y, new_y)
        max_x = max(max_x, new_x)
        max_y = max(max_y, new_y)

    tx2 = transform.x - min_x
    ty2 = transform.y - min_y
    width, height = (int(max_x - min_x + 1), int(max_y - min_y + 1))

    for l in range(self._max_level+1):

      out_buffer = np.zeros(shape=(width, height), dtype=np.uint8)
      out_img = cl.Image(downsampler.context, mf.READ_WRITE, image_format, (out_buffer.shape))

      if l==0:
        downsampler.program.transform(downsampler.queue, out_buffer.shape, None, in_img, np.float32(transform.r), np.float32(transform.x), np.float32(transform.y), out_img)
      else:
        downsampler.program.downsample(downsampler.queue, out_buffer.shape, None, in_img, out_img)
      

      cl.enqueue_read_image(downsampler.queue, out_img, (0,0), out_buffer.shape, out_buffer).wait()

      self._levels.append(out_buffer)
      in_img = out_img

      width /= 2
      height /= 2

    # print self._levels

  def get(self, level):
    '''
    '''

    return self._levels[level]
