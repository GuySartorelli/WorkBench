"""
Holds Attribute class and primary node classes.
"""
#imports eval from maya.mel if iksolver type is spring
import collections

from toolkitPackage.utils import names, misc
from toolkitPackage.workbench import Workbench
from toolkitPackage.converter import nodeInfo
from toolkitPackage.converter import commands

##NOTE: I may at some stage need to develop a dictionary which holds default attribute name conversions - e.g. jointOrient may be Maya specific!
##__getattr__ then would check for the CONVERSION attr first, and if that fails it'll look for the native attr.
##if it finds native attr, spit a warning that a script with that reference won't be compatible with other applications (but bench will if there is a conversion attr for it).
## IT OCCURS TO ME THAT MY SHAPES ARE NOT PARTICULARLY AGNOSTIC!
##A better way to do it would be creating the transform as a part of the buildMaya, but then only wrapping the shape.
##they should inherit transform, and for the buildMaya stuff (e.g. transform) it'll check if the thing is a shape, and if it is it'll grab the parent and operate on that.
##Do that LATER if you have time.


"""
API REFERENCE: http://help.autodesk.com/view/MAYAUL/2017/ENU/?guid=__py_ref_index_html
"""


class Attribute(object):
    '''
    This class handles manipulation of and getting information about attributes
    All node attributes are returned as Attribute objects
    Attribute objects can be printed or converted to strings
    Attribute objects of type boolean can be used directly in boolean checks
    Attribute objects that point to the same attribute will return true if compared using ==
    '''
    def __init__(self, attrName, node=None, _newAttr=False):
        """
        @param node: object of a class that inherets Node. Indicates the node to which the attribute belongs
        @param attrName: str, name of the attribute to which the Attribute object points
        @param _newAttr: bool, used only by the classmethod add. Leave at default value
        @return: instantiated Attribute object
        """
        if Workbench.modeIsMaya:
            try:
                if isinstance(attrName, str):
                    if not node is None:
                        self._MPlug = node._MFn.findPlug(attrName, True)
                        self.node = node
                    else:
                        raise TypeError("Attribute class requires Node named argument")
                else:
                    self._MPlug = attrName
                    nodeMObject = attrName.node()
                    #I need to get the name of the object before I can send it to be wrapped.
                    #TypeError will be raised if trying to set MFnDag for a non-dag node. Runtime if that non-dag node is a unitConversion. *facepalm*
                    try:
                        MFn = Workbench.om.MFnDagNode(nodeMObject)
                        nodeName = MFn.fullPathName()
                    except (TypeError, RuntimeError):
                        MFn = Workbench.om.MFnDependencyNode(nodeMObject)
                        nodeName = MFn.name()
                    #Now wrap and set the node.
                    self.node = commands.wrapNode(nodeName)[0] if node is None else node
            except AttributeError:
                raise AttributeError("{0} does not have attribute {1}".format(node.__repr__(), attrName))
    
    def __repr__(self):
        """
        :rtype: `unicode`
        """
        return u"{0!s}({1!r})".format(self.__class__.__name__, self.longName)
    
    def __str__(self):
        return u"{0}".format(self.fullPathName)
    
    def __nonzero__(self):
        if self.type() is bool:
            return self.get()
        else:
            return NotImplemented
    
    def __eq__(self, other):
        if Workbench.modeIsMaya:
            try:
                return self._MPlug == other._MPlug
            except AttributeError:
                return NotImplemented
        else:
            return self.node._isDag == other.node._isDag and self.fullPathName == other.fullPathName
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    @property
    def shortName(self):
        if Workbench.modeIsMaya:
            return self._MPlug.partialName(includeNodeName=True, useAlias=True)
    
    @property
    def longName(self):
        if Workbench.modeIsMaya:
            return self._MPlug.partialName(includeNodeName=True, useLongNames=True, useFullAttributePath=True)
    
    @property
    def fullPathName(self):
        return self.longName.replace(self.node.name, self.node.fullPathName)
    
    
    @property
    def type(self):
        #this property is for convenience only
        return self.getType()
    
    def getType(self, native=False):
        """
        Returns the attribute type
        @param native: bool, return the type in the native format
        @return: pythonic or native attribute type
        """
        if Workbench.modeIsMaya:
            #see http://austinjbaker.com/mplugs-getting-values
            pAttribute = self._MPlug.attribute()
            apiType = pAttribute.apiType() #pAttribute.apiTypeStr
            
            # Float Groups: rotate, translate, scale, Compounds
            if apiType in [Workbench.om.MFn.kAttribute3Double, Workbench.om.MFn.kAttribute3Float,
                           Workbench.om.MFn.kCompoundAttribute] and self._MPlug.isCompound:
                if native:
                    return apiType
                else:
                    return list if (len(xrange(self._MPlug.numChildren())) > 3) else misc.Vector
            
            # Numeric
            elif apiType == Workbench.om.MFn.kNumericAttribute:
                pNumericType = Workbench.om.MFnNumericAttribute(pAttribute).numericType()
                # Bool
                if pNumericType == Workbench.om.MFnNumericData.kBoolean:
                    return bool if not native else pNumericType
                # Int
                elif pNumericType in [Workbench.om.MFnNumericData.kShort, Workbench.om.MFnNumericData.kInt,
                                      Workbench.om.MFnNumericData.kLong, Workbench.om.MFnNumericData.kByte]:
                    return int if not native else pNumericType
                # Double/Float
                elif pNumericType in [Workbench.om.MFnNumericData.kFloat, Workbench.om.MFnNumericData.kDouble, Workbench.om.MFnNumericData.kAddr]:
                    return float if not native else pNumericType
                
            # Enum
            elif apiType == Workbench.om.MFn.kEnumAttribute:
                return int if not native else apiType
            
            # Typed
            elif apiType == Workbench.om.MFn.kTypedAttribute:
                pTypedType = Workbench.om.MFnTypedAttribute(pAttribute).attrType()
                # String
                if pTypedType == Workbench.om.MFnData.kString:
                    return str if not native else pTypedType
                # Matrix
                elif pTypedType == Workbench.om.MFnData.kMatrix:
                    return 'matrix' if not native else pTypedType
            
            # Distance
            elif apiType in [Workbench.om.MFn.kDoubleLinearAttribute, Workbench.om.MFn.kFloatLinearAttribute]:
                return 'centimeters' if not native else apiType
            
            # Angle
            elif apiType in [Workbench.om.MFn.kDoubleAngleAttribute, Workbench.om.MFn.kFloatAngleAttribute]:
                return 'degrees' if not native else apiType
                
            # Matrix (probably same as Typed but just to be safe)
            elif apiType == Workbench.om.MFn.kMatrixAttribute:
                return 'matrix' if not native else apiType
    
    @property
    def value(self):
        return self.get()
    
    @value.setter
    def value(self, value):
        self.set(value)
    
    def get(self):
        """
        Gets the current value stored by an attribute
        @aliases: attr.getValue(), attr.value
        @return: Attribute's value
        """
        if Workbench.modeIsMaya:
            #see http://austinjbaker.com/mplugs-getting-values
            attrType = self.getType()
            
            # Float Groups: rotate, translate, scale, Compounds
            if attrType in [list, misc.Vector]:
                result = []
                for cNum in xrange(self._MPlug.numChildren()):
                    result.append(Attribute(node=self.node, attrName=self._MPlug.child(cNum)).value )
                return result if attrType is list else misc.Vector(result)
            
            # Bool
            elif attrType is bool:
                    return self._MPlug.asBool()
            # Int/Enum
            elif attrType is int:
                return self._MPlug.asInt()
            # Double/Float
            elif attrType is float:
                return self._MPlug.asDouble()
            # Str
            elif attrType is str:
                return self._MPlug.asString()
            # Distance
            elif attrType == 'centimeters':
                return self._MPlug.asMDistance().asCentimeters()
            # Angle
            elif attrType == 'degrees':
                return self._MPlug.asMAngle().asDegrees()
            # Matrix
            elif attrType == 'matrix':
                return Workbench.om.MFnMatrixData(self._MPlug.asMObject()).matrix()
            else:
                commands.error("Error setting attribute value. Attribute type not found.")
    getValue = get
    
    def set(self, value):
        """
        Sets the current value stored by an attribute
        @aliases: attr.setValue()
        @param value: The new value to be held by this attribute. Data type depends on attribute type
        @return: None
        """
        if Workbench.modeIsMaya:
            #see http://austinjbaker.com/mplugs-setting-values
            attrType = self.getType()
            
            # Float Groups: rotate, translate, scale, Compounds
            if attrType in [list, misc.Vector]:
                if isinstance(value, collections.Sequence) and not isinstance(value, basestring):
                    for cNum in xrange(self._MPlug.numChildren()):
                        Attribute(node=self.node, attrName=self._MPlug.child(cNum)).set(value[cNum])
                elif (type(value) is misc.Vector or type(value) is Workbench.om.MVector) and attrType is misc.Vector:
                    Attribute(node=self.node, attrName=self._MPlug.child(0)).set(value.x)
                    Attribute(node=self.node, attrName=self._MPlug.child(1)).set(value.y)
                    Attribute(node=self.node, attrName=self._MPlug.child(2)).set(value.z)
                else:
                    commands.error("{0} got value of type {1}. Needs type {2}".format(self.__repr__(), type(value)), attrType)
                
            # Bool
            elif attrType is bool:
                if type(value) is bool or value in [0,1]:
                    self._MPlug.setBool(value)
                else:
                    commands.error("{0} got value of type {1}. Needs type {2}".format(self.__repr__(), type(value)), bool)
            # Int
            elif attrType is int:
                if isinstance(value, int):
                    self._MPlug.setInt(value)
                else:
                    commands.error("{0} got value of type {1}. Needs type {2}".format(self.__repr__(), type(value)), int)
            # Double/Float
            elif attrType is float:
                if isinstance(value, (float, int)):
                    self._MPlug.setDouble(float(value))
                else:
                    commands.error("{0} got value of type {1}. Needs type {2}".format(self.__repr__(), type(value)), float)
            # String
            elif attrType is str:
                if not isinstance(value, (str, unicode)):
                    commands.warning("Converting value of type {0} to {1}".format(attrType, str))
                self._MPlug.setString(str(value))
            # Distance
            elif attrType == 'centimeters':
                if isinstance(value, (float, int)):
                    value =  Workbench.om.MDistance(float(value), Workbench.om.MDistance.kCentimeters)
                    self._MPlug.setMDistance(value)
                else:
                    commands.error("{0} got value of type {1}. Needs type {2}".format(self.__repr__(), type(value)), float)
            # Angle
            elif attrType == 'degrees':
                if isinstance(value, (float, int)):
                    value = Workbench.om.MAngle(float(value), Workbench.om.MAngle.kDegrees)
                    self._MPlug.setMAngle(value)
                else:
                    commands.error("{0} got value of type {1}. Needs type {2}".format(self.__repr__(), type(value)), float)
            # Matrix
            elif attrType == 'matrix':
                if isinstance(value, Workbench.om._MPlug):
                    sourceValueAsMObject = Workbench.om.MFnMatrixData(value.asMObject()).object()
                    self._MPlug.setMObject(sourceValueAsMObject)
                else:
                    try:
                        MFnTrans = Workbench.om.MFnTransform(self._MPlug.node())
                        sourceMatrix = Workbench.om.MTransformationMatrix(value)#.asMatrix()
                        MFnTrans.set(sourceMatrix)
                    except RuntimeError:
                        commands.error("{0} is an MMatrix type attribute and requires an MPlug as value. The MPlug for a Workbench attribute is attribute._MPlug".format(self.__repr__()))
            else:
                commands.error("Error setting attribute value. Attribute type not found.")
    setValue = set
    
    def lock(self, unlock=False):
        """
        Locks the attribute so that values cannot be set
        @param unlock: bool, unlocks the attribute if True
        @return: None
        """
        if Workbench.modeIsMaya:
            #do the thing
            #unlock if unlock=True
            pass
    
    def connectTo(self, attribute, force=True):
        """
        Connects this attribute to another
        @param attribute: Attribute object to be connected to
        @param force: override any previously existing ingoing connections
        @return: None
        """
        if Workbench.modeIsMaya:
            #see http://austinjbaker.com/mplugs-connecting-plugs
            numeric=[bool, int, float, 'centimeters', 'degrees']
            compound=[list, misc.Vector]
            #check that attributes are compatible
            if any(self.getType() in typeList and attribute.getType() in typeList for typeList in [numeric, compound]) or self.getType() == attribute.getType():
                #disconnect existing connection if any
                if force:
                    try:
                        connected = attribute.listConnections(input=True, output=False)[0]
                        mayaModifierObject = Workbench.om.MDGModifier()
                        mayaModifierObject.disconnect(connected._MPlug, attribute._MPlug)
                        mayaModifierObject.doIt()
                        #if the intermediary node is a unitConversion or other useless node, get rid of it.
                        if isinstance(connected.node, Misc):
                            connected.node.delete()
                    except IndexError:
                        #index error because there is no incoming connection.
                        pass
                #connect attrs. If existing connection and not force, catch and throw the error
                try:
                    mayaModifierObject = Workbench.om.MDGModifier()
                    mayaModifierObject.connect(self._MPlug, attribute._MPlug)
                    mayaModifierObject.doIt()
                except RuntimeError:
                    commands.error("Cannot connect to {0} - connection already exists.".format(attribute.__repr__()))
            else:
                commands.error("Cannot connect attribute of type {0} to attribute of type {1}".format(self.getType(), attribute.getType()) )
    connect=connectTo
    
    def listConnections(self, input=False, output=False):
        """
        Gets a dictionary of inputs and outputs to which this attribute is connected
        @param input: bool, all incoming attributes will be returned
        @param output: bool, all outgoing attributes will be returned
        @return: list, all connected attributes
        """
        if not input and not output:
            input = True
            output = True
        if Workbench.modeIsMaya:
            attrList = []
            #connectedTo doesn't take keyword args, but the args would be (asDest=input, asSrc=output)
            for plug in self._MPlug.connectedTo(input, output):
                attrList.append(Attribute(attrName=plug))
            return attrList
    
    def delete(self):
        """
        Deletes the attribute. Removes the attribute from its node
        @return: None
        """
        if Workbench.modeIsMaya:
            #??
            #return success or failure as boolean?
            pass
    
    #NOTE ALSO:
    #compound plugs: http://austinjbaker.com/mplugs-compound-plugs
    #plug arrays: http://austinjbaker.com/mplugs-array-plug


class Node(object):
    '''
    Superclass for all Workbench nodes. Should not be instantiated directly;
    instead, instantiate the class for the appropriate node type
    '''
    def __init__(self, name=None, wrapNode=None, **kwargs):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @return: instantiated Node object
        """
        if wrapNode is None:
            #kwargs are passed by inherited nodes to indicate how to build the node
            self.build(name=name, **kwargs)
        else:
            self.wrapNode(wrapNode)
    
    #overwrite getattr magic method so that attributes are accessible using node.attrName
    def __getattr__(self, attrName):
        #check all dicts for self and MRO superclasses
        for obj in [self] + self.__class__.mro():
            if obj.__dict__.has_key(attrName):
                if isinstance(obj.__dict__[attrName], property):
                    return obj.__dict__[attrName]#.__get__(self, )
                else:
                    return obj.__dict__[attrName]
        if isinstance(self, Compound):
            #check as above for compound parts
            for node in self.compoundParts:
                if node.__dict__.has_key(attrName):
                    return node.__dict__[attrName]
                try:
                    #try to get the in-scene attribute from the compound parts
                    return Attribute(node=node, attrName=attrName)
                except RuntimeError:
                    pass
        else:
            try:
                #try to get the in-scene attribute from self
                return Attribute(node=self, attrName=attrName)
            except RuntimeError:
                pass
        #if nothing has that attribute (because we haven't returned yet), raise an error.
        raise AttributeError("{0} does not have an attribute \"{1}\".".format(self.__repr__(), attrName))
    
    def __repr__(self):
        """
        :rtype: `unicode`
        """
        return u"{0!s}({1!r})".format(self.__class__.__name__, self.name)
    
    def __str__(self):
        return u"{0}".format(self.fullPathName)
    
    def __nonzero__(self):
        return self.exists
    
    def __eq__(self, other):
        if Workbench.modeIsMaya:
            try:
                return self._MFn == other._MFn
            except AttributeError:
                return NotImplemented
        else:
            return self._isDag == other._isDag and self.fullPathName == other.fullPathName
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def wrapNode(self, node):
        """
        Wraps an in-scene node with this object
        @param node: fullPathName of in-scene node to be wrapped
        """
        nativeType = commands.nativeNodeType(node)
        if nativeType in nodeInfo.Conversion.nodeTypeByClass[self.__class__.__name__][Workbench.mode] or isinstance(self, CompoundPart):
            if Workbench.modeIsMaya:
                #get maya function set for API commands
                selList = Workbench.om.MSelectionList()
                selList.add(node)
                try:
                    nodeDagPath = selList.getDagPath(0)
                    self._isDag = True
                    self._MFn = Workbench.om.MFnDagNode(nodeDagPath)
                    self._MFn.fullPathName()
                except (TypeError, RuntimeError):
                    nodeDgPath = selList.getDependNode(0)
                    self._isDag = False
                    self._MFn = Workbench.om.MFnDependencyNode(nodeDgPath)
        else:
            commands.error("Native node {0!r} not supported by class {1!r}.".format(nativeType, self.__class__.__name__))
    
    @property
    def name(self):
        if Workbench.modeIsMaya:
            return self._MFn.name()
    
    @property
    def fullPathName(self):
        if Workbench.modeIsMaya:
            if self._isDag:
                return self._MFn.fullPathName()
            else:
                return self._MFn.name()
    
    @name.setter
    def name(self, newName):
        if Workbench.modeIsMaya:
            self.rename(newName)
        self._name = newName
    
    def rename(self, name, replace=None, keepPrefix=False, keepSuffix=False):
        """
        Renames the node
        @param name: str, new name for the node
        @param replace: str, string to replace with name
        @param keepPrefix: bool, whether to keep or replace the existing prefix (ignored if replace has value)
        @param keepSuffix: bool, whether to keep or replace the existing suffix (ignored if replace has value)
        @return: None
        """
        if replace is None:
            name = names.keepAffixes(name=self.name, newName=name, keepPrefix=keepPrefix, keepSuffix=keepSuffix)
        else:
            name = self.name.replace(name, replace)
        if Workbench.modeIsMaya:
            self._MFn.setName(name)
        #note: Transform had to overwrite this so if you change it here please change it there.
    
    def isUniquelyNamed(self):
        """
        Finds out if the node is uniquely named in your scene or bench.
        @aliases: node.nameIsUnique()
        @return: bool, if name is unique or not
        """
        if Workbench.modeIsMaya:
            return self._MFn.hasUniqueName()
    nameIsUnique = isUniquelyNamed
    
    def nextUniqueName(self, _newName=False):
        """
        Used to rename the node with a name that is unique to your scene and bench.
        @param _newName: Used by the class __init__ method if no name is passed for creation.
               Not intended to be used by users.
        @return: str, new name of node
        """
        #if there is already a digit at the end of the name:
        #add 1 to the digit
        #otherwise just slap a 1 at the end
        #check how pymel implements this to see if there is a better way
        while not self.isUniquelyNamed():
            self.name += 1 #note: This is shit.
        return self.name
    
    @property
    def exists(self):
        return Workbench.cmds.objExists(self.fullPathName)
    
    def addAttribute(type, longName=None, shortName=None, value=None, minValue=None, maxValue=None):
        """
        Adds new attributes to the node.
        @param type: str, type of the attribute to be added
        @param longName: str, long reference name for the attribute
        @param shortName: str, short reference name for the attribute
        @param value: initial value for the attribute. Data type depends on type
        @param minValue: float, minimum allowed value for new attribute if type is numeric
        @param maxValue: maximum allowed value for new attribute if type is numeric
        @return: Attribute object
        """
        #check that at least one attribute name type is string.
        if longName is None and shortName is None:
            raise TypeError("Requires an attribute name. None given or type was not str.")
        
        if Workbench.modeIsMaya:
            #see http://austinjbaker.com/mplugs-create-plug
            #return new attr object
            pass
    addAttr = addAttribute
    
    def listAttributes(self, type=None, unhidden=False, locked=False, unlocked=False, userDefined=False):
        """
        Lists all attributes for the node
        @params are not currently supported
        @aliases: node.listAttrs()
        @return: list, attributes attached to the node
        """
        attrList = []
        if Workbench.modeIsMaya:
            numAttrs = self._MFn.attributeCount()
            for num in range(numAttrs):
                plugObj = self._MFn.attribute(num)
                plug = self._MFn.findPlug(plugObj, True)
                attrList.append(Attribute(node=self, attrName=plug))
                #this is the API way but I'll need to do extra work for the parameters. Below is a hacky way to get the params in there.
            #type = commands.makeList(type)
            #for tp in type:
            #    eval("Workbench.cmds.listAttr(self, {0}=True)".format(tp etc etc))
        return attrList
    listAttrs = listAttributes
    
    def listConnections(self):
        """
        Lists all attributes connected to the node
        @return: list, Attribute objects connected to this node
        """
        connections = []
        if Workbench.modeIsMaya:
            for plug in self._MFn.getConnections():
                connections.append(Attribute(node=self, attrName=plug))
        return connections
    
    def getHierarchy(self, descendents=False, child=False, parent=False, shapes=False, type=None):
        """
        Gets the dag node hierarchy (does not include dependency nodes)
        @param descendents: include all descendents in returned list
        @param child: include all direct children in returned list
        @param parent: include direct parent in returned list
        @param shapes: return shapes parented to this node in returned list
        @param type: return only nodes of this type (can be native or Workbench node types)
        @return: list, nodes in the hierarchy per chosen parameters  
        """
        if not self._isDag:
            raise TypeError("getHierarchy command not available for dependency nodes")
        #if everything is false, give them EVERYTHING
        if not descendents and not child and not parent and not shapes:
            descendents=True
            parent=True
            child=True
        #if node is workbench type, get the valid native types.
        types=[]
        for type in misc.makeList(type):
            if nodeInfo.Conversion.nodeTypeByClass.has_key(type):
                types.append(nodeInfo.Conversion.nodeTypeByClass[type][Workbench.mode])
            else:
                types.append(type)
        
        wrapNodes = []
        nativeNodesList = []
        if Workbench.modeIsMaya:
            if type is None:
                if descendents:
                    nativeNodesList.append(Workbench.cmds.listRelatives(self, allDescendents=True, fullPath=True))
                if child:
                    nativeNodesList.append(Workbench.cmds.listRelatives(self, children=True, fullPath=True))
                if parent:
                    nativeNodesList.append(Workbench.cmds.listRelatives(self, parent=True, fullPath=True))
                if shapes:
                    nativeNodesList.append(Workbench.cmds.listRelatives(self, shapes=True, fullPath=True))
            else:
                if descendents:
                    nativeNodesList.append(Workbench.cmds.listRelatives(self, allDescendents=True, type=types, fullPath=True))
                if child:
                    nativeNodesList.append(Workbench.cmds.listRelatives(self, children=True, type=types, fullPath=True))
                if parent:
                    nativeNodesList.append(Workbench.cmds.listRelatives(self, parent=True, type=types, fullPath=True))
                if shapes:
                    nativeNodesList.append(Workbench.cmds.listRelatives(self, shapes=True, type=types, fullPath=True))
            for nativeNodes in nativeNodesList:
                if not nativeNodes is None:
                    for node in nativeNodes:
                        wrapNodes.append(node)
            returnNodes = commands.wrapNode( list(set(wrapNodes)) )
        return returnNodes
    listRelatives = getHierarchy
    
    def duplicate(self, name=None, noChildren=False, inputConnections=False, upstreamNodes=False, downstreamNodes=False,
                  translate=None, rotate=None, scale=None, relative=True):
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
        if name is None:
            name = self.name        
        
        if Workbench.modeIsMaya:
            #duplicate the in-scene object, using the appropriate flags
            #apply transformations
            #return a wrapped duplicate
            pass
    
    def delete(self):
        """
        Deletes the node from the scene
        @return: None
        """
        if Workbench.modeIsMaya:
            Workbench.cmds.delete(self)
        Workbench.bench.remove(self)
    
    def _buildMaya(self, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        #each class holds its own buildMaya info
        pass
    
    def build(self, **kwargs):
        """
        Builds the node into the scene according to parameters set in workbench.
        @return: None
        """
        if Workbench.modeIsStandalone:
            #throw an error
            pass
        else:
            #build the node into the scene
            if Workbench.modeIsMaya:
                self._buildMaya(**kwargs)
        
        if not Workbench.bench.hasNode(self):
            Workbench.bench.add(self)


class Compound(Node):
    """
    superclass for compound nodes
    """
    def __init__(self, wrapNode=None, name=None, **kwargs):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        """
        self.compoundParts = []
        super(Compound, self).__init__(wrapNode=wrapNode, name=name, **kwargs)
    
    def __repr__(self):
        """
        :rtype: `unicode`
        """
        return u"{0!s}({1!r})".format(self.__class__.__name__, [node.__repr__() for node in self.compoundParts])
    
    def __str__(self):
        return u"{0}".format(self.fullPathName)
    
    def wrapNode(self, node):
        """
        wrap node according to appropriate CompoundPart subclass
        @param node: native node to be wrapped
        """
        nativeType = commands.nativeNodeType(node)
        if nativeType in nodeInfo.Conversion.compoundNodeTypeByMode[self.__class__.__name__][Workbench.mode]:
            wrappedNode = nodeInfo.Conversion.compoundNodeTypeByMode[self.__class__.__name__][Workbench.mode](wrapNode=node)
            self.compoundParts.append(wrappedNode)
        else:
            commands.error("Native node {0!r} not supported by class {1!r}.".format(nativeType, self.__class__.__name__))
    
    def rename(self, name, replace=None, keepPrefix=False, keepSuffix=False):
        """
        Renames the node
        @param name: str, new name for the node
        @param replace: str, string to replace with name
        @param keepPrefix: bool, whether to keep or replace the existing prefix (ignored if replace has value)
        @param keepSuffix: bool, whether to keep or replace the existing suffix (ignored if replace has value)
        @return: None
        """
        for part in self.compoundParts:
            part.rename(name=name, replace=replace, keepPrefix=keepPrefix, keepSuffix=keepSuffix)
    
    def duplicate(self, name=None, noChildren=False, inputConnections=False, upstreamNodes=False, downstreamNodes=False,
                  translate=None, rotate=None, scale=None, relative=True):
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
        duplicatedNodes = []
        if downstreamNodes is True:
            commands.warning("Downstream nodes cannot be duplicated for compound nodes.")
        for node in self.compoundParts:
            if node is self.self.compoundParts[0]:
                dup = node.duplicate(name=name, noChildren=noChildren, inputConnections=inputConnections, upstreamNodes=upstreamNodes, downstreamNodes=False,
                                     translate=translate, rotate=rotate, scale=scale, relative=relative)
                duplicatedNodes.append(dup)
            else:
                dup = node.duplicate(name=name, noChildren=noChildren, inputConnections=True, upstreamNodes=False, downstreamNodes=False,
                                     translate=translate, rotate=rotate, scale=scale, relative=relative)
                duplicatedNodes.append(dup)
        return duplicatedNodes
    
    def delete(self):
        """
        Deletes the node from the scene
        @return: None
        """
        for node in self.compoundParts:
            node.delete()
        Workbench.bench.remove(self)


class CompoundPart(Node):
    def __init__(self, wrapNode=None, **kwargs):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        """
        self._partSuffix = 'Part'
        super(CompoundPart, self).__init__(wrapNode=wrapNode, **kwargs)
    
    def rename(self, name, replace=None, keepPrefix=False, keepSuffix=False):
        """
        Renames the node
        @param name: str, new name for the node
        @param replace: str, string to replace with name
        @param keepPrefix: bool, whether to keep or replace the existing prefix (ignored if replace has value)
        @param keepSuffix: bool, whether to keep or replace the existing suffix (ignored if replace has value)
        @return: None
        """
        if replace is None and not keepSuffix:
            name += self._partSuffix
        super(CompoundPart, self).rename(name=name, replace=replace, keepPrefix=keepPrefix, keepSuffix=keepSuffix)
    
    def build(self, **kwargs):
        #all of the building was done by the Compound object. This class only holds information about the built/wrapped node.
        pass


class Transform(object):
    """
    superclass for transform nodes
    """
    def rename(self, name, replace=None, keepPrefix=False, keepSuffix=False, renameShapes=True):
        """
        Renames the node
        @param name: str, new name for the node
        @param replace: str, string to replace with name
        @param keepPrefix: bool, whether to keep or replace the existing prefix (ignored if replace has value)
        @param keepSuffix: bool, whether to keep or replace the existing suffix (ignored if replace has value)
        @param renameShapes: bool, whether to rename shapes nodes which are children to this node 
        @return: None
        """
        #rename the shapes
        if renameShapes:
            shapeName = name+'Shape' if replace is None else name
            for shape in self.shapeNodes:
                shape.rename(name=shapeName, replace=replace, keepPrefix=keepPrefix, keepSuffix=keepSuffix)
        #rename the transform
        if replace is None:
            name = names.keepAffixes(name=self.name, newName=name, keepPrefix=keepPrefix, keepSuffix=keepSuffix)
        else:
            name = self.name.replace(name, replace)
        if Workbench.modeIsMaya:
            self._MFn.setName(name)
            
    @property
    def shapeNodes(self):
       return self.getHierarchy(shapes=True)
    
    def transform(self, query=False, relative=False, translate=None, rotate=None, scale=None, pivot=None, worldSpace=False):
        """
        Set the transform values for the node
        @param query: bool, return the current value instead of setting it. Must query only one transform at a time.
        @param relative: bool, apply transforms relative to current values 
        @param translate: list, XYZ translate values to apply
        @param rotate: list, XYZ rotate values to apply 
        @param scale: list, XYZ scale values to apply
        @param pivot: list, XYZ coordinates for node pivot point
        @param worldSpace: get or set transforms in worldspace
        @return: None or queried transforms
        """
        if Workbench.modeIsMaya:
            translateQuery = Workbench.cmds.xform(self, relative=relative, worldSpace=worldSpace, query=query, translation=translate)
            rotateQuery = Workbench.cmds.xform(self, relative=relative, worldSpace=worldSpace, query=query, rotation=rotate)
            scaleQuery = Workbench.cmds.xform(self, relative=relative, worldSpace=worldSpace, query=query, scale=scale)
            pivotQuery = Workbench.cmds.xform(self, relative=relative, worldSpace=worldSpace, query=query, pivots=pivot)
            #query should only be done one at a time - if done many at once, return only one query value. Priority is parameter order.
            return pivotQuery if pivotQuery else scaleQuery if scaleQuery else rotateQuery if rotateQuery else translateQuery
    
    def freezeTransform(self, translate=True, rotate=True, scale=True):
        """
        Freeze transforms for the node
        @param translate: bool, freeze or do not freeze translate values
        @param rotate: bool, freeze or do not freeze translate values
        @param scale: bool, freeze or do not freeze translate values
        @return: None
        """
        if Workbench.modeIsMaya:
            Workbench.cmds.makeIdentity(self, translate=translate, rotate=rotate, scale=scale, apply=True)
    
    def resetTransforms(self, translate=True, rotate=True, scale=True):
        """
        Reset transforms to 0
        @param translate: bool, reset or do not reset translate values
        @param rotate: bool, reset or do not reset translate values
        @param scale: bool, reset or do not reset translate values
        @return: None
        """
        if Workbench.modeIsMaya:
            Workbench.cmds.makeIdentity(self, translate=translate, rotate=rotate, scale=scale, apply=False)
    
    def getBoundingBox(self, worldSpace=False):
        """
        Get the size of the bounding box
        @param worldSpace: get bounding box values in world space
        @return: list, minimum and maximum XYZ values as vector objects
        """
        if Workbench.modeIsMaya:
            boundingBox = Workbench.cmds.xform(self, query=True, boundingBox=True, worldSpace=worldSpace)
            boundMin = misc.Vector(boundingBox[0:3])
            boundMax = misc.Vector(boundingBox[3:6])
            return [boundMin, boundMax]
    
    def matchTransform(self, matchNode, translate=False, rotate=False, scale=False):
        """
        Transform a node to match the transformations of another node
        @param matchNode: node object to be matched
        @param translate: bool or list[str], True for all axis or list axes to be matched (e.g. ['x', 'z'] )
        @param rotate: bool or list[str], True for all axis or list axes to be matched (e.g. ['x', 'z'] )
        @param scale: bool or list[str], True for all axis or list axes to be matched (e.g. ['x', 'z'] )
        @return: None
        """
        axisIndex = {'x':0, 'y':1, 'z':2}
        translate, rotate, scale = misc.setTransformAxisTrue(translate, rotate, scale)
        
        #use Transform node method transform(query=True) to match self to matchNode
        if translate:
            matchTranslate = self.transform(query=True, translate=True, worldSpace=True)
            matchNodeTranslate = matchNode.transform(query=True, translate=True, worldSpace=True)
            for axis in translate:
                matchTranslate[axisIndex[axis]] = matchNodeTranslate[axisIndex[axis]]
        
        if rotate:
            matchRotate = self.transform(query=True, rotate=True, worldSpace=True)
            matchNodeRotate = matchNode.transform(query=True, rotate=True, worldSpace=True)
            for axis in rotate:
                matchRotate[axisIndex[axis]] = matchNodeRotate[axisIndex[axis]]
        
        if scale:
            matchScale = self.transform(query=True, scale=True, worldSpace=True)
            matchNodeScale = matchNode.transform(query=True, scale=True, worldSpace=True)
            for axis in scale:
                matchScale[axisIndex[axis]] = matchNodeScale[axisIndex[axis]]
    
    def parent(self, parent=None, unparent=False, query=False):
        """
        Set a new parent for this node or unparent this node
        @param parent: node to be the new parent for this node (ignored if unparent or query is True)
        @param unparent: bool, unparent this node (i.e. set the parent for this node as the world. ignored if query is True)
        @param query: bool, get the parent instead of setting it
        @return: None
        """
        if unparent:
            parent=None
        
        if Workbench.modeIsMaya:
            if query is True:
                return self.getHierarchy(parent=True)
            else:
                Workbench.cmds.parent(self, parent, world=unparent)
    
    def hide(self):
        """
        Hides nodes in viewport
        @return: None
        """
        self.visibility.set(True)
    
    def unhide(self):
        """
        Unhides nodes in viewport
        @return: None
        """
        self.visibility.set(False)
    
    def toggleVisibility(self):
        """
        Hides visible nodes and unhides invisible nodes in viewport
        @return: None
        """
        currentVisibility = self.visibility.get()
        self.visibility.set(not currentVisibility)
    toggleVis = toggleVisibility
    
    def deleteHistory(self, nonDeformer=False):
        """
        Deletes history on the node
        @param nonDeformer: bool, delete non-deformer history only
        @return: None
        """
        if Workbench.modeIsMaya:
            if nonDeformer:
                Workbench.cmds.bakePartialHistory(self, prePostDeformers=True)
            else:
                Workbench.cmds.delete(self, constructionHistory=True)


class Shape(object):
    """
    superclass for shape nodes
    """
    def parent(self, parent=None, query=False):
        """
        Set a new parent for this node or unparent this node
        @param parent: node to be the new parent for this node (ignored if query is True)
        @param query: bool, get the parent instead of setting it
        @return: parent if query is True, else None
        """
        if query is True:
            return self.transformNode
        else:
            if Workbench.modeIsMaya:
                oldTransform = self.transformNode
                oldTransform.freezeTransform()
                Workbench.cmds.parent(self, parent, shape=True, relative=True)
                oldTransform.delete()
    
    @property
    def transformNode(self):
        if Workbench.modeIsMaya:
            return self.getHierarchy(parent=True)[0]
    
    def hide(self):
        """
        Hides nodes in viewport
        @return: None
        """
        self.visibility.set(True)
    
    def unhide(self):
        """
        Unhides nodes in viewport
        @return: None
        """
        self.visibility.set(False)
    
    
    def toggleVisibility(self):
        """
        Hides visible nodes and unhides invisible nodes in viewport
        @return: None
        """
        currentVisibility = self.visibility.get()
        self.visibility.set(not currentVisibility)
    toggleVis = toggleVisibility
    
    def deleteHistory(self, nonDeformer=False):
        """
        Deletes history on the node
        @param nonDeformer: bool, delete non-deformer history only
        @return: None
        """
        if Workbench.modeIsMaya:
            if nonDeformer:
                Workbench.cmds.bakePartialHistory(self, prePostDeformers=True)
            else:
                Workbench.cmds.delete(self, constructionHistory=True)
    
    def build(self, name, parent, translate, rotate, scale, pivot, **kwargs):
        """
        Builds the node into the scene according to parameters set in workbench.
        Parameters from __init__
        """
        transformNode = Group(name=name, parent=parent, translate=translate, rotate=rotate, scale=scale, pivot=pivot)
        name += 'Shape'
        if Workbench.modeIsStandalone:
            #throw an error
            pass
        else:
            #build the node into the scene
            if Workbench.modeIsMaya:
                self._buildMaya(name=name, parent=transformNode, **kwargs)
        
        if not Workbench.bench.hasNode(self):
            Workbench.bench.add(self)


class Group(Transform, Node):
    def __init__(self, wrapNode=None, name=None, parent=None, translate=[0,0,0], rotate=[0,0,0], scale=[1,1,1], pivot=[0,0,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param parent: parent new node to the specified transform node
        @param translate: list, initial XYZ translate values (ignored if wrapNode is used)
        @param rotate: list, initial XYZ rotate values (ignored if wrapNode is used)
        @param scale: list, initial XYZ scale values (ignored if wrapNode is used)
        @param pivot: list, initial XYZ coordinates for pivot point (ignored if wrapNode is used)
        @return: Group node object
        """
        #set default node name
        name = 'null' if name is None else name
        super(Group, self).__init__(wrapNode=wrapNode, name=name, parent=parent, translate=translate, rotate=rotate, scale=scale, pivot=pivot)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['transform']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['transform'] = cls 
    
    def _buildMaya(self, name, parent, translate, rotate, scale, pivot, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        if parent is None:
            newTransform = Workbench.cmds.createNode('transform', n=name, skipSelect=True)
        else:
            newTransform = Workbench.cmds.createNode('transform', n=name, parent=parent, skipSelect=True)
        self.wrapNode(newTransform)
        self.transform(translate=translate, rotate=rotate, scale=scale, pivot=pivot, worldSpace=True)
Group._registerClass()


class Joint(Transform, Node):
    def __init__(self, wrapNode=None, name=None, parent=None, translate=[0,0,0], rotate=[0,0,0], scale=[1,1,1], pivot=[0,0,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @return: Joint node object
        """
        #set default node name
        name = 'joint' if name is None else name
        super(Joint, self).__init__(wrapNode=wrapNode, name=name, parent=parent, translate=translate, rotate=rotate, scale=scale, pivot=pivot)
    
    def orient(self, value, relative=False):
        """
        Sets joint orient values for initial orientation without rotate values
        @param value: list, new joint orient values
        @param relative: bool, set orient values relative to the current value
        """
        if relative:
            value = misc.Vector(self.jointOrient[0]) + misc.Vector(value)
        self.jointOrient.set(value)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['joint']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['joint'] = cls
    
    def _buildMaya(self, name, parent, translate, rotate, scale, pivot, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        #NOTE: Add orients to init and _buildmaya? Or just as its own method?
        newJoint = Workbench.cmds.createNode('joint', n=name, skipSelect=True)
        self.wrapNode(newJoint)
        self.transform(translate=translate, rotate=rotate, scale=scale, pivot=pivot, worldSpace=True)
        if not parent is None:
            self.parent(parent)
Joint._registerClass()


class Cluster(Shape, Compound):
    def __init__(self, wrapNode=None, name=None, parent=None, components=None, translate=[0,0,0], rotate=[0,0,0], scale=[1,1,1], pivot=[0,0,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param parent: parent new node to the specified transform node
        @param components: node, component, or list of components to be affected
        @param translate: list, initial XYZ translate values (ignored if wrapNode is used)
        @param rotate: list, initial XYZ rotate values (ignored if wrapNode is used)
        @param scale: list, initial XYZ scale values (ignored if wrapNode is used)
        @param pivot: list, initial XYZ coordinates for pivot point (ignored if wrapNode is used)
        @return: Cluster compound object
        """
        #set default node name
        name = 'cluster' if name is None else name
        #Note that as additional integrations are added I may need to rethink this
        #In softimage at least clusters seem to be VERY different.
        #Possibly in those cases I would just have it build a joint instead. You can do this by setting self.__class__ = Joint
        super(Cluster, self).__init__(wrapNode=wrapNode, name=name, parent=parent, components=components, translate=translate, rotate=rotate, scale=scale, pivot=pivot)
    
    def addComponents(self, components):
        """
        Add components to be affected by this cluster
        @param components: components to be added
        @return: None
        """
        if Workbench.modeIsMaya:
            Workbench.cmds.sets(components, add=self.compoundParts[1])
    add=addComponents
    
    def removeComponents(self, components):
        """
        Remove components being affected by this cluster
        @param components: components to be removed
        @return: None
        """
        if Workbench.modeIsMaya:
            Workbench.cmds.sets(components, remove=self.listConnections(type='objectSet')[0])
    remove=removeComponents
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['clusterHandle', 'cluster']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['cluster'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['clusterHandle'] = cls
    
    def _buildMaya(self, name, parent, components, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        #create handle, object set, and cluster node
        newHandle = Workbench.cmds.createNode('clusterHandle', name=name, parent=parent, skipSelect=True)
        self.wrapNode(newHandle)
        objSet = Set(name=name+'Set', type='objectSet')
        newCluster = Workbench.cmds.createNode('cluster', name=name, skipSelect=True)
        self.wrapNode(newCluster)
        #connect cluster network
        self.message.connectTo(objSet.usedBy[0])
        handle.clusterTransforms[0].connectTo(self.clusterXforms)
        handle.transformNode.worldMatrix[0].connectTo(self.matrix)
        #add components to be affected by cluster
        self.addComponents(components)
Cluster._registerClass()


class ClusterPart(CompoundPart):
    """
    Class for wrapping cluster parts only. Do not instantiate directly.
    """
    def __init__(self, wrapNode=None, **kwargs):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @return: ClusterPart node object
        """
        if Workbench.modeIsMaya:
            if commands.nativeNodeType == 'clusterHandle':
                self._partSuffix = 'Shape'
            elif commands.nativeNodeType == 'cluster':
                self._partSuffix = 'Node'
        super(ClusterPart, self).__init__(wrapNode=wrapNode, **kwargs)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.compoundNodeTypeByMode['maya']['clusterHandle'] = cls
        nodeInfo.Conversion.compoundNodeTypeByMode['maya']['cluster'] = cls
ClusterPart._registerClass()


class Camera(Shape, Node):
    def __init__(self, wrapNode=None, name=None, parent=None, translate=[0,0,0], rotate=[0,0,0], scale=[1,1,1], pivot=[0,0,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param parent: parent new node to the specified transform node
        @param translate: list, initial XYZ translate values (ignored if wrapNode is used)
        @param rotate: list, initial XYZ rotate values (ignored if wrapNode is used)
        @param scale: list, initial XYZ scale values (ignored if wrapNode is used)
        @param pivot: list, initial XYZ coordinates for pivot point (ignored if wrapNode is used)
        @return: Camera node object
        """
        #set default node name
        name = 'camera' if name is None else name
        super(Camera, self).__init__(wrapNode=wrapNode, name=name, parent=parent, translate=translate, rotate=rotate, scale=scale, pivot=pivot)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['camera']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['camera'] = cls
    
    def _buildMaya(self, name, parent, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        @return: fullPathName of node to wrap
        """
        newCamera = Workbench.cmds.createNode('camera', n=name, parent=parent, skipSelect=True)
        self.wrapNode(newCamera)
Camera._registerClass()


class Curve(Shape, Node):
    def __init__(self, wrapNode=None, name=None, parent=None, type='line', points=[(0,0,0)], worldSpace=True, radius=1, degree=3, translate=[0,0,0], rotate=[0,0,0], scale=[1,1,1], pivot=[0,0,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param parent: parent new node to the specified transform node
        @param type: str, type of curve to create ('line', 'circle')
        @param points: list of tuples, list of coordinates at which to place curve points (for type line only)
        @param worldSpace: bool, determines whether the point coordinates are in world space. Does not affect transforms. (for type line only)
        @param radius: float, radius of nurbs circle (for type circle only)
        @param degree: int, degree of the new curve (default 3)
        @param translate: list, initial XYZ translate values (ignored if wrapNode is used)
        @param rotate: list, initial XYZ rotate values (ignored if wrapNode is used)
        @param scale: list, initial XYZ scale values (ignored if wrapNode is used)
        @param pivot: list, initial XYZ coordinates for pivot point (ignored if wrapNode is used)
        @return: Curve node object
        """
        #set default node name
        if name is None:
            name = 'curve' if type == 'line' else type
        super(Curve, self).__init__(wrapNode=wrapNode, name=name, parent=parent, type=type, points=points, worldSpace=worldSpace, radius=radius, degree=degree,
                                    translate=translate, rotate=rotate, scale=scale, pivot=pivot)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['nurbsCurve']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['nurbsCurve'] = cls
    
    def _buildMaya(self, name, parent, type, points, worldSpace, radius, degree,**kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        if type == 'line':
            newCurveTransform = Workbench.cmds.curve(parent=parent, name=name.replace('Shape',''), points=points, degree=degree, worldSpace=worldSpace)
        elif type == 'circle':
            newCurveTransform = Workbench.cmds.circle(name=name.replace('Shape',''), radius=radius, degree=degree)
            Workbench.cmds.parent(newCurveTransform, parent)
        newCurve = Workbench.cmds.listRelatives(newCurveTransform, shapes=True)[0]
        self.wrapNode(newCurve)
        self.parent(parent)
Curve._registerClass()


class NurbsSurface(Shape, Node):
    def __init__(self, wrapNode=None, name=None, parent=None, type='plane', axis=[0,1,0], degree=1, length=None, width=1, patchesU=1, patchesV=1,
                 translate=[0,0,0], rotate=[0,0,0], scale=[1,1,1], pivot=[0,0,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param parent: parent new node to the specified transform node
        @param type: str, type of nurb primitive to create ('plane', 'sphere', 'cone', 'cylinder', 'torus')
        @param axis: axis for the primitive's normals to face
        @param degree: int, degree of the new surface (default 1)
        @param length: float, length of the plane (for type 'plane' only)
        @param width: float, width of the plane (for type 'plane' only)
        @param patchesU: number of patches along the U (width) axis (for type 'plane' only)
        @param patchesV: number of patches along the V (length) axis (for type 'plane' only)
        @param translate: list, initial XYZ translate values (ignored if wrapNode is used)
        @param rotate: list, initial XYZ rotate values (ignored if wrapNode is used)
        @param scale: list, initial XYZ scale values (ignored if wrapNode is used)
        @param pivot: list, initial XYZ coordinates for pivot point (ignored if wrapNode is used)
        @return: NurbsSurface node object
        """
        #set default node name
        if name is None:
            name = 'surface'+type.title()
        super(NurbsSurface, self).__init__(wrapNode=wrapNode, name=name, parent=parent, axis=axis, degree=degree, length=length, width=width,
                                           patchesU=patchesU, patchesV=patchesV, translate=translate, rotate=rotate, scale=scale, pivot=pivot)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['nurbsSurface']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['nurbsSurface'] = cls
    
    def _buildMaya(self, name, parent, axis, degree, length, width, patchesU, patchesV, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        @return: fullPathName of node to wrap
        """
        if type == 'plane':
            #length is absolute value. Must convert to ratio of width
            lengthRatio = float(length) / width
            newNurbsTransform = Workbench.cmds.nurbsPlane(parent=parent, name=name.replace('Shape',''), axis=axis, degree=degree,
                                                          lengthRatio=lengthRatio, width=width, patchesU=patchesU, patchesV=patchesV)
        elif type == 'sphere':
            newNurbsTransform = Workbench.cmds.sphere(parent=parent, name=name.replace('Shape',''), axis=axis, degree=degree)
        elif type == 'cone':
            newNurbsTransform = Workbench.cmds.cone(parent=parent, name=name.replace('Shape',''), axis=axis, degree=degree)
        elif type == 'cylinder':
            newNurbsTransform = Workbench.cmds.cylinder(parent=parent, name=name.replace('Shape',''), axis=axis, degree=degree)
        elif type == 'torus':
            newNurbsTransform = Workbench.cmds.torus(parent=parent, name=name.replace('Shape',''), axis=axis, degree=degree)
        newNurbs = Workbench.cmds.listRelatives(newNurbsTransform, shapes=True)[0]
        self.wrapNode(newNurbs)
        self.parent(parent)
NurbsSurface._registerClass()

Nurbs = NurbsSurface
Surface = NurbsSurface


class Mesh(Shape, Node):
    def __init__(self, wrapNode=None, name=None, parent=None, type='plane', translate=[0,0,0], rotate=[0,0,0], scale=[1,1,1], pivot=[0,0,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param parent: parent new node to the specified transform node
        @param type: str, type of primitive to create
        @param translate: list, initial XYZ translate values (ignored if wrapNode is used)
        @param rotate: list, initial XYZ rotate values (ignored if wrapNode is used)
        @param scale: list, initial XYZ scale values (ignored if wrapNode is used)
        @param pivot: list, initial XYZ coordinates for pivot point (ignored if wrapNode is used)
        @return: Mesh node object
        """
        #set default node name
        if name is None:
            name = 'poly'+type.title()
        super(Mesh, self).__init__(wrapNode=wrapNode, name=name, parent=parent, type=type, translate=translate, rotate=rotate, scale=scale, pivot=pivot)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['mesh']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['mesh'] = cls
    
    def _buildMaya(self, name, partypeitive, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        @return: fullPathName of node to wrap
        """
        if type == 'plane':
            newMeshTransform = Workbench.cmds.polyPlane(parent=parent, name=name.replace('Shape',''))
        elif type == 'sphere':
            newMeshTransform = Workbench.cmds.polySphere(parent=parent, name=name.replace('Shape',''))
        elif type == 'cube':
            newMeshTransform = Workbench.cmds.polyCube(parent=parent, name=name.replace('Shape',''))
        elif type == 'cylinder':
            newMeshTransform = Workbench.cmds.polyCylinder(parent=parent, name=name.replace('Shape',''))
        elif type == 'cone':
            newMeshTransform = Workbench.cmds.polyCone(parent=parent, name=name.replace('Shape',''))
        elif type == 'torus':
            newMeshTransform = Workbench.cmds.polyTorus(parent=parent, name=name.replace('Shape',''))
        elif type == 'pyramid':
            newMeshTransform = Workbench.cmds.polyPyramid(parent=parent, name=name.replace('Shape',''))
        elif type == 'pipe':
            newMeshTransform = Workbench.cmds.polyPipe(parent=parent, name=name.replace('Shape',''))
        newMesh = Workbench.cmds.listRelatives(newMeshTransform, shapes=True)[0]
        self.wrapNode(newMesh)
        self.parent(parent)
Mesh._registerClass()

Geo = Mesh
Geometry = Mesh
Poly = Mesh


class Locator(Shape, Node):
    def __init__(self, wrapNode=None, name=None, parent=None, translate=[0,0,0], rotate=[0,0,0], scale=[1,1,1], pivot=[0,0,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param parent: parent new node to the specified transform node
        @param translate: list, initial XYZ translate values (ignored if wrapNode is used)
        @param rotate: list, initial XYZ rotate values (ignored if wrapNode is used)
        @param scale: list, initial XYZ scale values (ignored if wrapNode is used)
        @param pivot: list, initial XYZ coordinates for pivot point (ignored if wrapNode is used)
        @return: Locator node object
        """
        #set default node name
        name = 'locator' if name is None else name
        super(Locator, self).__init__(wrapNode=wrapNode, name=name, parent=parent, translate=translate, rotate=rotate, scale=scale, pivot=pivot)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['locator']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['locator'] = cls
    
    def _buildMaya(self, name, parent, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        newLoc = Workbench.cmds.createNode('locator', name=name, parent=parent, skipSelect=True)
        self.wrapNode(newLoc)
Locator._registerClass()


class Set(Node):
    def __init__(self, wrapNode=None, name=None, type='objectSet'):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param type: type of set to create
        @return: Blendshape node object
        """
        #set default node name
        name = type if name is None else name
        super(Set, self).__init__(wrapNode=wrapNode, name=name, type=type)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['objectSet']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['objectSet'] = cls
    
    def _buildMaya(self, name, type, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        newSet = Workbench.shadingNode(type, name=name, asUtility=True, skipSelect=True)
        self.wrapNode(newSet)
Set._registerClass()


class IkSolver(Transform, Node):
    def __init__(self, wrapNode=None, name=None, type='rotatePlane', startJnt=None, endJnt=None, sticky=True, curve=None, createCurve=True,
                 parentCurve=True, simplifyCurve=True, numSpans=1):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param type: str, type of IkSolver ('rotatePlane, spring, singleChain, spline')
        @param startJnt: joint object at the start of the IK chain
        @param endJnt: joint object at the end of the IK chain; effector and handle are created at this point
        @param sticky: a sticky IK handle will attempt to keep its endJnt in the same place when the rest of the skeleton is being manipulated
        @param curve: curve object to use for IK Spline handle
        @param createCurve: create a new curve for IK Spline Handle (ignored if curve has value)
        @param parentCurve: automatically parent IK Spline curve under joint chain
        @param simplifyCurve: automatically simplify IK Spline curve
        @param numSpans: number of spans for new IK Spline curve (ignored if curve has value)
        @return: IkSolver compound object
        """
        if name is None:
            if type == 'rotatePlane':
                name = 'ikRP'
            elif type == 'spring':
                name = 'ikSpring'
            elif type == 'singleChain':
                name = 'ikSC'
            elif type == 'spline':
                name = 'ikSpline'
        super(IkSolver, self).__init__(wrapNode=wrapNode, name=name, type=type, startJnt=startJnt, endJnt=endJnt, sticky=sticky, curve=curve,
                                       createCurve=createCurve, parentCurve=parentCurve, simplifyCurve=simplifyCurve, numSpans=numSpans)
    
    def wrapNode(self, node):
        """
        wrap node according to appropriate CompoundPart subclass
        @param node: native node to be wrapped
        """
        #if we're in maya and it's an effector that has a handle, we want to wrap the handle instead
        if Workbench.modeIsMaya and commands.nativeNodeType(node) == 'ikEffector':
            handle = Workbench.cmds.listConnections(node+'.handlePath[0]')
            if not handle is None:
                super(IkSolver, self).wrapNode(handle)
                return
        #if we didn't return then there's no handle or we're not in maya, so just wrap up the effector
        super(IkSolver, self).wrapNode(node)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['ikHandle', 'ikEffector']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['ikHandle'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['ikEffector'] = cls
    
    def _buildMaya(self, name, type, startJnt, endJnt, sticky, curve, createCurve, parentCurve, simplifyCurve, numSpans, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        @return: fullPathName of node to wrap
        """
        type = type.lower()
        #if no start or end jnt passed, get them from the selection
        if startJnt is None or endJnt is None:
            selection = commands.getSelection()
            if len(selection) < 2 or not isinstance(selection[0], Joint) or not isinstance(selection[1], Joint):
                commands.error("startJnt and endJnt must be passed or two joints must be selected.")
            else:
                startJnt = selection[0]
                endJnt = selection[1]
        #set sticky string from boolean
        if sticky:
            sticky = 'sticky'
        else:
            sticky = 'off'
        #prepare native solver strings
        solverType = {'rotateplane':'ikRPsolver', 'singlechain':'ikSCsolver', 'spline':'ikSplineSolver', 'spring':'ikSpringSolver'}
        #spring solvers must be 'enabled' first using the mel command
        if type == 'spring':
            from maya.mel import eval as melEval
            melEval('ikSpringSolver;')
        elif type == 'spline':
            #curve parameter can't be None - if it's passed it must be a curve node.
            if not curve is None:
                newHandle = Workbench.cmds.ikHandle(name=name+'Handle', solver=solverType[type], startJoint=startJnt, endEffector=endJnt, sticky=sticky,
                                                    curve=curve, createCurve=createCurve, parentCurve=parentCurve, simplifyCurve=simplifyCurve, numSpans=numSpans)[0]
        #and now all the other ik handles
        else:
            newHandle = Workbench.cmds.ikHandle(name=name+'Handle', solver=solverType[type], startJoint=startJnt, endEffector=endJnt, sticky=sticky,
                                                createCurve=createCurve, parentCurve=parentCurve, simplifyCurve=simplifyCurve, numSpans=numSpans)[0]
        #rename the effector 'cause "effector73" is a pretty ugly name - not a workbench node type so use cmds
        effector = Workbench.cmds.listConnections(self.endEffector)
        Workbench.cmds.rename(effector, name+'Effector')
        #wrap handle
        self.wrapNode(newHandle)
        #get curve if ik type is spline and a curve was created or passed
        try:
            self.curve = self.inCurve.listConnections()[0].node
        except AttributeError:
            pass
IkSolver._registerClass()

IkHandle = IkSolver


class Skin(Node):
    def __init__(self, wrapNode=None, name=None, geometry=None, joints=None, maxInfluences=None, type='heatmap'):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param geometry: object(s) to be deformed (ignored if wrapNode is used)
        @param joints: joint(s) to use as influences (ignored if wrapNode is used)
        @param maxInfluences: int, maximum number of joint influences per vertex (ignored if wrapNode is used)
        @return: Skin node object
        """
        #set default node name
        name = 'skin' if name is None else name
        super(Skin, self).__init__(wrapNode=wrapNode, name=name, geometry=geometry, joints=joints, maxInfluences=maxInfluences, type=type)
    
    def addGeometry(self, geometry):
        """
        Add geometry to be deformed by this skin node
        @param geometry: geometry to be added to this deformer
        @return: None
        """
        pass
    
    def addJoints(self, joints, lockWeights=False):
        """
        Add joints to act as influences for this skin node
        @param joints: joints to be added as influences for this deformer
        @return: None
        """
        pass
    
    def removeGeometry(self, geometry):
        """
        Remove geometry from this skin node
        @param geometry: geometry to be removed from this deformer
        @return: None
        """
        pass
    
    def removeJoints(self, joints):
        """
        Remove joints as influences for this skin node
        @param joints: joints to be removed as influences for this deformer
        @return: None
        """
        pass
    
    def unbind(self):
        """
        Remove all geometry being deformed from this skin node
        @return: None
        """
        pass
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['']}
        nodeInfo.Conversion.nodeTypeByMode['maya'][''] = cls
    
    def _buildMaya(self, name, geometry, joints, maxInfluences, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        @return: fullPathName of node to wrap
        """
        #for now options are: heatmap, closest points, advanced
        #advanced, if version is 2017 update 3+ ONLY, is 1 influence not maintain, the tension deformer and then mc.BakeDeformerTool() 
        #with a warning that the last step is to be done manually)
        pass
Skin._registerClass()


class BlendShape(Node):
    def __init__(self, wrapNode=None, name=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @return: Blendshape node object
        """
        #set default node name
        name = 'blendShape' if name is None else name
        super(BlendShape, self).__init__(wrapNode=wrapNode, name=name)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['']}
        nodeInfo.Conversion.nodeTypeByMode['maya'][''] = cls
    
    def _buildMaya(self, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        @return: fullPathName of node to wrap
        """
        #return fullPathName
        pass
BlendShape._registerClass()


class Animation(Node):
    def __init__(self, wrapNode=None, name=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @return: Animation node object
        """
        #set default node name
        name = 'animCurve' if name is None else name
        super(Animation, self).__init__(wrapNode=wrapNode, name=name)
    
    def setInfinity(preInfinity=None, postInfinity=None):
        """
        set how to determine values before the first and after the last keyframes
        @param preInfinity: str, curve type before the first keyframe. "constant", "linear", "cycle", "cycleRelative", "oscillate"
        @param postInfinity: str, curve type after the last keyframe. "constant", "linear", "cycle", "cycleRelative", "oscillate"
        @return: None
        """
        if Workbench.modeIsMaya:
            if not preInfinity is None:
                self.preInfinity.set(preInfinity)
            if not postInfinity is None:
                self.postInfinity.set(postInfinity)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['']}
        nodeInfo.Conversion.nodeTypeByMode['maya'][''] = cls
    
    def _buildMaya(self, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        @return: fullPathName of node to wrap
        """
        #return fullPathName
        pass
Animation._registerClass()


class PointOnCurve(Node):
    def __init__(self, wrapNode=None, name=None, curve=None, position=0, nearestTo=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param curve: curve from which to get info
        @param postion: float (0-1) or attribute, point position along curve from which to get information (ignored if nearestTo is passed)
        @param nearestTo: list or coordinates or node from which to derive the nearest point on the curve
        @return: PointOnCurve node object
        """
        #set default node name
        if name is None:
            name is 'pointOnCurveInfo' if nearestTo is None else 'nearestPointOnCurve'
        super(PointOnCurve, self).__init__(wrapNode=wrapNode, name=name, curve=curve, position=position, nearestTo=nearestTo)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['nearestPointOnCurve', 'pointOnCurveInfo']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['nearestPointOnCurve'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['pointOnCurveInfo'] = cls

    def _buildMaya(self, name, curve, position, nearestTo, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        #if nearestTo isn't passed, create pointOnCurveInfo
        if nearestTo is None:
            newPointOn = Workbench.cmds.shadingNode('pointOnCurveInfo', name=name, asUtility=True, skipSelect=True)
            self.wrapNode(newPointOn)
            if isinstance(position, Attribute):
                position.connectTo(self.parameter)
            else:
                self.parameter.set(postition)
        #otherwise create nearestPointOnCurve
        else:
            newPointOn = Workbench.cmds.shadingNode('nearestPointOnCurve', name=name, asUtility=True, skipSelect=True)
            self.wrapNode(newPointOn)
            if isinstance(nearestTo, Transform):
                nearestTo.translate.connectTo(self.inPosition)
            else:
                self.inPosition.set(nearestTo)
        #if curve was passed, get shape from transform and connect to inputCurve
        if not curve is None:
            if isinstance(curve, Transform):
                curve = curve.shapeNodes[0]
            curve.worldSpace[0].connectTo(self.inputCurve)
PointOnCurve._registerClass()


class PointOnSurface(Node):
    def __init__(self, wrapNode=None, name=None, surface=None, positionU=0.5, positionV=0.5, nearestTo=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param surface: surface from which to get info
        @param postionU: float (0-1) or attribute, point position along U axis of surface from which to get information (ignored if nearestTo is passed)
        @param postionV: float (0-1) or attribute, point position along U axis of surface from which to get information (ignored if nearestTo is passed)
        @param nearestTo: list or coordinates or node from which to derive the nearest point on the surface
        @return: PointOnSurface node object
        """
        #set default node name
        if name is None:
            name is 'pointOnSurfaceInfo' if nearestTo is None else 'nearestPointOnSurface'
        super(PointOnSurface, self).__init__(wrapNode=wrapNode, name=name, surface=surface, positionU=positionU, positionV=positionV, nearestTo=nearestTo)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['closestPointOnSurface', 'pointOnSurfaceInfo']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['closestPointOnSurface'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['pointOnSurfaceInfo'] = cls

    def _buildMaya(self, name, surface, positionU, positionV, nearestTo, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        #if nearestTo isn't passed, create pointOnSurfaceInfo
        if nearestTo is None:
            newPointOn = Workbench.cmds.shadingNode('pointOnSurfaceInfo', name=name, asUtility=True, skipSelect=True)
            self.wrapNode(newPointOn)
            #connect or set parameter U and V
            if isinstance(positionU, Attribute):
                positionU.connectTo(self.parameterU)
            else:
                self.parameterU.set(postitionU)
            
            if isinstance(positionV, Attribute):
                positionV.connectTo(self.parameterU)
            else:
                self.parameterV.set(postitionV)
        #otherwise create closestPointOnSurface
        else:
            newPointOn = Workbench.cmds.shadingNode('closestPointOnSurface', name=name, asUtility=True, skipSelect=True)
            self.wrapNode(newPointOn)
            #connect or set inPosition
            if isinstance(nearestTo, Transform):
                nearestTo.translate.connectTo(self.inPosition)
            else:
                self.inPosition.set(nearestTo)
        #if surface was passed, get shape from transform and connect to inputSurface
        if not surface is None:
            if isinstance(surface, Transform):
                surface = surface.shapeNodes[0]
            surface.worldSpace[0].connectTo(self.inputSurface)
PointOnSurface._registerClass()

PointOnNurbs = PointOnSurface


class PointOnMesh(Node):
    def __init__(self, wrapNode=None, name=None, mesh=None, nearestTo=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param mesh: mesh from which to get info
        @param nearestTo: list or coordinates or node from which to derive the nearest point on the surface
        @return: PointOnMesh node object
        """
        #set default node name
        name = 'nearestPointOnMesh' if name is None else name
        super(PointOnMesh, self).__init__(wrapNode=wrapNode, name=name)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['closestPointOnMesh']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['closestPointOnMesh'] = cls

    def _buildMaya(self, name, mesh, nearestTo, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        #create closestPointOnMesh
        newPointOn = Workbench.cmds.shadingNode('closestPointOnMesh', name=name, asUtility=True, skipSelect=True)
        self.wrapNode(newPointOn)
        #connect or set inPosition
        if isinstance(nearestTo, Transform):
            nearestTo.translate.connectTo(self.inPosition)
        else:
            self.inPosition.set(nearestTo)
        #if mesh was passed, get shape from transform and connect to inputMesh
        if not mesh is None:
            if isinstance(mesh, Transform):
                mesh = mesh.shapeNodes[0]
            mesh.worldMesh[0].connectTo(self.inMesh)
PointOnMesh._registerClass()

PointOnPoly = PointOnMesh
PointOnGeo = PointOnMesh


class Constraint(Node):
    def __init__(self, name=None, wrapNode=None, node=None, parent=None, type='parent', weight=1, maintainOffset=False, axis='xyz', parentOrientAxis='xyz',
                 parentPointAxis='xyz', aimVector=[1,0,0], upVector=[0,1,0], worldUpType='vector', worldUpObject=None, worldUpVector=[0,1,0]):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param node: node object to be constrained
        @param parent: parent node for the constraint
        @param name: bool or str, defines the name for a new node
        @param type: str, type of constraint ('parent', 'orient', 'point', 'scale', 'aim', 'poleVector')
        @param weight: float 0-1, amount of influence the parent has on the constraint
        @param maintainOffset: bool, maintain the existing transforms relative to constraint target
        @param axis: str or list, axes on which to make the constraint (e.g. 'xz' or ['x','z']; ignored if parentConstraint) 
        @param parentOrientAxis: str or list, axes for the orient component (for parent constraint only)
        @param parentPointAxis: str or list, axes for the point component (for parent constraint only)
        @param aimVector: list, local vector coordinates that points towards the target (for aim constraint only)
        @param upVector: list, local vector coordinates that aligns with the world up (for aim constraint only)
        @param worldUpType: str, type of world up computation ('scene', 'object', 'objectRotation', 'vector', 'none')(for aim constraint only)
        @param worldUpObject: node object to use for worldUpType 'object' and 'objectRotation' (for aim constraint only)
        @param worldUpVector: list, world vector coordinates that up bector should align with (for aim constraint only)
        @return: Constraint node object
        """
        #set default node name
        name = type+'Constraint' if name is None else name
            
        super(Constraint, self).__init__(wrapNode=wrapNode, name=name, node=node, parent=parent, weight=weight, type=type, maintainOffset=maintainOffset,
                                         axis=axis, parentOrientAxis=parentOrientAxis, parentPointAxis=parentPointAxis, aimVector=aimVector, upVector=upVector,
                                         worldUpType=worldUpType, worldUpObject=worldUpObject, worldUpVector=worldUpVector)
    
    def removeTarget(self, node):
        """
        Removes target from the constraint
        """
        if Workbench.modeIsMaya:
            if commands.nativeNodeType(self) == 'parentConstraint':
                Workbench.cmds.parentConstraint(self, remove=node)
            elif commands.nativeNodeType(self) == 'orientConstraint':
                Workbench.cmds.orientConstraint(self, remove=node)
            elif commands.nativeNodeType(self) == 'pointConstraint':
                Workbench.cmds.pointConstraint(self, remove=node)
            elif commands.nativeNodeType(self) == 'scaleConstraint':
                Workbench.cmds.scaleConstraint(self, remove=node)
            elif commands.nativeNodeType(self) == 'aimConstraint':
                Workbench.cmds.aimConstraint(self, remove=node)
            elif commands.nativeNodeType(self) == 'poleVectorConstraint':
                Workbench.cmds.poleVectorConstraint(self, remove=node)
    
    def listParents(self):
        """
        List all nodes affecting this constraint
        """
        if Workbench.modeIsMaya:
            if commands.nativeNodeType(self) == 'parentConstraint':
                return commands.wrapNode(Workbench.cmds.parentConstraint(self, query=True, targetList=True))
            elif commands.nativeNodeType(self) == 'orientConstraint':
                return commands.wrapNode(Workbench.cmds.orientConstraint(self, query=True, targetList=True))
            elif commands.nativeNodeType(self) == 'pointConstraint':
                return commands.wrapNode(Workbench.cmds.pointConstraint(self, query=True, targetList=True))
            elif commands.nativeNodeType(self) == 'scaleConstraint':
                return commands.wrapNode(Workbench.cmds.scaleConstraint(self, query=True, targetList=True))
            elif commands.nativeNodeType(self) == 'aimConstraint':
                return commands.wrapNode(Workbench.cmds.aimConstraint(self, query=True, targetList=True))
            elif commands.nativeNodeType(self) == 'poleVectorConstraint':
                return commands.wrapNode(Workbench.cmds.poleVectorConstraint(self, query=True, targetList=True))
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['parentConstraint', 'orientConstraint', 'pointConstraint', 'scaleConstraint',
                                                                     'aimConstraint', 'poleVectorConstraint']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['parentConstraint'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['orientConstraint'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['pointConstraint'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['scaleConstraint'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['aimConstraint'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['poleVectorConstraint'] = cls
    
    def _buildMaya(self, name, node, parent, weight, type, maintainOffset, axis, parentOrientAxis, parentPointAxis,
                   aimVector, upVector, worldUpType, worldUpObject, worldUpVector, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        #if no node or parent passed, get them from the selection
        if node is None or parent is None:
            selection = commands.getSelection()
            if len(selection) < 2 or not isinstance(selection[0], Transform) or not isinstance(selection[1], Transform):
                commands.error("node and parent must be passed or two transformable nodes must be selected.")
            else:
                parent = selection[0]
                node = selection[1]
        #make sure axes lists are valid (and are lists)
        axis = nodeInfo.Conversion.confirmValidAxis(axis)
        parentOrientAxis = nodeInfo.Conversion.confirmValidAxis(parentOrientAxis)
        parentPointAxis = nodeInfo.Conversion.confirmValidAxis(parentPointAxis)
        if axis is None or parentOrientAxis is None or parentPointAxis is None:
            commands.error("Axes must be combinations of x,y,z only!")
        #maya orient axes are opt-out so we need the reverse list
        skipAxis = []
        skipRotate=[]
        skipTranslate=[]
        for ax in 'xyz':
            if not ax in axis:
                skipAxis.append(ax)
            if not ax in parentOrientAxis:
                skipRotate.append(ax)
            if not ax in parentPointAxis:
                skipTranslate.append(ax)
        #actually make the constraints
        if type == 'parent' or type == 'parentConstraint':
            newConstraint = Workbench.cmds.parentConstraint([parent, node], name=name, weight=weight, maintainOffset=maintainOffset,
                                                            skipRotate=skipRotate, skipTranslate=skipTranslate)
        elif type == 'orient' or type == 'orientConstraint':
            newConstraint = Workbench.cmds.orientConstraint([parent, node], name=name, weight=weight, maintainOffset=maintainOffset, skip=skipAxis)
        elif type == 'point' or type == 'pointConstraint':
            newConstraint = Workbench.cmds.pointConstraint([parent, node], name=name, weight=weight, maintainOffset=maintainOffset, skip=skipAxis)
        elif type == 'scale' or type == 'scaleConstraint':
            newConstraint = Workbench.cmds.scaleConstraint([parent, node], name=name, weight=weight, maintainOffset=maintainOffset, skip=skipAxis)
        elif type == 'aim' or type == 'aimConstraint':
            newConstraint = Workbench.cmds.aimConstraint([parent, node], name=name, weight=weight, maintainOffset=maintainOffset, skip=skipAxis,
                                                         aimVector=aimVector, upVector=upVector, worldUpType=worldUpType.lower(), worldUpObject=worldUpObject,
                                                         worldUpVector=worldUpVector)
        elif type == 'poleVector' or type == 'poleVectorConstraint':
            newConstraint = Workbench.cmds.poleVectorConstraint([parent, node], name=name, weight=weight)
        self.wrapNode(newConstraint)
Constraint._registerClass()


class BlendAttributes(Node):
    def __init__(self, wrapNode=None, name=None, input=None, output=None, blendControl=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param input: list, attributes to be blended
        @param output:  attribute to receive output
        @param blendControl: attribute to control the blending value
        @return: BlendAttributes node object
        """
        #set default node name
        name = 'blendAttrs' if name is None else name
        super(BlendAttributes, self).__init__(wrapNode=wrapNode, name=name, input=input, output=output, blendControl=blendControl)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['blendColors', 'blendTwoAttr']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['blendColors'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['blendTwoAttr'] = cls
    
    def _buildMaya(self, name, input, output, blendControl, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        #I'll check which node to make, and how to connect attrs
        blendType = 'blendTwoAttr'
        inputType = '1D'
        outputType = '1D'
        #3D input or output can't be done with blendTwoAttr - note that for now I am only checking the first input. I'm also not currently accepting straight values for inputs
        if not input is None and commands.makeList(input)[0].type is misc.Vector:
            inputType = '3D'
            blendType = 'blendColors'
        if not output is None and commands.makeList(output)[0].type is misc.Vector:
            outputType = '3D'
            blendType = 'blendColors'
        #make the node
        if blendType == 'blendColors':
            newBlend = Workbench.cmds.shadingNode('blendColors', name=name, asUtility=True, skipSelect=True)
        elif blendType == 'blendTwoAttr':
            newBlend = Workbench.cmds.shadingNode('blendTwoAttr', name=name, asUtility=True, skipSelect=True)
        #wrap and connect inputs
        self.wrapNode(newBlend)
        if not input is None:
            for n, input in enumerate(commands.makeList(input)):
                if inputType == '3D' and blendType == 'blendTwoAttr':
                    input.connectTo(self.input)
                elif inputType == '1D' and blendType == 'blendTwoAttr':
                    input.connectTo(self.input[n])
                #blendColors is meant to use colours, so the inputs are named as such. What's more there's only two.
                elif inputType == '3D' and blendType == 'blendColors':
                    if n == 0:
                        input.connectTo(self.color1)
                    if n == 1:
                        input.connectTo(self.color2)
                    else:
                        commands.warning("Too many inputs. First two connected only.")
                elif blendType == 'blendColors':
                    if n == 0:
                        input.connectTo(self.color1R)
                    if n == 1:
                        input.connectTo(self.color2R)
                    else:
                        commands.warning("Too many inputs. First two connected only.")
        #connect outputs
        if not output is None:
            for n, output in enumerate(commands.makeList(output)):
                #blend colours 1D output isn't index based - it's color based.
                if outputType == '1D' and blendType == 'blendColors':
                    self.outputR.connectTo(output)
                #connect any other output types
                else:
                    self.output.connectTo(output)
        #finally connect the blender control... which has a different name on each blender node.
        if not blendControl is None:
            if blendType == 'blendColors':
                blendControl.connectTo(self.blender)
            else:
                blendControl.connectTo(self.attributesBlender)
BlendAttributes._registerClass()


class Condition(Node):
    def __init__(self, wrapNode=None, name=None, type='equal', firstTerm=0, secondTerm=0, trueValue=[0,0,0], falseValue=[1,1,1], output=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param type: str, type of condition ('equal', 'notEqual', 'greater', 'greaterEqual', 'less', 'lessEqual')
        @param firstTerm: float or attribute object to which the second term will be compared
        @param secondTerm: float or attribute object to compare to the first term
        @param trueValue: list or 3D attribute to be output if condition is true
        @param falseValue: list or 3D attribute to be output if condition is false
        @param output: attribute to which the value should be outputted
        @return: Condition node object
        """
        #set default node name
        name = 'condition' if name is None else name
        super(Condition, self).__init__(wrapNode=wrapNode, name=name, type=type, firstTerm=firstTerm, secondTerm=secondTerm,
                                        trueValue=trueValue, falseValue=falseValue, output=output)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['condition']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['condition'] = cls
    
    def _buildMaya(self, name, type, firstTerm, secondTerm, trueValue, falseValue, output, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        typeEnum = {'equal':0, 'notequal':1, 'greater':2, 'greaterequal':3, 'less':4, 'lessequal':5}
        newCondition = Workbench.cmds.shadingNode('condition', name=name, asUtility=True, skipSelect=True)
        self.wrapNode(newCondition)
        self.operation.set(typeEnum[type.lower()])
        if isinstance(firstTerm, Attribute):
            firstTerm.connectTo(self.firstTerm)
        else:
            self.firstTerm.set(firstTerm)
        if isinstance(secondTerm, Attribute):
            secondTerm.connectTo(self.secondTerm)
        else:
            self.secondTerm.set(secondTerm)
        if isinstance(trueValue, Attribute):
            if any(trueValue.type is attrType for attrType in [misc.Vector, list]):
                trueValue.connectTo(self.colorIfTrue)
            else:
                trueValue.connectTo(self.colorIfTrueR)
        else:
            self.colorIfTrue.set(trueValue)
        if isinstance(falseValue, Attribute):
            if any(falseValue.type is attrType for attrType in [misc.Vector, list]):
                falseValue.connectTo(self.colorIfFalse)
            else:
                falseValue.connectTo(self.colorIfFalseR)
        else:
            self.colorIfFalse.set(falseValue)
        if not output is None:
            if any(output.type is attrType for attrType in [misc.Vector, list]):
                self.outColor.connectTo(output)
            else:
                self.outColorR.connectTo(output)
Condition._registerClass()


class AddSubtract(Node):
    def __init__(self, wrapNode=None, name=None, type='add', input=None, output=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param type: str, type of operation ('add', 'subtract', 'average')
        @param input: list, attributes to be added/subtracted
        @param output: attribute to receive output
        @return: Add node object
        """
        #set default node name
        name = type if name is None else name
        super(AddSubtract, self).__init__(wrapNode=wrapNode, name=name, type=type, input=input, output=output)
    
    @classmethod
    def _registerClass(cls):
        #note: addDoubleLinear can be wrapped by this class but cannot be constructed with it
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['plusMinusAverage', 'addDoubleLinear']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['plusMinusAverage'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['addDoubleLinear'] = cls
    
    def _buildMaya(self, name, type, input, output, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        typeEnum = {'add':1, 'subtract':2, 'average':3}
        newAdd = Workbench.cmds.shadingNode('plusMinusAverage', name=name, asUtility=True, skipSelect=True)
        #wrap and connect inputs
        self.wrapNode(newAdd)
        if not input is None:
            for n, input in enumerate(commands.makeList(input)):
                #different input attrs for 1D and 3D dealies
                if commands.makeList(input)[0].type is misc.Vector:
                    input.connectTo(self.input3D[n])
                    inputType='3D'
                else:
                    input.connectTo(self.input1D[n])
                    inputType='1D'
        #connect outputs
        if not output is None:
            for n, output in enumerate(commands.makeList(output)):
                #different output attrs for 1D and 3D dealies - also for 3D input vs 1D input
                if commands.makeList(output)[0].type is misc.Vector:
                    self.output3D.connectTo(output)
                elif inputType == '1D':
                    self.output1D.connectTo(output)
                elif inputType == '3D':
                    self.output3Dx.connectTo(output)
        #set type
        self.operation.set(typeEnum[type.lower()])
AddSubtract._registerClass()

Add = AddSubtract
Subtract = AddSubtract
Average = AddSubtract


class MultiplyDivide(Node):
    def __init__(self, wrapNode=None, name=None, type='multiply', input=None, output=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param type: str, type of operation ('multiply', 'divide', 'power')
        @param input: list, attributes to be multiplied/divided
        @param output: attribute to receive output
        @return: Multiply node object
        """
        #set default node name
        name = type if name is None else name
        super(MultiplyDivide, self).__init__(wrapNode=wrapNode, name=name, type=type, input=input, output=output)
    
    @classmethod
    def _registerClass(cls):
        #note: multDoubleLinear can be wrapped by this class but cannot be constructed with it
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['multiplyDivide', 'multDoubleLinear']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['multiplyDivide'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['multDoubleLinear'] = cls
    
    def _buildMaya(self, type, input, output, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        typeEnum = {'multiply':1, 'divide':2, 'power':3}
        newMult = Workbench.cmds.shadingNode('multiplyDivide', name=name, asUtility=True, skipSelect=True)
        #wrap and connect inputs
        self.wrapNode(newMult)
        if not input is None:
            for n, input in enumerate(commands.makeList(input)):
                #different input attrs for 1D and 3D dealies. Also only 2 inputs.
                if commands.makeList(input)[0].type is misc.Vector:
                    if n == 0:
                        input.connectTo(self.input1)
                    elif n == 1:
                        input.connectTo(self.input)
                    else:
                        commands.warning("Too many inputs. First two connected only.")
                else:
                    if n == 0:
                        input.connectTo(self.input1X)
                    elif n == 1:
                        input.connectTo(self.input2X)
                    else:
                        commands.warning("Too many inputs. First two connected only.")
        #connect outputs
        if not output is None:
            for n, output in enumerate(commands.makeList(output)):
                #different output attrs for 1D and 3D dealies
                if commands.makeList(output)[0].type is misc.Vector:
                    self.output.connectTo(output)
                else:
                    self.output.connectTo(outputX)
        #set type
        self.operation.set(typeEnum[type.lower()])
MultiplyDivide._registerClass()

Multiply = MultiplyDivide
Divide = MultiplyDivide
Power = MultiplyDivide


class Reverse(Node):
    def __init__(self, wrapNode=None, name=None, input=None, output=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param input: attribute object(s) to be reversed
        @param output: attribute to receive output
        @return: Multiply node object
        """
        #set default node name
        name = 'reverse' if name is None else name
        super(Reverse, self).__init__(wrapNode=wrapNode, name=name, input=input, output=output)
    
    @classmethod
    def _registerClass(cls):
        #note: multDoubleLinear can be wrapped by this class but cannot be constructed with it
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['reverse']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['reverse'] = cls
    
    def _buildMaya(self, type, input, output, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        newReverse = Workbench.cmds.shadingNode('reverse', name=name, asUtility=True, skipSelect=True)
        #wrap and connect inputs
        self.wrapNode(newReverse)
        if not input is None:
            for n, input in enumerate(commands.makeList(input)):
                #different input attrs for 1D and 3D dealies. Also only 1 3D input and 3 1D inputs.
                if commands.makeList(input)[0].type is misc.Vector:
                    if n == 0:
                        input.connectTo(self.input)
                    else:
                        commands.warning("Too many inputs. First one connected only.")
                else:
                    if n == 0:
                        input.connectTo(self.inputX)
                    elif n == 1:
                        input.connectTo(self.inputY)
                    elif n == 2:
                        input.connectTo(self.inputZ)
                    else:
                        commands.warning("Too many inputs. First three connected only.")
        #connect outputs
        if not output is None:
            for n, output in enumerate(commands.makeList(output)):
                #different output attrs for 1D and 3D dealies
                if commands.makeList(output)[0].type is misc.Vector:
                    self.output.connectTo(output)
                else:
                    self.output.connectTo(outputX)
                    if n > 0:
                        commands.warning("All outputs connected from {0}".format(self.outputX))
Reverse._registerClass()


class Distance(Shape, Node):
    def __init__(self, wrapNode=None, name=None, parent=None, visible=False, createLocators=False, start=[0,0,0], end=[0,0,0], output=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param parent: parent node for the distance node (only if visible is true)
        @param visible: bool, whether the distance node should exist in the viewport
        @param createLocators: bool, whether locators should be created and parented under the start/end nodes (only if visible is true - locators will be created regardless if start or end are not nodes)
        @param start: list or node object to denote the start position of the distance node (if node, distance will be connected to dynamically update to translate changes)
        @param end: list or node object to denote the end position of the distance node (if node, distance will be connected to dynamically update to translate changes)
        @param output: attribute to receive output
        @return: Distance node object
        """
        #set default node name
        name = 'distance' if name is None else name
        super(Distance, self).__init__(wrapNode=wrapNode, name=name, visible=visible, createLocators=createLocators, start=start, end=end, output=output)
    
    @classmethod
    def _registerClass(cls):
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['distanceDimension', 'distanceBetween']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['distanceDimension'] = cls
        nodeInfo.Conversion.nodeTypeByMode['maya']['distanceBetween'] = cls

    def _buildMaya(self, name, parent, visible, createLocators, start, end, output, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        if visible:
            #distanceDimension
            startNode = None
            endNode = None
            #get transform values from nodes in case we're building locators, and define the start/end Nodes
            if isinstance(start, node):
                startNode = start
                start = start.transform(translate=True, query=True, worldSpace=True)
            if isinstance(end, node):
                endNode = end
                end = end.transform(translate=True, query=True, worldSpace=True)
            #make and wrap the node, get the locators' transforms
            newDist = Workbench.createNode('distanceDimension', name=name, parent=parent, skipSelect=True)
            self.wrapNode(newDist)
            #create and parent up locators if appropriate, then connect them up. If not locator, decompose worldmatrix of start/end to get the correct points.
            if createLocators or not isinstance(start, node):
                startLoc = Locator(name=name.replace('Shape', 'StartLoc'), parent=startNode, translate=start)
                startLoc.worldPosition[0].connectTo(self.startPoint)
            else:
                DecomposeMatrix(name=name.replace('Shape', 'DecompStartMatrix'), input=startNode.worldMatrix[0], outputTranslate=self.startPoint)
            if createLocators or not isinstance(end, node):
                endLoc = Locator(name=name.replace('Shape', 'EndLoc'), parent=endNode, translate=end)
                endLoc.worldPosition[0].connectTo(self.endPoint)
            else:
                DecomposeMatrix(name=name.replace('Shape', 'DecompEndMatrix'), input=endNode.worldMatrix[0], outputTranslate=self.endPoint)
        
        else:
            #distanceBetween - isn't a shape, so delete the transform that was created
            if not parent is None:
                parent.delete()
            newDist = Workbench.cmds.shadingNode('distanceBetween', name=name, asUtility=True, skipSelect=True)
            self.wrapNode(newDist)
            #connect the nodes or set the values as appropriate
            if isinstance(start, node):
                start.translate.connectTo(self.point1)
            else:
                self.point1.set(start)
            if isinstance(end, node):
                end.translate.connectTo(self.point2)
            else:
                self.point2.set(end)
        
        #output is (uncharacteristically for Maya) the same for the two nodes
        if not output is None:
            self.distance.connectTo(output)
Distance._registerClass()


class DecomposeMatrix(Node):
    def __init__(self, wrapNode=None, name=None, input=None, outputTranslate=None, outputRotate=None, outputScale=None):
        """
        @param wrapNode: fullPathName of node to be wrapped if any
        @param name: bool or str, defines the name for a new node
        @param input: matrix attribute object to be decomposed
        @param outputTranslate: attribute object to receive decomposed translate
        @param outputRotate: attribute object to receive decomposed rotate
        @param outputScale: attribute object to receive decomposed scale
        @return: DecomposeMatrix node object
        """
        #set default node name
        name = 'decomposeMatrix' if name is None else name
        super(DecomposeMatrix, self).__init__(wrapNode=wrapNode, name=name, input=input, outputTranslate=outputTranslate, outputRotate=outputRotate, outputScale=outputScale)
    
    @classmethod
    def _registerClass(cls):
        #note: multDoubleLinear can be wrapped by this class but cannot be constructed with it
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['decomposeMatrix']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['decomposeMatrix'] = cls
    
    def _buildMaya(self, type, input, outputTranslate, outputRotate, outputScale, **kwargs):
        """
        Internal instructions for building node in Maya. Do not call directly.
        """
        newDecomp = Workbench.cmds.shadingNode('decomposeMatrix', name=name, asUtility=True, skipSelect=True)
        self.wrapNode(newDecomp)
        #wrap connect inputs
        if not input is None:
            input.connectTo(self.inputMatrix)
        #connect outputs
        if not outputTranslate is None:
            self.outputTranslate.connectTo(outputTranslate)
        if not outputRotate is None:
            self.outputRotate.connectTo(outputRotate)
        if not outputScale is None:
            self.outputScale.connectTo(outputScale)
DecomposeMatrix._registerClass()


class Misc(Node):
    """
    class for miscellaneous nodes which need to be wrapped but should not be created
    """
    @classmethod
    def _registerClass(cls):
        #note: multDoubleLinear can be wrapped by this class but cannot be constructed with it
        nodeInfo.Conversion.nodeTypeByClass[cls.__name__] = {'maya':['unitConversion']}
        nodeInfo.Conversion.nodeTypeByMode['maya']['unitConversion'] = cls
    
    def build(self, **kwargs):
        """
        no building possible for this class
        """
        pass
Misc._registerClass()