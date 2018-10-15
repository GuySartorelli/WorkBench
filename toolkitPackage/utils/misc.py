def setTransformAxisTrue(self, translate, rotate, scale):
    """
    set transform to all axes if that transform is True or if all are False
    @param translate: 
    @param rotate: 
    @param scale: 
    """
    transforms = translate+rotate+scale
    if translate is True or not transforms:
        translate = ['x', 'y', 'z']
    if rotate is True or not transforms:
        rotate = ['x', 'y', 'z']
    if scale is True or not transforms:
        scale = ['x', 'y', 'z']
    return translate, rotate, scale


def makeList(var):
    """
    returns var as a list (or returns var if already a list)
    @param var: variable to return as a list
    """
    return var if type(var) is list else [var]


def combineAttributesWithNodes(node, attribute):
    """
    combines nodes and attributes into valid attribute objects
    @param node: node object(s) to get attribute objects from
    @param attribute: attribute name(s) or object(s) to append to nodes
    """
    node = utils.misc.makeList(node)
    attribute = utils.misc.makeList(attribute)
    
    attributes = []
    if node[0]:
        for n in node:
            for attr in attribute:
                if type(attr) is str:
                    attributes.append(attr)
                else:
                    attributes.append(n.__getattr__(attr))
    else:
        for attr in attribute:
            attributes.append(attr)
    return attributes

#VERY TEMPORARY!!!!
from ..workbench import Workbench
Workbench.mode='maya'
Vector = Workbench.om.MVector
'''
class Vector
For vectors:
use Maya's magic method style.
Also use more intuitive methods e.g. Vector().dot(othervector)
Magic methods should be aliases of intuitive methods.
'''