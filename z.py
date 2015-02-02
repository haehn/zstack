#!/usr/bin/env python
import cv2
import os
import sys
import socket
import time
import tornado
import tornado.websocket


from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line

import _zstack

#
# default handler
#
class Handler(tornado.web.RequestHandler):

  def initialize(self, logic):
    self.__logic = logic

  @tornado.web.asynchronous
  @gen.coroutine
  def get(self, uri):
    '''
    '''
    # response = yield self.__logic.handle(self)
    self.__logic.handle(self)


  def post(self, uri):
    '''
    '''
    self.__logic.handle(self)


class ServerLogic:

  def __init__( self ):
    '''
    '''
    self._data_grabber = None

  def run( self, data_grabber ):
    '''
    '''
    self._data_grabber = data_grabber

    ip = socket.gethostbyname(socket.gethostname())
    port = 2001

    webapp = tornado.web.Application([

      (r'/viewer/(.*)', tornado.web.StaticFileHandler, dict(path=os.path.join(os.path.dirname(__file__),'web'))),
      (r'/data/(.*)', Handler, dict(logic=self))
  
    ])

    

    webapp.listen(port,max_buffer_size=1024*1024*150000)

    print '*'*80
    print '*', '\033[93m'+'ZSTACK RUNNING', '\033[0m'
    print '*'
    print '*', 'open', '\033[92m'+'http://' + ip + ':' + str(port) + '/' + '\033[0m'
    print '*'*80

    tornado.ioloop.IOLoop.instance().start()

  @gen.coroutine
  def handle( self, handler ):
    '''
    '''
    content = None

    #
    #
    #
    print 'test'

    requested_tile = handler.request.uri.split('/')[-1].split('-')
    zoomlevel = int(requested_tile[0])
    x = int(requested_tile[1])
    y = int(requested_tile[2])

    # print 'req', zoomlevel, x, y

    if zoomlevel < 10:
      zoomlevel = 10

    if zoomlevel > 16:
      zoomlevel = 16


    zoomlevel = 6 - (zoomlevel-10)





    while 1:
      loop = IOLoop.instance()
      yield gen.Task(loop.add_timeout, time.time() + 5)


    tile = self._data_grabber.getSection("W02_Sec001_Montage_montaged.json",zoomlevel)

    # output = StringIO.StringIO()
    content = cv2.imencode('.jpg', tile[y*512:y*512+512,x*512:x*512+512])[1].tostring()
    content_type = 'image/jpeg'


    # invalid request
    if not content:
      content = 'Error 404'
      content_type = 'text/html'

    # print 'IP',r.request.remote_ip

    handler.set_header('Access-Control-Allow-Origin', '*')
    handler.set_header('Content-Type', content_type)
    handler.write(content)




def print_help( script_name ):
  '''
  '''
  description = ''
  print description
  print
  print 'Usage: ' + script_name + ' INPUT_DIRECTORY OUTPUT_DIRECTORY'
  print


#
# entry point
#
if __name__ == "__main__":

  # always show the help if no arguments were specified
  if len(sys.argv) != 0 and len( sys.argv ) < 3:
    print_help( sys.argv[0] )
    sys.exit( 1 )

  input_dir = sys.argv[1]
  output_dir = sys.argv[2]

  data_grabber = _zstack.DataGrabber()
  data_grabber.run( input_dir )
  # data_grabber.getSection("W02_Sec001_Montage_montaged.json",5)
  # data_grabber.getSection("W02_Sec001_Montage_montaged.json",4)
  # data_grabber.getSection("W02_Sec001_Montage_montaged.json",3)
  # data_grabber.getSection("W02_Sec001_Montage_montaged.json",2)
  # data_grabber.getSection("W02_Sec001_Montage_montaged.json",1)
  # data_grabber.getSection("W02_Sec001_Montage_montaged.json",0)


  server_logic = ServerLogic()
  server_logic.run( data_grabber )
