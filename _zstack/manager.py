import ctypes
import json
import math
import multiprocessing as mp
import numpy as np
import os
import sys

from indexer import Indexer
from level import Level
from loader import Loader
from stitcher import Stitcher
from view import View

class Manager(object):

  def __init__(self, input_dir):
    '''
    '''
    self._input_dir = input_dir
    self._indexer = Indexer()

    self._no_workers = mp.cpu_count() - 1 # leave one main process out
    self._active_workers = mp.Queue(self._no_workers)

    self._loading_queue = []#mp.Queue()
    self._viewing_queue = []

    self._sections = None
    self._views = {}

    self._zoomlevels = None

    self._client_tile_size = 512

    self._current_roi = [-1, -1, -1, -1]
    self._current_z = -1
    self._n = 1
    self._current_zoomlevel = -1
    self._current_client_tile = [None, None, None, None]

  def start(self):
    '''
    '''
    print 'Starting manager with', self._no_workers, 'workers.'

    #
    # index all JSONs
    #
    self._sections = self._indexer.index(self._input_dir)

    print 'Indexed', len(self._sections), 'sections.'

    #
    # find zoomlevels by taking the first tile
    # 
    self._zoomlevels = range(int(math.log(self._sections[0]._tiles[0]._width/512,2)) + 1)

    #
    # add the first sections to the viewing queue
    #
    # for z in range(2):
    self._views[0] = [None]*len(self._zoomlevels)
    # for l in self._zoomlevels[:1:-1]: # but don't queue the two largest zoomlevels yet
    for l in self._zoomlevels[::-1]:
      view = View(self._sections[0]._tiles, l)
      self._views[0][l] = view
      self._viewing_queue.append(view)

    # we start here
    self._current_z = 0
    self._current_zoomlevel = self._zoomlevels[-1]



  def onLoad(self, tile):
    '''
    '''
    print 'Loaded', tile
    # print 'Loaded', tile._mipmapLevels["0"]['imageUrl'], Loader.shmem_as_ndarray(tile._memory)[0:1000]
    self._active_workers.get() # reduce worker counter


  def onStitch(self, view):
    '''
    '''
    print 'Stitched', view
    self._active_workers.get() # reduce worker counter


  def getContent(self):
    '''
    Returns a JSON content descriptor.
    '''
    sections = []
    for i,s in enumerate(self._sections):
      s_descriptor = {}
      s_descriptor['width'] = s._bbox[1]
      s_descriptor['height'] = s._bbox[3]
      s_descriptor['layer'] = i
      s_descriptor['minLevel'] = self._zoomlevels[0]
      s_descriptor['maxLevel'] = self._zoomlevels[-1]
      s_descriptor['tileSize'] = self._client_tile_size
      sections.append(s_descriptor)

    return json.dumps(sections)

  def calc_tiles(self,x,y,z,zoomlevel):
    '''
    '''

    #
    # calculate tiles we really need for the next section
    #
    next_section = self._sections[z]

    if next_section:
      multiplicator = 2**zoomlevel

      # convert x,y from client coordinates to full resolution coordinates
      x_0 = x*self._client_tile_size*multiplicator
      y_0 = y*self._client_tile_size*multiplicator

      # check in which tile x_0 and y_0 are
      tiles_required = []
      for i,t in enumerate(self._sections[z]._tiles):

        # we need to incorporate the transforms here
        offset_x = 0
        offset_y = 0

        for transform in t._transforms:

          offset_x += transform.x
          offset_y += transform.y      

        # print 'top left', offset_x, offset_y
        # print 'bottom right', offset_x+t._bbox[1], offset_y+t._bbox[3]

        if x_0 >= offset_x and y_0 >= offset_y:
          if x_0 <= offset_x+t._bbox[1] and y_0 <= offset_y+t._bbox[3]:

            # print 'Tile', i
            tiles_required.append(t)


      # # create view for the next section
      # view = View(tiles_required, zoomlevel)

      # if not z in self._views:
      #   self._views[z] = [None]*len(self._zoomlevels)


      # self._views[z][zoomlevel] = view
      # self._viewing_queue.append(view)

      # print 'Added future view', tiles_required

      return tiles_required

  def image_roi_to_tiles(self,z,image_roi):
    '''
    '''

    i_top_left = (image_roi[0], image_roi[1])
    i_bottom_right = (image_roi[2], image_roi[3])

    print i_top_left, i_bottom_right

    # check in which tile x_0 and y_0 are
    tiles_required = []
    for i,t in enumerate(self._sections[z]._tiles):

      # we need to incorporate the transforms here
      offset_x = 0
      offset_y = 0

      for transform in t._transforms:

        offset_x += transform.x
        offset_y += transform.y      

      # print 'top left', offset_x, offset_y
      # print 'bottom right', offset_x+t._bbox[1], offset_y+t._bbox[3]

      roi_part_of_tile = False

      tile_top_left = [offset_x, offset_y]
      tile_bottom_right = [offset_x+t._bbox[1], offset_y+t._bbox[3]]


      # roi includes top left of tile
      if (tile_top_left[0] >= i_top_left[0] and tile_top_left[1] >= i_top_left[1]):
        if (tile_top_left[0] <= i_bottom_right[0] and tile_top_left[1] <= i_bottom_right[1]):
          roi_part_of_tile = True

      # roi includes bottom right of tile
      if (tile_bottom_right[0] >= i_top_left[0] and tile_bottom_right[1] >= i_top_left[1]):
        if (tile_bottom_right[0] <= i_bottom_right[0] and tile_bottom_right[1] <= i_bottom_right[1]):
          roi_part_of_tile = True

      # now also check if the tile includes parts of the roi
      if (tile_top_left[0] <= i_top_left[0] and tile_top_left[1] <= i_top_left[1]):
        if (tile_bottom_right[0] >= i_top_left[0] and tile_bottom_right[1] >= i_top_left[1]):
          # top left corner of roi is inside this tile
          roi_part_of_tile = True

      if (tile_top_left[0] <= i_bottom_right[0] and tile_top_left[1] <= i_bottom_right[1]):
        if (tile_bottom_right[0] >= i_bottom_right[0] and tile_bottom_right[1] >= i_bottom_right[1]):
          # bottom right corner of roi is inside this tile
          roi_part_of_tile = True


      if roi_part_of_tile:
        tiles_required.append(t)

    return tiles_required



  def get(self,x,y,z,zoomlevel,image_roi):
    '''
    Grab data using the client tile format.
    '''

    # if (z != self._current_z):
      # we are navigating from slice to slice
      # print 'navigating'

    # if (zoomlevel != self._current_zoomlevel):
      # we are changing the zoom
      # print 'zooming'
      # remove all views in queue
      # self._viewing_queue = []
      # self.get_next(x,y,z,zoomlevel)

    if (self._current_roi[0] == -1):
      # we have a new roi
      print 'NEW',self.image_roi_to_tiles(z, image_roi)
      self._current_roi = image_roi

    if self._current_roi[0] != image_roi[0] or self._current_roi[1] != image_roi[1] or self._current_roi[2] != image_roi[2] or self._current_roi[3] != image_roi[3]:
      # the roi changed
      print self.image_roi_to_tiles(z, image_roi)
      self._current_roi = image_roi
    
    # if zoomlevel == 0:
    #   future_tiles = self.get_next(x,y,z,zoomlevel)  
    #   # print 'We are ready to looooooad', x, y, z, zoomlevel
    #   # print future_tiles
    #   # view = View()
    #   z_new = z + 1
    #   if not z_new in self._views:
    #     self._views[z_new] = [None]*len(self._zoomlevels)

    #   view = self._views[z_new][zoomlevel]

    #   if not view:
    #     view = View(future_tiles, zoomlevel)
    #     self._views[z_new][zoomlevel] = view
    #     self._viewing_queue.append(view)
    #     print 'Added future view'


    self._current_client_tile = [x,y,z,zoomlevel]
    self._current_z = z
    self._current_zoomlevel = zoomlevel

    # check if we have data for this tile
    if not z in self._views:
      self._views[z] = [None]*len(self._zoomlevels)

    view = self._views[z][zoomlevel]

    if not view:
      # if we have a higher zoomlevel, exit
      # if self._views[z][0]:
      #   view = self._views[z][0]
      # else:
      #   print 'Did not find view for layer', z, 'and zoomlevel', zoomlevel
      # we still need to load this zoomlevel
      view = View(self._sections[z]._tiles, zoomlevel)
      # required_tiles = self.calc_tiles(x,y,z,zoomlevel)

      # view = View(required_tiles, zoomlevel)
      self._views[z][zoomlevel] = view
      self._viewing_queue.append(view) # add it to the viewing queue

      # if len(required_tiles) == 1:
      #   # this view only requires one tile one disk
      #   # for i in range(5):
      #   z += 1
      #   tile = self.calc_tiles(x,y,z,zoomlevel)[0]
      #   tile._status.loading()
      #   self._loading_queue.append(tile)      
          # view = View(required_tiles, zoomlevel)
          # self._views[z][zoomlevel] = view
          # self._viewing_queue.append(view) # add it to the viewing queue        

      # view = View(self.get_next(x,y,z,zoomlevel), zoomlevel)      
      # self._views[z+1][zoomlevel] = view
      # self._viewing_queue.append(view)
      return np.empty(0) # and jump out

    # here we definitely have a view for this section with the right zoomlevel
    # but we have to check if it was fully loaded yet

    # TODO we need to check if the tiles cover our ROI  

    if view._status.isLoaded():
      # yes, it is - we can immediately get the data
      data = view._imagedata
      bbox = view._bbox
      data = data.reshape(bbox[3], bbox[1])
      return data

    return np.empty(0) # and jump out


  def process(self):
    '''
    Starts loading the next section.
    '''
    # return

    # do nothing while workers are not available
    if self._active_workers.full():
      return

    #
    # here we have at least 1 worker available
    #

    #
    # viewing has higher priority, so check if we have anything
    # in the viewing queue
    #
    if len(self._viewing_queue) != 0:

      for view in self._viewing_queue:

        # check if we have the tiles required for this view
        allLoaded = True

        for tile in view._tiles:
          # print tile
          if tile._status.isVirgin():
            # we need to load this tile
            tile._status.loading()
            self._loading_queue.append(tile)
            allLoaded = False
            # print 'We need tile', tile
          elif tile._status.isLoading():
            # the tile is still loading
            allLoaded = False
            

        if allLoaded:
          #
          # we have all the tiles and
          # now we can stitch the view
          #
          self._viewing_queue.remove(view)
          view._status.loading()
          # print 'Stitching', view

          # now it is time to calculate the bounding box for this view
          bbox = View.calculateBB(view._tiles, view._zoomlevel)
          # print bbox
          view._bbox = bbox # re-attach the bounding box (since something could have changed)

          # allocate shared mem for view
          memory = mp.RawArray(ctypes.c_ubyte, bbox[1]*bbox[3])
          view._memory = memory # we need to keep a reference
          view._imagedata = Stitcher.shmem_as_ndarray(memory)

          # start worker
          args = (self, view)
          worker = mp.Process(target=Stitcher.run, args=args)
          self._active_workers.put(1) # increase worker counter
          print 'starting stitcher', view
          worker.start()


    #
    # loading has lower priority
    # check if we have anything in the loading queue
    #
    if len(self._loading_queue) != 0:
      tile = self._loading_queue.pop(0)

      #zoomlevels = [0, 1, 2, 3, 4, 5] # TODO dynamically

      # allocate shared mem for tile and for each zoom level
      for z in self._zoomlevels:
        divisor = 2**z
        tile_width = tile._bbox[1] / divisor
        tile_height = tile._bbox[3] / divisor # TODO maybe int?
        memory = mp.RawArray(ctypes.c_ubyte, tile_width*tile_height)
        imagedata = Loader.shmem_as_ndarray(memory)
        tile._levels.append(Level(memory, imagedata))

      # start worker
      args = (self, tile)
      worker = mp.Process(target=Loader.run, args=args)
      self._active_workers.put(1) # increase worker counter
      print 'starting loader', tile
      worker.start()
      return # jump out

    #
    # we basically do no computations right now
    # start loading data in advance
    # last_client_tile = self._current_client_tile
    # if last_client_tile[0]:
    #   n = self._n
    #   if abs(last_client_tile[2]-n) < 3:
    #     future_tiles = self.calc_tiles(last_client_tile[0], last_client_tile[1], n, last_client_tile[3])
    #     if len(future_tiles) == 1:
          
    #       tile = future_tiles[0]
    #       print 'Loading 1 future tile for z =',n, tile

          
    #       # if not n in self._views:
    #       #   self._views[n] = [None]*len(self._zoomlevels)

    #       # if not self._views[n][last_client_tile[3]]:
    #       #   view = View(future_tiles, last_client_tile[3])
    #       #   self._views[n][last_client_tile[3]] = view
    #       #   self._viewing_queue.append(view)        
    #       if tile._status.isVirgin():
    #         tile._status.loading()
    #         self._loading_queue.append(tile)
    #         self._n += 1

