import direct.directbase.DirectStart
from panda3d.ai import *
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import PandaNode, NodePath, TextNode
from panda3d.core import Vec3, Vec4, BitMask32
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectButton
import sys

# global variables
SPEED = 8               # speed of the main character (sonic)
HEALTH = 100
TIME = 5
TOTAL_TIME = 5
#TIME = 120
#TOTAL_TIME = 120

# function to put instructions on the screen
def addInstruction(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1),
                        pos=pos, align=TextNode.ALeft, scale=0.05)

def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1),
                        pos=(1.3, -0.95), align=TextNode.ARight, scale=0.07)

#def showMainMenu():


class Game(DirectObject):

    def __init__(self):

        self.setAI()

        self.keyMap = {
                "left"     : 0,
                "right"    : 0,
                "forward"  : 0,
                "backward" : 0,
                "cam-left" : 0,
                "cam-right": 0,
                }
        base.win.setClearColor(Vec4(0, 0, 0, 1))


        # the environment
        self.env = loader.loadModel("../assets/models/world")
        self.env.reparentTo(render)
        self.env.setPos(0, 0, 0)

        # HUD
        self.time_text = addInstruction((-1.2, 0.9), "Time Remaining :: %s" % TIME)
        self.health_text = addInstruction((0.9, 0.9), "Health :: %s" % HEALTH)

        # the flag ( destination )
        self.flag = loader.loadModel("../assets/models/flag/flag")
        self.flag.reparentTo(render)
        self.flag.setScale(0.1)
        self.flag.setPos(0, 0, 5)
        self.DESTINATION = self.flag.getPos()

        # main character (sonic)
        self.START = self.env.find("**/start_point").getPos()
        self.sonic = Actor("../assets/models/sonic/sonic",
                {"run" : "../assets/models/sonic/sonic-run",
                 "win" : "../assets/models/sonic/sonic-win",
                 "board" : "../assets/models/sonic/sonic-board" ,
                 "fwboard" : "../assets/models/sonic/sonic-fallingwboard",
                 "fwoboard" : "../assets/models/sonic/sonic-fallingwoboard" })
        self.sonic.reparentTo(render)
        self.sonic.setScale(0.05)
        self.sonic.setPos(self.START)

        # create a floater object to be used as a temporary
        # variable in a variety of calculations
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)

        # keyboard and mouse events
        self.accept("escape", sys.exit)
        self.accept("w", self.setKey, ["forward" , 1])
        self.accept("a", self.setKey, ["left" , 1])
        self.accept("s", self.setKey, ["backward" , 1])
        self.accept("d", self.setKey, ["right" , 1])
        self.accept("w-up", self.setKey, ["forward", 0])
        self.accept("a-up", self.setKey, ["left", 0])
        self.accept("s-up", self.setKey, ["backward", 0])
        self.accept("d-up", self.setKey, ["right", 0])
        self.accept("arrow_left", self.setKey, ["cam-left", 1])
        self.accept("arrow_left-up", self.setKey, ["cam-left", 0])
        self.accept("arrow_right", self.setKey, ["cam-right", 1])
        self.accept("arrow_right-up", self.setKey, ["cam-right", 0])

        taskMgr.add(self.move, "moveTask")

        # variable to keep track of moving state
        self.isMoving = False

        # setup the camera
        base.disableMouse()
        base.camera.setPos(self.sonic.getX(), self.sonic.getY() + 10, 2)

        self.cTrav = CollisionTraverser()

        self.sonicGroundRay = CollisionRay()
        self.sonicGroundRay.setOrigin(0, 0, 1000)
        self.sonicGroundRay.setDirection(0, 0, -1)
        self.sonicGroundCol = CollisionNode('sonicRay')
        self.sonicGroundCol.addSolid(self.sonicGroundRay)
        self.sonicGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.sonicGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.sonicGroundColNp = self.sonic.attachNewNode(self.sonicGroundCol)
        self.sonicGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.sonicGroundColNp, self.sonicGroundHandler)

        self.camGroundRay = CollisionRay()
        self.camGroundRay.setOrigin(0, 0, 1000)
        self.camGroundRay.setDirection(0, 0, -1)
        self.camGroundCol = CollisionNode('camRay')
        self.camGroundCol.addSolid(self.camGroundRay)
        self.camGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.camGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.camGroundColNp = base.camera.attachNewNode(self.camGroundCol)
        self.camGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.camGroundColNp, self.camGroundHandler)

        # see the collision rays
        self.sonicGroundColNp.show()
        self.camGroundColNp.show()

        # visual representation of the collisions occuring
        self.cTrav.showCollisions(render)

        self.createTrexAI()

        # create some lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor(Vec4(0.3, 0.3, 0.3, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(Vec3(-5, -5, -5))
        directionalLight.setColor(Vec4(1, 1, 1, 1))
        directionalLight.setSpecularColor(Vec4(1, 1, 1, 1))
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(directionalLight))

        # check win
        taskMgr.add(self.checkWin, "checkWin")

        # check time
        taskMgr.add(self.checkTime, "checkTime")

        # check health
        taskMgr.add(self.checkHealth, "checkHealth")

    def createTrexAI(self):
        startPos = self.env.find("**/start_point").getPos()

        # Load the trex actor and loop its animation
        self.trex = Actor("../assets/models/trex/trex",
                {"run" : "../assets/models/trex/trex-run",
                 "eat" : "../assets/models/trex/trex-eat"})
        self.trex.reparentTo(render)
        self.trex.setScale(0.25)
        self.trex.setPlayRate(3, 'run')
        self.trex.loop('run')
        self.trex.setPos(startPos[0], startPos[-1] - 20, startPos[2])

        self.trexGroundRay = CollisionRay()
        self.trexGroundRay.setOrigin(0,0,1000)
        self.trexGroundRay.setDirection(0,0,-1)
        self.trexGroundCol = CollisionNode('pandaRay')
        self.trexGroundCol.addSolid(self.trexGroundRay)
        self.trexGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.trexGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.trexGroundColNp = self.trex.attachNewNode(self.trexGroundCol)
        self.trexGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.trexGroundColNp, self.trexGroundHandler)

        # AI code for trex
        self.trexAI = AICharacter("trex", self.trex, 100, 0.05, 5)
        self.AIworld.addAiChar(self.trexAI)
        self.trexAIbehaviors = self.trexAI.getAiBehaviors()

        # pursue behavior
        self.trexAIbehaviors.pursue(self.sonic)


        taskMgr.add(self.moveTrexAI, "moveTrexAI")

    # to create the AI world
    def setAI(self):
        self.AIworld = AIWorld(render)
        taskMgr.add(self.AIUpdate, "AIUpdate")

    def AIUpdate(self, task):
        self.AIworld.update()
        return task.cont

    def moveTrexAI(self, task):

        startpos = self.trex.getPos()

        entries = []
        for i in range(self.trexGroundHandler.getNumEntries()):
            entry = self.trexGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
                                     x.getSurfacePoint(render).getZ()))

        if(len(entries) > 0) and (entries[0].getIntoNode().getName() =="terrain"):
            trexZ = entries[0].getSurfacePoint(render).getZ()
            trexY = entries[0].getSurfacePoint(render).getY()
            trexX = entries[0].getSurfacePoint(render).getX()

            self.trex.setZ(entries[0].getSurfacePoint(render).getZ())
        else:
            self.trex.setPos(startpos)

        return task.cont



    def setKey(self, action, value):
        self.keyMap[action] = value

    def move(self, task):

        base.camera.lookAt(self.sonic)
        if(self.keyMap["cam-left"] != 0):
            base.camera.setX(base.camera, -30 * globalClock.getDt())
        if(self.keyMap["cam-right"] != 0):
            base.camera.setX(base.camera, +30 * globalClock.getDt())

        startpos = self.sonic.getPos()

        if(self.keyMap["left"] != 0):
            self.sonic.setH(self.sonic.getH() + 300 * globalClock.getDt())
        if(self.keyMap["right"] != 0):
            self.sonic.setH(self.sonic.getH() - 300 * globalClock.getDt())
        if(self.keyMap["forward"] != 0):
            self.sonic.setY(self.sonic, -100 * globalClock.getDt() * SPEED)
        if(self.keyMap["backward"] != 0):
            self.sonic.setY(self.sonic, 100 * globalClock.getDt() * SPEED)

        # If sonic is moving, loop the run animation
        # If he is standing still, stop the animation
        if(self.keyMap["forward"] != 0) or (self.keyMap["left"] != 0) or (self.keyMap["right"] != 0) or (self.keyMap["backward"] != 0):
            if self.isMoving is False:
                self.sonic.loop("board")
                self.isMoving = True
        else:
            if self.isMoving:
                self.sonic.stop()
                self.sonic.pose("fwboard", 5)
                self.isMoving = False

        # If the camera is too far from sonic, move it closer
        # If the camera is too close to sonic, move it farther

        camvec = self.sonic.getPos() - base.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if(camdist > 10.0):
            base.camera.setPos(base.camera.getPos() + (camvec * (camdist-10)))
            camdist = 10.0
        if(camdist < 5.0):
            base.camera.setPos(base.camera.getPos() - (camvec * (5-camdist)))
            camdist = 5.0

        # now check for collisions

        self.cTrav.traverse(render)

        entries = []
        for i in range(self.sonicGroundHandler.getNumEntries()):
            entry = self.sonicGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
                                     x.getSurfacePoint(render).getZ()))

        if(len(entries) > 0) and (entries[0].getIntoNode().getName() == 'terrain'):
            self.sonic.setZ(entries[0].getSurfacePoint(render).getZ())
        else:
            self.sonic.setPos(startpos)


        # keep the camera at one foot avoce the terrian
        # or two feet above sonic, whichever is greater

        entries = []
        for i in range(self.camGroundHandler.getNumEntries()):
            entry = self.camGroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x,y: cmp(y.getSurfacePoint(render).getZ(),
                                     x.getSurfacePoint(render).getZ()))

        if(len(entries) > 0) and (entries[0].getIntoNode().getName() == "terrain"):
            base.camera.setZ(entries[0].getSurfacePoint(render).getZ() + 1.0)

        if (base.camera.getZ() < self.sonic.getZ() + 2.0):
            base.camera.setZ(self.sonic.getZ() + 2.0)


        # The camera should look in sonic's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above sonic's head

        self.floater.setPos(self.sonic.getPos())
        self.floater.setZ(self.sonic.getZ() + 2.0)
        base.camera.lookAt(self.floater)

        # Update the camera based on mouse movement
        md = base.win.getPointer(0)
        x = md.getX()
        y = md.getY()
        if base.win.movePointer(0, base.win.getXSize()/2, base.win.getYSize()/2):
            base.camera.setX(base.camera, (x - base.win.getXSize()/2) * globalClock.getDt() * 0.1)

        # timer countdown
        global TIME
        TIME = TOTAL_TIME - int(task.time)

        self.time_text.setText("Time Remaining :: %i" % TIME)

        return task.cont

    def checkWin(self, task):
        delta = self.sonic.getDistance(self.flag)
        if(delta < 30):
            self.winText = OnscreenText(text="You Win!", style=1, fg=(1, 1, 1, 1),
                        pos=(0,0), align=TextNode.ACenter, scale=0.4)
            self.resetBtn = DirectButton(text=("Restart", "Restart", "Restart"), scale=0.1,
                    command=self.resetGame, pos=(0, 0, -0.7))

            taskMgr.remove("moveTask")
            return task.done
        return task.cont

    def checkTime(self, task):
        time_left = TIME
        if(time_left == 0):
            taskMgr.remove("moveTask")
            self.gameOverText = OnscreenText(text="Game Over!", style=1, fg=(1, 1, 1, 1),
                        pos=(0, 0), align=TextNode.ACenter, scale=0.4)
            self.resetBtn = DirectButton(text=("Restart", "Restart", "Restart"), scale=0.1,
                        command=self.resetGame, pos=(0, 0, -0.7))
            return task.done
        return task.cont

    def checkHealth(self, task):
        health_left = HEALTH
        if(health_left == 0):
            taskMgr.remove("moveTask")
            self.gameOverText = OnscreenText(text="Game Over!", style=1, fg=(1, 1, 1, 1),
                        pos=(0, 0), align=TextNode.ACenter, scale=0.4)
            self.resetBtn = DirectButton(text=("Restart", "Restart", "Restart"), scale=0.1,
                        command=self.resetGame, pos=(0, 0, -0.7))
            return task.done
        return task.cont

    def resetGame(self):
        # re-add the move task
        taskMgr.add(self.move, "moveTask")

        # remove GUI elements
        if hasattr(game, 'gameOverText'):
            self.gameOverText.destroy()
        if hasattr(game, 'resetBtn'):
            self.resetBtn.destroy()
        if hasattr(game, 'winText'):
            self.winText.destroy()

        # reset position
        self.sonic.setPos(self.START)

        # reset time count
        global TIME, TOTAL_TIME
        TIME = 120
        TOTAL_TIME = 120






game = Game()
run()
