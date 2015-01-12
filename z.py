#!/usr/bin/env python
import os
import sys
import socket
import tornado
import tornado.websocket

import _zstack

#
# default handler
#
class Handler(tornado.web.RequestHandler):

  def initialize(self, logic):
    self.__logic = logic

  def get(self, uri):
    '''
    '''
    self.__logic.handle(self)

  def post(self, uri):
    '''
    '''
    self.__logic.handle(self)


class ServerLogic:

  def __init__( self ):
    '''
    '''
    pass

  def run( self, input_dir, output_dir ):
    '''
    '''
    ip = socket.gethostbyname(socket.gethostname())
    port = 2001

    webapp = tornado.web.Application([

      (r'/(.*)', Handler, dict(logic=self))
  
    ])

    

    webapp.listen(port,max_buffer_size=1024*1024*150000)

    print '*'*80
    print '*', '\033[93m'+'ZSTACK RUNNING', '\033[0m'
    print '*'
    print '*', 'open', '\033[92m'+'http://' + ip + ':' + str(port) + '/' + '\033[0m'
    print '*'*80

    tornado.ioloop.IOLoop.instance().start()

  def handle( self, r ):
    '''
    '''
    content = None

    # invalid request
    if not content:
      content = 'Error 404'
      content_type = 'text/html'

    # print 'IP',r.request.remote_ip

    r.set_header('Access-Control-Allow-Origin', '*')
    r.set_header('Content-Type', content_type)
    r.write(content)




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

  server_logic = ServerLogic()
  server_logic.run( input_dir, output_dir )
