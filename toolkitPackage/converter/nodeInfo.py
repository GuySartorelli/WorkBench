"""
Holds Conversion class which has information about node classes. Placed here to avoid circular imports.
"""
class Conversion(object):
    """
    This class holds information about which native nodes are wrapped by which classes, and valid parameter strings for some node classes
    """
    nodeTypeByClass = {}
    nodeTypeByMode = {'maya':{}}
    compoundNodeTypeByMode = {'maya':{}}
    
    @classmethod
    def confirmValidAxis(cls, axis):
        """
        axis could be a list e.g. ['x', 'y', 'z'] or str e.g. 'xyz' or 'x,y,z'. Check it against valid axis strings and then return it as a list
        @param axis: str or list, axes to be checked
        @return: list, axes in a list
        """
        validAxisStrings = ['x', 'y', 'z', 'xy', 'xz', 'yz', 'xyz']
        
        axis = ''.join(axis).lower().replace(',', '')
        if axis in validAxisStrings:
            return [c for c in axis]
        else:
            return None