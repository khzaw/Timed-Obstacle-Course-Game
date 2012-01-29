import direct.directbase.DirectStart
from panda3d.ai import *
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay, CollisionHandlerPusher, CollisionSphere
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import PandaNode, NodePath, TextNode
from panda3d.core import Vec3, Vec4, BitMask32
from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectButton
import sys

# global variables
SPEED = 1               # speed of the main character (sonic)
HEALTH = 100
TIME = 120
TOTAL_TIME = 120

# function to put instructions on the screen
def addInstruction(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1, 1, 1, 1),
                        pos=pos, align=TextNode.ALeft, scale=0.05)

def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1, 1, 1, 1),
                        pos=(1.3, -0.95), align=TextNode.ARight, scale=0.07)

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

        # the menu
        self.loadAudio()
        self.showMenu()

        # keyboard and mouse events
        self.accept("escape", sys.exit)
        self.accept("w", self.setKey, ["forward", 1])
        self.accept("a", self.setKey, ["left", 1])
        self.accept("s", self.setKey, ["backward", 1])
        self.accept("d", self.setKey, ["right", 1])
        self.accept("w-up", self.setKey, ["forward", 0])
        self.accept("a-up", self.setKey, ["left", 0])
        self.accept("s-up", self.setKey, ["backward", 0])
        self.accept("d-up", self.setKey, ["right", 0])
        self.accept("arrow_left", self.setKey, ["cam-left", 1])
        self.accept("arrow_left-up", self.setKey, ["cam-left", 0])
        self.accept("arrow_right", self.setKey, ["cam-right", 1])
        self.accept("arrow_right-up", self.setKey, ["cam-right", 0])

        # create some lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor(Vec4(0.3, 0.3, 0.3, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(Vec3(-5, -5, -5))
        directionalLight.setColor(Vec4(1, 1, 1, 1))
        directionalLight.setSpecularColor(Vec4(1, 1, 1, 1))
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(directionalLight))

    def loadAudio(self):
        self.startAudio = base.loader.loadSfx("../assets/audio/start.mp3")
        self.gameAudio = base.loader.loadSfx("../assets/audio/game.mp3")
        self.winAudio = base.loader.loadSfx("../assets/audio/win.mp3")
        self.loseAudio = base.loader.loadSfx("../assets/audio/lose.mp3")

    def createPresents(self):
        self.speedPill = loader.loadModel("../assets/models/capsule/capsule")
        self.speedPill.reparentTo(render)
        self.speedPill.setScale(0.025)
        self.speedPill.setPos(-43.9744, 32.031, 0.6)

        self.speedPillb = loader.loadModel("../assets/models/capsule/capsule")
        self.speedPillb.reparentTo(render)
        self.speedPillb.setScale(0.025)
        self.speedPillb.setPos(-57.7858, -61.5068, 3.80818)

        self.banana = loader.loadModel("../assets/models/banana/banana")
        self.banana.reparentTo(render)
        self.banana.setScale(3)
        self.banana.setPos(-72.484, -7.14435, 5.05246)

        self.sphinx = loader.loadModel("../assets/models/sphinx/sphinx")
        self.sphinx.reparentTo(render)
        self.sphinx.setScale(0.0025)
        self.sphinx.setPos(-48.0702, -39.4669, 0.5)


    def createMilesAI(self):
        startPos = self.env.find("**/start_point").getPos()

        # load miles actor
        self.miles1 = Actor("../assets/models/miles/tails",
                {"board"   : "../assets/models/miles/tails-board",
                 "win"     : "../assets/models/miles/tails-win",
                 "fwboard" : "../assets/models/miles/tails-fallingwboard",
                 "fwoboard": "../assets/models/miles/tails-fallingwoboard"})

        self.miles2 = Actor("../assets/models/miles/tails",
                {"board"   : "../assets/models/miles/tails-board",
                 "win"     : "../assets/models/miles/tails-win",
                 "fwboard" : "../assets/models/miles/tails-fallingwboard",
                 "fwoboard": "../assets/models/miles/tails-fallingwoboard"})

        self.miles = [self.miles1, self.miles2]

        self.miles1.reparentTo(render)
        self.miles1.setScale(0.05)
        self.miles1.setPlayRate(3, 'run')
        self.miles1.loop('board')
        self.miles1.setPos(startPos[0] + 5, startPos[1] - 20, startPos[2])

        self.miles1GroundRay = CollisionRay()
        self.miles1GroundRay.setOrigin(0, 0, 1000)
        self.miles1GroundRay.setDirection(0, 0, -1)
        self.miles1GroundCol = CollisionNode('miles1Ray')
        self.miles1GroundCol.addSolid(self.miles1GroundRay)
        self.miles1GroundCol.setFromCollideMask(BitMask32.bit(0))
        self.miles1GroundCol.setIntoCollideMask(BitMask32.allOff())
        self.miles1GroundColNp = self.miles1.attachNewNode(self.miles1GroundCol)
        self.miles1GroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.miles1GroundColNp, self.miles1GroundHandler)

        # AI code for miles1
        self.miles1AI = AICharacter("miles1", self.miles1, 100, 1, 7)
        self.AIworld.addAiChar(self.miles1AI)
        self.miles1AIbehaviors = self.miles1AI.getAiBehaviors()

        # pursue behavior
        self.miles1AIbehaviors.pursue(self.sonic)

        taskMgr.add(self.moveMiles1AI, "moveMiles1AI")

        self.miles2.reparentTo(render)
        self.miles2.setScale(0.05)
        self.miles2.setPlayRate(3, 'run')
        self.miles2.loop('win')
        self.miles2.setPos(startPos[0] -5, startPos[1] - 20, startPos[2])

        self.miles2GroundRay = CollisionRay()
        self.miles2GroundRay.setOrigin(0, 0, 1000)
        self.miles2GroundRay.setDirection(0, 0, -1)
        self.miles2GroundCol = CollisionNode('miles2Ray')
        self.miles2GroundCol.addSolid(self.miles2GroundRay)
        self.miles2GroundCol.setFromCollideMask(BitMask32.bit(0))
        self.miles2GroundCol.setIntoCollideMask(BitMask32.allOff())
        self.miles2GroundColNp = self.miles2.attachNewNode(self.miles2GroundCol)
        self.miles2GroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.miles2GroundColNp, self.miles2GroundHandler)

        self.miles2AI = AICharacter("miles2", self.miles2, 100, 1, 7)
        self.AIworld.addAiChar(self.miles2AI)
        self.miles2AIbehaviors = self.miles2AI.getAiBehaviors()

        # puruse behavior
        self.miles2AIbehaviors.pursue(self.sonic)

        taskMgr.add(self.moveMiles2AI, "moveMiles2AI")

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
        self.trexGroundCol = CollisionNode('trexRay')
        self.trexGroundCol.addSolid(self.trexGroundRay)
        self.trexGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.trexGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.trexGroundColNp = self.trex.attachNewNode(self.trexGroundCol)
        self.trexGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.trexGroundColNp, self.trexGroundHandler)

        #self.pusher.addCollider(self.trexGroundColNp, self.sonic)

        # AI code for trex
        self.trexAI = AICharacter("trex", self.trex, 100, 1, 7)
        self.AIworld.addAiChar(self.trexAI)
        self.trexAIbehaviors = self.trexAI.getAiBehaviors()

        # pursue behavior
        #self.trexAIbehaviors.pursue(self.sonic)

        self.trexAIbehaviors.pursue(self.sonic)

        taskMgr.add(self.moveTrexAI, "moveTrexAI")


    # to create the AI world
    def setAI(self):
        self.AIworld = AIWorld(render)
        taskMgr.add(self.AIUpdate, "AIUpdate")

    def AIUpdate(self, task):
        self.AIworld.update()
        return task.cont

    def moveMiles1AI(self, task):
        startpos = self.miles1.getPos()

        entries = []
        for i in range(self.miles1GroundHandler.getNumEntries()):
            entry = self.miles1GroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x, y: cmp(y.getSurfacePoint(render).getZ(),
                                      x.getSurfacePoint(render).getZ()))

        if(len(entries) > 0) and (entries[0].getIntoNode().getName() == "terrain"):
            miles1Z = entries[0].getSurfacePoint(render).getZ()
            miles1Y = entries[0].getSurfacePoint(render).getY()
            miles1X = entries[0].getSurfacePoint(render).getX()

            self.miles1.setZ(entries[0].getSurfacePoint(render).getZ())
        else:
            self.miles1.setPos(startpos)

        return task.cont

    def moveMiles2AI(self, task):
        startpos = self.miles2.getPos()

        entries = []
        for i in range(self.miles2GroundHandler.getNumEntries()):
            entry = self.miles2GroundHandler.getEntry(i)
            entries.append(entry)
        entries.sort(lambda x, y: cmp(y.getSurfacePoint(render).getZ(),
                                      x.getSurfacePoint(render).getZ()))

        if(len(entries) > 0) and (entries[0].getIntoNode().getName() == "terrain"):
            miles2Z = entries[0].getSurfacePoint(render).getZ()
            miles2Y = entries[0].getSurfacePoint(render).getY()
            miles2X = entries[0].getSurfacePoint(render).getX()

            self.miles2.setZ(entries[0].getSurfacePoint(render).getZ())
        else:
            self.miles2.setPos(startpos)

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

        print self.sonic.getPos()

        return task.cont

    def checkWin(self, task):
        delta = self.sonic.getDistance(self.flag)
        if(delta < 25):
            self.winText = OnscreenText(text="You Win!", style=1, fg=(1, 1, 1, 1),
                        pos=(0,0), align=TextNode.ACenter, scale=0.4)
            self.resetBtn = DirectButton(text=("Restart", "Restart", "Restart"), scale=0.1,
                    command=self.resetGame, pos=(0, 0, -0.7))

            taskMgr.remove("moveTask")
            if(self.gameAudio.status() == self.gameAudio.PLAYING):
                self.gameAudio.stop()
                self.winAudio.play()
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

    def checkGameOver(self, task):
        health_left = HEALTH
        if(1 <= health_left <=10):
            global SPEED
            SPEED = 0.5
        if(health_left <= 0):
            taskMgr.remove("moveTask")
            self.gameOverText = OnscreenText(text="Game Over!", style=1, fg=(1, 1, 1, 1),
                        pos=(0, 0), align=TextNode.ACenter, scale=0.4)
            self.resetBtn = DirectButton(text=("Restart", "Restart", "Restart"), scale=0.1,
                        command=self.resetGame, pos=(0, 0, -0.7))

            if(self.gameAudio.status() == self.gameAudio.PLAYING):
                self.gameAudio.stop()
                self.loseAudio.play()
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

        if(self.winAudio.status() == self.winAudio.PLAYING) or (self.loseAudio.status() == self.loseAudio.PLAYING):
            self.winAudio.stop()
            self.loseAudio.play()
            self.gameAudio.play()

        # reset position
        self.sonic.setPos(self.START)

        # reset time count
        global TIME, TOTAL_TIME
        TIME = 120
        TOTAL_TIME = 120

    def showMenu(self):
        #TODO: add more controls text
        self.startAudio.play()
        self.gameNameText = OnscreenText(text="Run, Baby, Run", style=1, fg=(1, 1, 1, 1),
                                         pos=(0,0.5), align=TextNode.ACenter, scale=0.3)
        self.controlsText = OnscreenText(text="Controls", style=1, fg=(1, 1, 1, 1),
                                         pos=(0,0), align=TextNode.ACenter, scale=0.05)
        self.startBtn = DirectButton(text=("Start", "Start", "Start"), scale=0.1,
                command=self.startGame, pos=(0, 0, -0.7))

    def checkConditions(self, task):
        trexDelta = self.sonic.getDistance(self.trex)
        miles1Delta = self.sonic.getDistance(self.miles1)
        miles2Delta = self.sonic.getDistance(self.miles2)
        if trexDelta <= 5 or miles1Delta <= 5 or miles2Delta <= 5:
            global HEALTH
            HEALTH = HEALTH - 1
            if HEALTH < 0:
                HEALTH = 0
            self.health_text.setText("Health :: %i" % HEALTH)

        return task.cont

    def checkSpeed(self, task):
        speedDelta = self.sonic.getDistance(self.speedPill)
        if speedDelta <= 30:
            global SPEED
            SPEED = SPEED + 1
            self.speedPill.removeNode()
            return task.done
        return task.cont

    def checkSpeed2(self, task):
        speedDelta2 = self.sonic.getDistance(self.speedPillb)
        print speedDelta2
        if speedDelta2 <= 3720:
            global SPEED
            SPEED = SPEED + 1
            self.speedPillb.removeNode()
            return task.done
        return task.cont

    def checkHealthBoost(self, task):
        healthDelta = self.sonic.getDistance(self.banana)
        if healthDelta <= 3:
            global HEALTH
            HEALTH = HEALTH + 10
            if HEALTH > 100:
                HEALTH = 100
            self.banana.removeNode()
            self.health_text.setText("Health :: %i" % HEALTH)
            return task.done
        return task.cont

    def checkTimeAdd(self, task):
        timeAddDelta = self.sonic.getDistance(self.sphinx)
        if timeAddDelta <= 507:
            global TOTAL_TIME
            TOTAL_TIME = TOTAL_TIME + 10
            self.time_text.setText("Time Remaining :: %i" % TOTAL_TIME)
            self.sphinx.removeNode()
            return task.done
        return task.cont


    def startGame(self):
        # remove menu main elements
        if hasattr(game, 'startBtn'):
            self.startBtn.destroy()
        if hasattr(game, 'gameNameText'):
            self.gameNameText.destroy()
        if hasattr(game, 'controlsText'):
            self.controlsText.destroy()
        if self.startAudio.status() == self.startAudio.PLAYING:
            self.startAudio.stop()
            self.gameAudio.play()

        # HUD information (time, health)
        self.time_text = addInstruction((-1.2, 0.9), "Time Reamining :: %i" % TIME)
        self.health_text = addInstruction((0.9, 0.9), "Health :: %i" % HEALTH)

        # the environment
        self.env = loader.loadModel("../assets/models/world")
        self.env.reparentTo(render)
        self.env.setPos(0, 0, 0)

        # the flag(destination)
        self.flag = loader.loadModel("../assets/models/flag/flag")
        self.flag.reparentTo(render)
        self.flag.setScale(0.1)
        self.flag.setPos(0, 0, 5)
        self.DESTINATION = self.flag.getPos()

        # main character(sonic)
        self.START = self.env.find("**/start_point").getPos()
        self.sonic = Actor("../assets/models/sonic/sonic",
                {"run"     : "../assets/models/sonic/sonic-run",
                 "win"     : "../assets/models/sonic/sonic-win",
                 "board"   : "../assets/models/sonic/sonic-board",
                 "fwboard" : "../assets/models/sonic/sonic-fallingwboard",
                 "fwoboard": "../assets/models/sonic/sonic-fallingwoboard"})
        self.sonic.reparentTo(render)
        self.sonic.setScale(0.05)
        self.sonic.setPos(self.START)

        # create a floater object to be used as a temporary
        # variable in a variety of calculations
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)

        taskMgr.add(self.move, "moveTask")

        # varible to keep track of moving state
        self.isMoving = False

        # variable to keep track of speed boost
        self.speedBoost = False

        # variable to keep track of invulnerability
        self.invul = False

        # setup the camera
        base.disableMouse()
        base.camera.setPos(self.sonic.getX(), self.sonic.getY() + 10, 2)

        self.cTrav = CollisionTraverser()
        #self.pusher = CollisionHandlerPusher()

        self.sonicGroundRay = CollisionRay()
        self.sonicGroundRay.setOrigin(0, 0, 1000)
        self.sonicGroundRay.setDirection(0, 0, -1)
        self.sonicGroundCol = CollisionNode('sonicRay')
        self.sonicGroundCol.addSolid(self.sonicGroundRay)
        #self.sonicGroundCol.addSolid(CollisionSphere(0, 0, 1.5, 1.5))
        self.sonicGroundCol.setFromCollideMask(BitMask32.bit(0))
        self.sonicGroundCol.setIntoCollideMask(BitMask32.allOff())
        self.sonicGroundColNp = self.sonic.attachNewNode(self.sonicGroundCol)
        self.sonicGroundHandler = CollisionHandlerQueue()
        self.sonicPusher = CollisionHandlerPusher()
        self.sonicPusher.addInPattern('%fn-into-%in')
        self.cTrav.addCollider(self.sonicGroundColNp, self.sonicGroundHandler)
        #self.cTrav.addCollider(self.sonicGroundColNp, self.sonicPusher)
        #self.sonicPusher.addCollider(self.sonicGroundColNp, self.sonic)



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

        # create AI characters
        self.createTrexAI()
        self.createMilesAI()

        # place the presents
        self.createPresents()

        # check winning condition
        taskMgr.add(self.checkWin, "checkWin")

        # check time conditions
        taskMgr.add(self.checkTime, "checkTime")

        # check health conditions
        taskMgr.add(self.checkGameOver, "checkGameOver")

        # check other conditions
        taskMgr.add(self.checkConditions, "checkConditions")

        taskMgr.add(self.checkSpeed, "checkSpeed")
        taskMgr.add(self.checkSpeed2, "checkSpeed2")
        taskMgr.add(self.checkHealthBoost, "checkHealthBoost")
        taskMgr.add(self.checkTimeAdd, "checkTimeAdd")

game = Game()
run()
