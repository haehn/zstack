import json

from fileloader import FileLoader
from section import Section

class JSONLoader(FileLoader):

  def load(self):
    '''
    '''
    
    with open(self._filename) as f:
      new_section = Section.fromJSON(json.load(f))

    return new_section

