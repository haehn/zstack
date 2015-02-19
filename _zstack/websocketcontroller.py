import json
import numpy as np
import StringIO
import zlib

class WebSocketController(object):

  def __init__(self, manager):
    '''
    '''
    self._manager = manager

    self._websocket = None

  def handshake(self, websocket):
    '''
    '''
    self._websocket = websocket

    self.send_welcome()


  def send_welcome(self):
    '''
    '''
    self._websocket.send(u'welcome')

  def on_message(self, message):
    '''
    '''
    message = json.loads(message)

    if message['name'] == 'GET':
      roi = message['value'][0]
      zoomlevel = message['value'][1]

      view = self._manager._views[0][0]
      data = view._imagedata
      bbox = view._bbox
      data = data.reshape(bbox[3], bbox[1])      



      c_image_data = zlib.compress(data[roi[0]:roi[1], roi[2]:roi[3]].ravel())

      output = StringIO.StringIO()
      output.write(c_image_data)

      self._websocket.send(output.getvalue())
