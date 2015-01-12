import os
import glob
from jsonloader import JSONLoader

class DataGrabber:

  def __init__(self):

    pass

  def run(self, input_dir):

    #
    # we are looking for JSON files in the input directory
    #
    json_files = glob.glob(os.path.join(input_dir, '*.json'))

    sections = {}

    for f in json_files:

      section = os.path.basename(f)

      loader = JSONLoader(f)
      loaded_section = loader.load()

      sections[section] = loaded_section

      print 'Found section ' + section + ' with ' + str(len(loaded_section._tiles)) + ' tiles.'



    # load data 
    for s in sections:
      sections[s].load(input_dir)
