import base64
import cv2
import json
import numpy as np
import uuid
import StringIO
import zlib

from view import View

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

    if message['name'] == 'PREPARE':
      z = message['value'][0]
      roi = message['value'][1]
      zoomlevel = message['value'][2]

      # check if we have data for this tile
      # if not z in self._manager._views:
      #   self._manager._views[z] = [None]*len(self._manager._zoomlevels)


      # view = self._manager._views[z][zoomlevel]

      # if not view:
      req_tiles = self._manager.image_roi_to_tiles(z, zoomlevel, roi)
      print req_tiles
      uid = uuid.uuid4()
      view = View(req_tiles, zoomlevel, roi, uid.hex)
      # self._manager._views[z][zoomlevel] = view
      self._manager._viewing_queue.append(view)
      self._manager._views[uid.hex] = view
      self._websocket.send(u'wait '+uid.hex)


    elif message['name'] == 'GET':
      uid = message['value'][0]

      if not uid in self._manager._views or not self._manager._views[uid]._status.isLoaded():
        self._websocket.send(u'wait '+uid)
      else:

        view = self._manager._views[uid]
        data = view._imagedata
        bbox = view._bbox
        roi = view._roi
        data = data.reshape(bbox[3], bbox[1])      

        # c_image_data = zlib.compress(data[roi[0]:roi[1], roi[2]:roi[3]].ravel())
        # output = StringIO.StringIO()
        # output.write(c_image_data)
        # self._websocket.send(output.getvalue())

        # c_image_data = data[roi[0]:roi[1], roi[2]:roi[3]].ravel()
        # self._websocket.send(c_image_data.tostring())

        content = cv2.imencode('.jpg', data[roi[0]:roi[1], roi[2]:roi[3]])[1].tostring()
        
        self._websocket.send(content)

