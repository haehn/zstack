import cv2
import os
import socket
import time
import tornado
import tornado.gen
import tornado.web
import tornado.websocket

cl = []

class WebSocketHandler(tornado.websocket.WebSocketHandler):

  def initialize(self, manager):
    '''
    '''
    self._manager = manager
    self._manager._broadcaster = self
    self.__controller = self._manager._websocket_controller

  def open(self):
    '''
    '''
    if self not in cl:
      cl.append(self)

    self.__controller.handshake(self)

  def on_close(self):
    '''
    '''
    if self in cl:
      cl.remove(self)

  def on_message(self, message):
    '''
    '''
    self.__controller.on_message(message)

  def send(self, message, binary=True):
    '''
    '''
    # for c in cl:
    self.write_message(message, binary=binary)

  def broadcast(self, message, binary=True):
    '''
    '''
    for c in cl:
      c.write_message(message, binary=binary)


class WebServerHandler(tornado.web.RequestHandler):

  def initialize(self, webserver):
    self._webserver = webserver

  @tornado.web.asynchronous
  @tornado.gen.coroutine
  def get(self, uri):
    '''
    '''
    self._webserver.handle(self)


class WebServer:

  def __init__( self, manager ):
    '''
    '''
    self._manager = manager

  def start( self ):
    '''
    '''

    ip = socket.gethostbyname('')
    port = 2001

    webapp = tornado.web.Application([

      (r'/ws', WebSocketHandler, dict(manager=self._manager)),
      (r'/viewer/(.*)', tornado.web.StaticFileHandler, dict(path=os.path.join(os.path.dirname(__file__),'../web'))),
      (r'/data/(.*)', WebServerHandler, dict(webserver=self))
  
    ])

    webapp.listen(port, max_buffer_size=1024*1024*150000)

    print 'Starting webserver at \033[93mhttp://' + ip + ':' + str(port) + '\033[0m'

    tornado.ioloop.PeriodicCallback(self._manager.process, 100).start()
    tornado.ioloop.IOLoop.instance().start()

  @tornado.gen.coroutine
  def handle( self, handler ):
    '''
    '''
    content = None

    request = handler.request.uri.split('/')[-1]

    if request == 'content':
      # must be the table of contents
      content = self._manager.getContent()
      content_type = 'text/json'

    else:
      # must be a tile
      requested_tile = request.split('-')
      zoomlevel = int(requested_tile[0])
      x = int(requested_tile[1])
      y = int(requested_tile[2])
      z = int(requested_tile[3])
      image_top_left_x = int(requested_tile[4])
      image_top_left_y = int(requested_tile[5])
      image_bottom_right_x = int(requested_tile[6])
      image_bottom_right_y = int(requested_tile[7])
      image_roi = [image_top_left_x, image_top_left_y, image_bottom_right_x, image_bottom_right_y]

      tile = self._manager.get(x, y, z, zoomlevel, image_roi)

      # right now block until we have the result.. maybe can be solved better
      while tile.shape == (0,):
        # loop = IOLoop.instance()
        # yield gen.Task(loop.add_timeout, time.time() + 5)
        self._manager.process()
        tile = self._manager.get(x, y, z, zoomlevel, image_roi, None)
      
      ts = self._manager._client_tile_size
      content = cv2.imencode('.jpg', tile[y*ts:y*ts+ts,x*ts:x*ts+ts])[1].tostring()
      content_type = 'image/jpeg'

    # invalid request
    if not content:
      content = 'Error 404'
      content_type = 'text/html'

    handler.set_header('Access-Control-Allow-Origin', '*')
    handler.set_header('Content-Type', content_type)
    handler.write(content)
