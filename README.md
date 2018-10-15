The beginnings of a cross-platform 3D rigging toolkit written in python. Intended to allow rigs created in one application to be seamlessly imported into another for animating.
This project has been temporarily put on hold while I learn more about programming best-practices and work on developing my own independent 3D rigging application (of which this will become a component).

Currently this project only works in maya and has extremely limited functionality. 

The Bench class is intended to hold information about which nodes exist in the current rig and will be used to save/load/build "benches" aka rig files.
The Workbench class holds information about which application the toolkit is being run in as well as what bench is currently being used to store the nodes.



To use the toolit, import Workbench and set Workbench.mode = "maya"
import converter.nodes as wbn
import converter.commands as wbc

While there are a lot of commands to manipulate nodes, this is mostly to mimic the maya commands functional conventions. It is recommended to limit use of commands to those functions not available as methods on node classes.
Examples are:
wbc.select
wbc.listSelection
wbc.getDistance
wbc.getDirection
Please read the documentation comments for information about how to use those functions.

Most of the usefulness with the workbench toolkit is in wbn.
For example if you want to create a joint located at x=1, y=20, y=0, you can use:
joint1 = wbn.Joint(translate=[10,20,0], name="jointA")

You can then create another joint with joint1 as its parent:
joint2 = wbn.Joint(parent=joint1, translate=[0,10,0])

You can easily group nodes using the Group class
group = Group(joint1)

And create an IK solver with the IkSolver class
ik = IkSolver(startJnt=joint1, endJnt=joint2)

You can then manipulate those nodes through the methods available in nodes.py (I suggest giving that file a good look-through) e.g:
joint2.rename("jointB")
group.freezeTransform()
joint1.hide() #OR joint1.toggleVisibility()

Attributes are also objects on the node, e.g.
group.translateX = 50 #OR group.translateX.value = 50 OR group.translateX.set(50)
group.rotate.lock()
joint2.addAttribute(type="float", shortName="j1rx") #OR addattr(....) #note that addAttribute is not yet implemented
joint1.rotateX.connectTo(joint2.j1rx)



The intention is to also include procedural auto-rigging modules for quickly setting up stretchy ik/fk limbs and other common/frequent systems.