#imports maya.cmds and maya.api.OpenMaya if Workbench.modeIsMaya()

from importlib import import_module

class Bench(object):
    #This class will hold all of the nodes
    def __init__(self, name='newBench'):
        import os.path
        
        self._ext = '.bench'
        self.name = name
        self.defaultPath = "/benchFiles/"
        self.path = self.defaultPath
    
    def _getFilePath(self, name):
        if name is None:
            name = self.name
        if self.path[-1] != '/':
            self.path += '/'
        
        #check for relative path and return full path with file name
        if self.path[0] == '.' or ( self.path[0] == '/' and self.path[1] != '/' ): 
            relativePath = os.path.dirname(os.path.realpath(__file__))
            return os.path.join(relativePath, self.path, name + self._ext)
        else:
            return os.path.join(self.path, name + self._ext)
    
    def add(self, node):
        #add the node to the object. Now you can 
        #to save on memory, perhaps either only the char node should be added?
        #Alternatively, add and immediately save to file so we're not holding a dict of all the nodes.
        pass
    
    def remove(self, node):
        #remove the node from the object. Probably called automatically on node destruction.
        pass
    
    def hasNode(self, node):
        #check if a node is held by this bench and return true or false
        pass
    
    def save(self, name=None):
        file = self._getFilePath(name)
        #save bench down to file
    
    def load(self, name):
        file = self._getFilePath(name)
        #instantiate and add nodes based on self.path + name + self.ext
    
    def build(self):
        #looks at all nodes (and attributes) in the bench and builds/connects them in a logical order.
        pass

class Workbench(object):
    '''Used for setting and checking the application you're running Workbench in.'''
    _mode = 'standalone'
    mayaModeStrings = ['maya', 'autodesk maya']
    standaloneModeStrings = ['standalone', 'stand-alone', 'bench']
    
    modeVersion = None
    bench = Bench()
    
    #using a metaclass allows me to have class property methods for mode setting, getting, and checking.
    class __metaclass__(type):
        @property
        def mode(cls):
            '''Workbench.mode is the application you're running Workbench in'''
            return cls._mode
        
        @mode.setter
        def mode(cls, value):
            if value.lower() in cls.standaloneModeStrings:
                cls._mode = 'standalone'
            
            elif value.lower() in cls.mayaModeStrings:
                cls._mode = 'maya'
                print "importing maya modules"
                cls.om = import_module('maya.api.OpenMaya')
                cls.cmds = import_module('maya.cmds')
                cls.modeVersion = cls.cmds.about(version=1)
                
            else:
                #throw an error
                pass
    
        @property
        def modeIsStandalone(cls):
            return cls.mode in cls.standaloneModeStrings
        
        @property
        def modeIsMaya(cls):
            return cls.mode in cls.mayaModeStrings