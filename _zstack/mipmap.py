import numpy as np
import pyopencl as cl
import sys

from rigidmodel2d import RigidModel2D

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
    # image_format = cl.ImageFormat(cl.channel_order.R, cl.channel_type.UNSIGNED_INT8)
    # in_img = cl.Image(downsampler.context, mf.READ_ONLY | mf.USE_HOST_PTR, image_format, hostbuf=self._original)

    img_seq = self._original.ravel()

    in_img = cl.Buffer(downsampler.context, mf.READ_ONLY | mf.USE_HOST_PTR, hostbuf=img_seq)

    transform = self._transforms[1]
    # transform = RigidModel2D("0.24 500 500")
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
    output_width, output_height = (int(max_x - min_x)+1, int(max_y - min_y)+1)


    print transform.r, transform.x, transform.y

    # if output_width % 2 != 0:
    #   print 'adjusting width'
    #   output_width += 1
    # if output_height % 2 != 0:
    #   print 'adjusting height'
    #   output_height += 1


    # last_used_nbytes = output_width*output_height


    for l in range(self._max_level+1):

      print 'level', l

      out_buffer = np.zeros(output_width*output_height, dtype=np.uint8)

      # out_img = cl.Image(downsampler.context, mf.READ_WRITE, image_format, (out_buffer.shape))
      out_img = cl.Buffer(downsampler.context, mf.READ_WRITE, out_buffer.nbytes)

      # print 'created output buffer', out_buffer.nbytes

      if l==0:
        # print img_seq.nbytes, width, height, output_width, output_height, out_buffer.nbytes
        downsampler.program.transform(downsampler.queue,
                                      (width*height,),
                                      None,
                                      in_img, 
                                      np.int32(width),
                                      np.int32(height),
                                      np.float32(transform.r),
                                      np.float32(tx2),
                                      np.float32(ty2),
                                      np.int32(output_width),
                                      np.int32(output_height),
                                      out_img)
      else:
        # continue
        # print 'downsampling', width, height, width*height, 'n', output_width, output_height, output_width*output_height

        downsampler.program.ds(downsampler.queue,
                              (width*height,),
                              None,
                              in_img,
                              np.int32(width),
                              np.int32(height),
                              np.int32(output_width),
                              np.int32(output_height),
                              out_img)

      
      # if l>0 and last_used_nbytes!= (out_buffer.nbytes * 4):
      #   print 'last_used_nbytes', last_used_nbytes
      #   print 'out_buffer.nbytes', out_buffer.nbytes
      #   print 'out_buffer.nbytes*4', out_buffer.nbytes*4
      #   print 'width,height', width, height
      #   print 'output_width,output_height', output_width, output_height


      # cl.enqueue_read_image(downsampler.queue, out_img, (0,0), out_buffer.shape, out_buffer).wait()
      cl.enqueue_copy(downsampler.queue, out_buffer, out_img).wait()

      # last_used_nbytes = out_buffer.nbytes
      
      # re-create 2d image from output buffer
      out_buffer = out_buffer.reshape(output_width, output_height)
      self._levels.append(out_buffer)
      

      # if l>3:
      #   print 'writing'
      #   import cv2
      #   cv2.imwrite('/tmp/testnew'+str(l)+'.jpg', out_buffer)

      in_img = out_img
      width = output_width
      height = output_height
      output_width /= 2
      output_height /= 2
      # if output_width % 2 != 0:
      #   output_width += 1
      # if output_height % 2 != 0:
      #   output_height += 1  

    # print self._levels

  def get(self, level):
    '''
    '''

    return self._levels[level]
