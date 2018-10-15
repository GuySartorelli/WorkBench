import utils.names #not correct path
import nodes, commands #not correct path

def insertJoints(startJnt, numJnts, endJnt=None, name=None, delimiter=1, suffix=None):
    """
    inserts joints between two existing joints
    
    @param startJnt: joint node to act as parent to the inserted joint chain
    @param numJnts: int, number of new joints to be added to the chain
    @param endJnt: existing joint node to be the last joint in the chain. Must be direct child of startJnt
    @param name: str, name prefix for inserted joints. Default is startJnt's name
    @param delimiter: str or int, starting letter or number to use as name suffix for new joints (increases for each joint)
    @param suffix: suffix for all new joints. Default strips from startJnt
    @return: list, all joints in the chain including original startJnt and endJnt
    """
    if endJnt is None:    
        endJnt = startJnt.getHierarchy(children=True, type='joint')[0]
    #get average distance for new joints. numJnts+1 because endJnt needs to be part of the average distance calc.
    jntDist = getDistance(startJnt, endJnt) / (numJnts+1.0)
    jntDir = getDirection(startJnt, endJnt)
    #getDirection returns a worldspace unit vector so we just need to give it a magnitude
    jntTranslate = jntDir * jntDist
    
    #set joint name and suffix if not supplied
    if name is None:
        name = utils.names.stripAffix(name=startJnt.name, suffix=True)[0]
    if suffix is None:
        suffix = utils.names.stripAffix(name=startJnt.name, suffix=True)[-1]
    
    jnts = [parentJnt]
    delimiterIterator = utils.names.generateDelimiters(delimiter)
    #add new joints into the chain at the correct distances
    for n, char in zip(range(0, numJnts), delimiterIterator):
        newJnt = converter.nodes.Joint(name=name+str(char)+suffix, parent=jnts[-1])
        newJnt.transform(translate=jntTranslate*(n+1), relative=True, worldSpace=True)
        jnts.append(newJnt)
    
    #position original child joint correctly and append to list
    childJnt.parent(jnts[-1])
    childJnt.transform(translate=jntTranslate, relative=True, worldSpace=True)
    jnts.append(childJnt)
    return jnts