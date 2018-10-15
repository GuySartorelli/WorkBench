"""
Holds command methods for manipulating nodes and attributes
"""
import collections

from toolkitPackage import utils
from toolkitPackage.workbench import Workbench
from toolkitPackage.converter import nodeInfo

'''
To add if I need it or after assignment:
nodeExists (workbench=None by default but can use this parameter to check if the node exists in a bench instead. Asterisk means "any characters" so that you can check *_bind aka anything that ends with _bind.)

types for listSelection, nativeType parameter for listNodes
'''

def select(node, add=False, deselect=False, hierarchy=False):
    """
    Select (or deselect) the node(s) in the 3D application
    @param node: node object or list of objects to be selected (or deselected)
    @param add: add the node to the current selection (instead of replacing selection)
    @param deselect: remove the node fromt he current selection
    @param hierarchy: select all children, grandchildren, etc of the node
    @return: None
    """
    if Workbench.modeIsStandalone:
        raise TypeError("select command not available for Workbench mode {0!r}".format(Workbench.mode))
    
    elif Workbench.modeIsMaya:
        Workbench.cmds.select(node, add=add, deselect=deselect, hierarchy=hierarchy) #may need node.fullPathName


def wrapNode(node):
    """
    Wraps supported nodes based on string name
    @param node: str, name or fullPathName of node to be wrapped
    """
    nodes = utils.misc.makeList(node)
    wrappedNodes = []
    for nd in nodes:
        #using the name passed or retrieved, wrap the node.
        if isinstance(nd, (str, unicode)):
            try:
                wrappedNodes.append(nodeInfo.Conversion.nodeTypeByMode[Workbench.mode][nativeNodeType(nd)](wrapNode=nd))
            except KeyError:
                warning("Native node {0!r} not currently supported by Workbench.".format(nativeNodeType(nd)) )
    return wrappedNodes


def listSelection():
    """
    Wraps supported nodes for the current in-application selection
    @return: list, all nodes currently selected
    """
    if Workbench.modeIsStandalone:
        raise TypeError("getSelection command not available for Workbench mode {0!r}".format(Workbench.mode))
    
    if Workbench.modeIsMaya:
        #Returns wrapped node objects. Gets class from dictionary on nodeInfo.Conversion.
        selection = Workbench.cmds.ls(sl=1, long=1)
   
    return wrapNode(selection)

getSelection = listSelection


def listNodes(name=None, type=None, invisible=False):
    """
    List all nodes in the scene according to parameters
    @param name: str, list all nodes with this name. Use * as wildcard.
    @param type: list or str, list all nodes of this type. Workbench node types only.
    @param invisible: bool, list only invisible dag objects.
    @return: list, wrapped nodes that fit the parameters
    """
    type = utils.misc.makeList(type)
    nodesList = []
    
    if Workbench.modeIsStandalone:
        raise TypeError("listNodes command not available for Workbench mode {0!r}".format(Workbench.mode))
    
    if Workbench.modeIsMaya:
        for tp in type:
            if not tp is None:
                for mayaType in nodeInfo.Conversion.nodeTypeByClass[tp]['maya']:
                    if name:
                        nodesList.append( Workbench.cmds.ls(name, long=1, type=mayaType, invisible=invisible) )
                    else:
                        nodesList.append( Workbench.cmds.ls(long=1, type=mayaType, invisible=invisible) )
            else:
                if name:
                    nodesList.append( Workbench.cmds.ls(name, long=1, invisible=invisible) )
                else:
                    nodesList.append( Workbench.cmds.ls(long=1, invisible=invisible) )
    
    return wrapNode(nodesList)


def nativeNodeType(node):
    """
    Gets native node type from the 3D application based on the node name string
    @param node: str, full path of node of which you want the type
    @return: str, native node type 
    """
    if Workbench.modeIsStandalone:
        raise TypeError("nativeNode command not available for Workbench mode {0!r}".format(Workbench.mode))
    
    elif Workbench.modeIsMaya:
        #you can get the API type by adding api=True
        return Workbench.cmds.nodeType(node)


def getHierarchy(node, descendents=False, ancestors=False, children=False, parent=False, shapes=False, type=None):
    """
    Gets the dag node hierarchy (does not include dependency nodes)
    @param node: node object from which you want a hierarchy list
    @param descendents: include all descendents in returned list
    @param ancestors: include all ancestors in returned list
    @param children: include all direct children in returned list
    @param parent: include direct parent in returned list
    @param shapes: return shapes parented to this node in returned list
    @param type: return only nodes of this type (can be native or Workbench node types)
    @return: list, nodes in the hierarchy per chosen parameters  
    """
    return node.getHierarchy(descendents=descendents, ancestors=ancestors, children=children, parent=parent, shapes=shapes, type=type)
    
listRelatives = getHierarchy


def transform(node, query=False, relative=False, translate=None, rotate=None, scale=None, pivot=None, worldSpace=False):
    """
    Set the transform values for the node
    @param node: node object to be transformed
    @param query: bool, return the current value instead of setting it
    @param relative: bool, apply transforms relative to current values 
    @param translate: list, XYZ translate values to apply
    @param rotate: list, XYZ rotate values to apply 
    @param scale: list, XYZ scale values to apply
    @param pivot: list, XYZ coordinates for node pivot point
    @param worldSpace: get or set transforms in worldspace
    @return: None or queried transforms
    """
    return node.transform(query=query, relative=relative, translate=translate, rotate=rotate, scale=scale, pivot=pivot)


def freezeTransform(node, translate=None, rotate=None, scale=None):
    """
    Freeze transforms for the node
    @param node: node object to have frozen transforms
    @param translate: list, XYZ translate values to freeze
    @param rotate: list, XYZ rotate values to freeze
    @param scale: list, XYZ scale values to freeze
    @return: None    
    """
    node.freezeTransform(translate=translate, rotate=rotate, scale=scale)


def getBoundingBox(node, worldSpace=False):
    """
    Get the size of the bounding box
    @param node: node object of which to get the bounding box
    @param worldSpace: get bounding box values in world space
    @return: list, minimum and maximum XYZ values as vector objects
    """
    return node.getBoundingBox(worldSpace=worldSpace)


def matchTransform(node, matchNode, translate=False, rotate=False, scale=False):
    """
    Transform a node to match the transformations of another node
    @param node: node object to be transformed
    @param matchNode: node object to be matched
    @param translate: bool or list[str], True for all axis or list axes to be matched (e.g. ['x', 'z'] )
    @param rotate: bool or list[str], True for all axis or list axes to be matched (e.g. ['x', 'z'] )
    @param scale: bool or list[str], True for all axis or list axes to be matched (e.g. ['x', 'z'] )
    @return: None
    """
    node.matchTransform(matchNode=matchNode, translate=translate, rotate=rotate, scale=scale)


def parent(node, parent, query=False):
    """
    Set a new parent for this node or unparent this node
    @param node: node to be parented
    @param parent: node to be the new parent (ignored if query is True)
    @param query: bool, get the parent instead of setting it
    @return: parent if query is True, else None
    """
    node.parent(parent=parent, query=query)


def duplicate(node, name=None, noChildren=False, inputConnections=False, upstreamNodes=False, downstreamNodes=False, translate=None, rotate=None, scale=None, relative=True):
    """
    Duplicates the node and optionally any nodes connected to it
    @param name: str, name for the new duplicate (or None)
    @param noChildren: bool, does not duplicate children if True
    @param inputConnections: bool, copies input connections from original if True
    @param upstreamNodes: bool, duplicates and connects nodes upstream if True
    @param downstreamNodes: bool, duplicates and connects nodes downstream if True
    @param translate: list, new XYZ coordinates for duplicate node if transformable
    @param rotate: list, new XYZ orientation for duplicate node if transformable
    @param scale: list, new XYZ scale for duplicate node if transformable
    @param relative: bool, transforms relative to original position if True
    @return: duplicate node object
    """
    return node.duplicate(name=node, noChildren=noChildren, inputConnections=inputConnections, upstreamNodes=upstreamNodes, downstreamNodes=downstreamNodes,
                          translate=translate, rotate=rotate, scale=scale, relative=relative)


def hide(node):
    """
    Hides nodes in viewport
    @param node: node object(s) to be hidden
    @return: None
    """
    node = utils.misc.makeList(node)
    for nd in node:
        nd.hide()


def unhide(node):
    """
    Unhides nodes in viewport
    @param node: node object(s) to be unhidden
    @return: None
    """
    node = utils.misc.makeList(node)
    for nd in node:
        nd.unhide()


def toggleVisibility(node):
    """
    Hides visible nodes and unhides invisible nodes in viewport
    @param node: node object(s) to be hidden or unhidden
    @return: None
    """
    node = utils.misc.makeList(node)
    for nd in node:
        nd.toggleVisibility()

toggleVis = toggleVisibility


def rename(node, name, replace=None, keepPrefix=False, keepSuffix=False, delimiter=1):
    """
    Renames the node(s)
    @param node: node object(s) to be renamed
    @param name: str, new name for the node(s)
    @param replace: str, string to replace with name
    @param keepPrefix: bool, whether to keep or replace the existing prefix(s) (ignored if replace has value)
    @param keepSuffix: bool, whether to keep or replace the existing suffix(s) (ignored if replace has value)
    @param delimiter: str or int, starting delimiter character for renaming multiple objects (ignored if replace has value)
    """
    node = utils.misc.makeList(node)
    for nd, delim in zip(node, utils.names.generateDelimiters(delimiter)):
        if len(node) > 1 and not replace is None:
            name += delim
        nd.rename(name=name, replace=replace, keepPrefix=keepPrefix, keepSuffix=keepSuffix)


def delete(item):
    """
    deletes a node or attribute
    @param item: node or attribute object to be deleted
    @return: None
    """
    item.delete()


def loft(curves, name=None, degree=3, spansBetweenCurves=1):
    """
    Creates a lofted nurbs surface between curves
    @param curves: list, curve objects between which the surface should be lofted
    @param name: str, name of new lofted surface
    @param degree: int, degree of the resulting surface
    @param spansBetweenCurves: int, number of spans between curves 
    @return: nurbs surface object
    """
    if not name:
        name = 'loftedSurface'
    if Workbench.modeIsMaya:
        newNurb = Workbench.cmds.loft(curves, name=name, degree=degree, sectionSpans=spansBetweenCurves)
    return wrapNode(newNurb)


def addAttribute(node, type, longName=None, shortName=None, value=None, minValue=None, maxValue=None):
        """
        Adds new attributes to the node.
        @param node: node to which the attribute should be added
        @param type: str, type of the attribute to be added
        @param longName: str, long reference name for the attribute
        @param shortName: str, short reference name for the attribute
        @param value: initial value for the attribute. Data type depends on type
        @param minValue: float, minimum allowed value for new attribute if type is numeric
        @param maxValue: maximum allowed value for new attribute if type is numeric
        @return: Attribute object
        """
        node.addAttribute(type=type, longName=longName, shortName=shortName, value=value, minValue=minValue, maxValue=maxValue)

addAttr = addAttribute


def setAttribute(attribute, value, node=None):
    """
    Sets the current value stored by an attribute
    @param attribute: name of attribute as str or attribute object for which the attribute should be set
    @param value: new value to be held by this attribute. Data type depends on attribute type
    @param node: node object that has the attribute
    @return: None
    """
    if node:
        attribute = node.__getattr__(attribute)
    attribute.set(value)

setAttr = setAttribute


def getAttribute(attribute, node=None):
    """
    Gets the current value stored by an attribute
    @param attribute: name of attribute as str or attribute object for which the attribute should be set
    @param node: node object that has the attribute
    @return: Attribute's value
    """
    return attribute.get()

getAttr = getAttribute


def lockAttribute(attribute, node=None, unlock=False):
    """
    Locks the attribute so that values cannot be set
    @param attribute: name of attribute(s) as str (list if multiple) or attribute object(s) for which the attribute should be set
    @param node: node object(s) that has the attribute
    @param unlock: bool, unlocks the attribute if True
    @return: None
    """
    #get attribute object(s) from node(s)
    attributes = utils.misc.combineAttributesWithNodes(node, attribute)
    for attr in attributes:
        attr.lock(unlock=unlock)

lockAttr = lockAttribute


def connectAttribute(fromAttribute, toAttribute, force=False, ):
    """
    connect two attributes together
    @param fromAttribute: Attribute object to be connected
    @param toAttribute: Attribute object to connect to
    @param force: override any previously existing incoming connections
    @return: None
    """
    fromAttribute.connectTo(toAttribute=toAttribute, force=force)

connectAttr = connectAttribute


def listConnections(attribute=None, node=None):
    """
    Gets a dictionary of inputs and outputs to which this attribute is connected
    @param attribute: name of attribute as str or attribute object for which to list connections
    @param node: node object that has the attribute
    @return: dict, 'input': Attribute object coming in to this attribute,
             'output': list of Attribute objects coming out of this attribute
    """
    if attribute is None:
        return node.listConnections()
    else:
        attributes = utils.misc.combineAttributesWithNodes(node, attribute)
        #combineAttributesWithNodes returns a list so get the first attribute
        return attributes[0].listConnections()


def listAttributes(node):
    """
    Lists all attributes for the node
    @node: node object for which to list attributes
    @return: list, attributes attached to the node
    """
    return node.listAttributes()

listAttrs = listAttributes


def attributeExists(attribute, node=None):
    """
    Find out whether an attribute exists in-scene
    @param attribute: name of attribute as str or attribute object for which to list connections
    @param node: node object that has the attribute
    @return: bool, True if attribute exists 
    """
    if type(attribute) is str:
        #if __getattr__ returns an object, the attribute exists in scene
        try:
            node.__getattr__(attribute)
            return True
        except AttributeError:
            return False
    else:
        #if you can get a value with .get(), the attribute exists in scene
        try:
            attribute.get()
            return True
        except AttributeError:
            return False

attrExists = attributeExists


def setDrivenKey(driver, driven, driverValue, drivenValue, inTangent=None, outTangent=None, preInfinity=None, postInfinity=None):
    """
    connects attributes using a set driven key
    @param driver: attribute object to act as driver for the driver/driven relationship
    @param driven: attribute object to be driven for the driver/driven relationship
    @param driverValue: value of the driver attribute for this keyframe
    @param drivenValue: value of the driven attribute for this keyframe
    @param inTangent: str, the in tangent type for this keyframe. "auto", "clamped", "fast", "flat", "linear", "plateau", "slow", "spline", "stepnext"
    @param outTangent: str, the out tangent type for this keyframe. "auto", "clamped", "fast", "flat", "linear", "plateau", "slow", "spline", "stepnext"
    @param preInfinity: str, determine how to determine values before the first keyframe. "constant", "linear", "cycle", "cycleRelative", "oscillate"
    @param postInfinity: str, determine how to determine values after the last keyframe. "constant", "linear", "cycle", "cycleRelative", "oscillate"
    @return: Animation node which holds the set driven key
    """
    if inTangent is None:
        inTangent = 'linear'
    if outTangent is None:
        outTangent = 'linear'
    
    if Workbench.modeIsStandalone:
        raise TypeError("error command not available for Workbench mode {0!r}".format(Workbench.mode))
    
    elif Workbench.modeIsMaya:
        Workbench.cmds.setDrivenKeyframe(driven, currentDriver=driver, driverValue=driverValue, value=drivenValue, inTangentType=inTangent, outTangentType=outTangent)
    
    #set infinity
    animNode = driven.listConnections(type='Animation')['in']
    animNode.setInfinity(preInfinity=preInfinity, postInfinity=postInfinity)
    return animNode


def getVectorFromNode(node, worldSpace=True):
    """
    create vector object based on node worldspace position
    @param node: node object or position as list to turn into a vector
    @param worldSpace: bool, whether to get the node position in worldSpace
    @return: vector, vector of node position
    """
    if not isinstance(node, utils.misc.Vector):
        if isinstance(node, collections.Sequence) and not isinstance(node, basestring):
            #could be a list, tuple, etc
            vector = utils.misc.Vector(node)
        else:
            vector = utils.misc.Vector(node.transform(query=True, transform=True, worldSpace=worldSpace))
    else:
        vector = node
    return vector


def getDistance (start, end):
    """
    find the distance between one position and another
    @param start: list or vector or node, start position from which to get the distance
    @param end: list or vector or node, end position from which to get the distance
    @return: vector, distance from start position to end position
    """
    start = getVectorFromNode(start)
    end = getVectorFromNode(end)
    return (end-start).length()


def getDirection(start, end):
    """
    find the direction expressed as a unit vector between one position and another
    @param start: list or vector or node, position from which to get the direction
    @param end: list or vector or node, position to which direction be facing
    @return: vector, unit vector expressing the direction from start position to end position
    """
    #I THINK THIS IS INCORRECT!
    start = getVectorFromNode(start)
    end = getVectorFromNode(end)
    return (end-start).normal()    


def error(message):
    """
    raises an error with a specified message
    @param message: message to display with the error
    @return: None
    """
    if Workbench.modeIsStandalone:
        raise TypeError("error command not available for Workbench mode {0!r}".format(Workbench.mode))
    
    elif Workbench.modeIsMaya:
        Workbench.cmds.error(message)


def warning(message):
    """
    raises an error with a specified message
    @param message: message to display with the error
    @return: None
    """
    if Workbench.modeIsStandalone:
        raise TypeError("warning command not available for Workbench mode {0!r}".format(Workbench.mode))
    
    elif Workbench.modeIsMaya:
        Workbench.cmds.warning(message)