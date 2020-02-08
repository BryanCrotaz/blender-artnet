# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import types
import socket
import select
import threading
import math

Universes = []  # float data 0-1
RawUniverses = []  # byte data 0-255
ArtNetSocket = None

FixtureTypes = {
    "wash": {
        "power": 1000,
        "color": "rgbw",
        "red": 8,
        "green": 10,
        "blue": 12,
        "white": 14,
        "pan": 0,
        "tilt": 2,
        "zoom": 20,
        "panRange": 540,
        "tiltRange": 270,
        "minZoom": 12,
        "maxZoom": 49
    },
    "spot": {
        "power": 1000,
        "color": "cmy",
        "cyan": 8,
        "magenta": 9,
        "yellow": 10,
        "pan": 0,
        "tilt": 2,
        "zoom": 21,
        "panRange": 540,
        "tiltRange": 270,
        "minZoom": 10,
        "maxZoom": 45
    },
    "pointe": {
        "power": 1000,
        "color": "wheel",
        "colorWheel": {
            0: [1,1,1],
            9: [1,0,0],
            18: [0,0,1],
            27: [0,1,1],
            37: [0.2,1,0,2],
            46: [1,0,1]
        },
        "pan": 0,
        "tilt": 2,
        "zoom": 16,
        "panRange": 540,
        "tiltRange": 270,
        "minZoom": 5,
        "maxZoom": 20
    }
}

FixtureUniverses = {
    2: {
        "Spot.027": {
            "fixtureType": "wash",
            "baseAddress": 147
        },
        "Spot.028": {
            "fixtureType": "wash",
            "baseAddress": 180
        },
     #   "Spot.012": {
     #       "fixtureType": "wash",
     #       "baseAddress": 181
     #   },
        "Spot.026": {
            "fixtureType": "wash",
            "baseAddress": 246
        },
     #   "Spot.012": {
     #       "fixtureType": "wash",
      #      "baseAddress": 181
     #   }
    },
    3: {
        "Spot.015": {
            "fixtureType": "wash",
            "baseAddress": 247
        },
        "Spot.014": {
            "fixtureType": "wash",
            "baseAddress": 214
        },
        "Spot.012": {
            "fixtureType": "wash",
            "baseAddress": 181
        },
        "Spot.016": {
            "fixtureType": "wash",
            "baseAddress": 148
        },
        "Spot.013": {
            "fixtureType": "wash",
            "baseAddress": 115
        },
        "Spot.017": {
            "fixtureType": "wash",
            "baseAddress": 82
        },
        "Spot.018": {
            "fixtureType": "wash",
            "baseAddress": 49
        }
    },
    4: {
        "Spot.020": {
            "fixtureType": "wash",
            "baseAddress": 247
        },
        "Spot.019": {
            "fixtureType": "wash",
            "baseAddress": 214
        },
        "Spot.021": {
            "fixtureType": "wash",
            "baseAddress": 181
        },
        "Spot.022": {
            "fixtureType": "wash",
            "baseAddress": 148
        },
        "Spot.023": {
            "fixtureType": "wash",
            "baseAddress": 115
        },
        "Spot.024": {
            "fixtureType": "wash",
            "baseAddress": 82
        },
        "Spot.025": {
            "fixtureType": "wash",
            "baseAddress": 49
        }
    }
}

UniverseUpdatesPending = {} # map of universe indices : bool
UniverseUpdatesLock = threading.Lock()

def getUniverse(index):
    while (len(Universes) <= index):
        universe = []
        for _ in range(512):
            universe.append(0)
        Universes.append(universe)
        rawUniverse = []
        for _ in range(512):
            rawUniverse.append(0)
        RawUniverses.append(rawUniverse)
    return Universes[index]   
    
def init():
    setup()
    ArtNetSocket = connect()
    if (ArtNetSocket != None):
        thread = threading.Thread(target=socketLoop, args=(ArtNetSocket,))
        thread.start()
    bpy.app.timers.register(updateBlender, first_interval=0.1, persistent=True)

def connect():
    try:
        UDP_IP = "0.0.0.0"
        UDP_PORT = 6454

        artNetSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        artNetSocket.bind((UDP_IP, UDP_PORT))
        artNetSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # blocking socket as we're listening in a background thread
        artNetSocket.setblocking(1)
        return artNetSocket
    except Exception as err:
        print("error while connecting", err)
        disconnect(artNetSocket)
        return None

def disconnect(artNetSocket):
    if (artNetSocket is not None):
        artNetSocket.close()
    ArtNetSocket = None

def isArtNet(packet):
    return (packet[0] == 65 
            and packet[1] == 114 
            and packet[2] == 116
            and packet[8] == 0
            and packet[9] == 80) # known header

def rgbwToRgb(red, green, blue, white):
    w = white
    r = (red + w/3) * 3 / 4
    g = (green + w/3) * 3 / 4
    b = (blue + w/3) * 3 / 4
    return [r,g,b]    

def cmyToRgb(cyan, magenta, yellow):
    r = 1-cyan
    g = 1-magenta
    b = 1-yellow
    return [r,g,b]    

def setup():
    # grab the objects to be mapped to data
    objects = bpy.context.scene.objects
    for universe in FixtureUniverses:
        u = FixtureUniverses[universe]
        for name in u:
            # grab the blender named object so we don't need to do this every frame
            obj = objects[name]
            u[name]["object"] = obj
            # base address is 1-based so subtract 1 from it
            u[name]["baseAddress"] -= 1
            obj.rotation_mode = "XYZ"
    for fixtureType in FixtureTypes:
        ft = FixtureTypes[fixtureType]
        # convert degrees to radians so we don't do this every frame
        ft["panRange"] = math.radians(ft["panRange"])
        ft["tiltRange"] = math.radians(ft["tiltRange"])
    
def socketLoop(artNetSocket):
    # runs in a background thread
    # must not access blender directly
    socket = artNetSocket
#    for t in range(10):
    while True:
        try:
            # read the packet
            packet, _addr = socket.recvfrom(1024) 
            if (len(packet) > 18 and isArtNet(packet)):
                # packet received describing a universe
                channels = packet[16]*256 + packet[17]
                # packets don't have to have all 512 channels
                if (channels <= 512):
                    universeIndex = packet[15]*256 + packet[14]   
                    # universe has float data 0-1
                    universe = getUniverse(universeIndex)
                    # rawUniverse has byte data to detect changes
                    rawUniverse = RawUniverses[universeIndex]
                    universeChanged = False
                    # loop through the channels
                    for i in range(channels):
                        rawValue = packet[i+18]
                        if (rawUniverse[i] != rawValue):
                            # data changed since last time
                            rawUniverse[i] = rawValue    
                            universe[i] = rawValue / 255.0
                            universeChanged = True
                        i += 1 # ++ operator doesn't exist in python
                    # let the main thread know that there's an update
                    if (universeChanged):
                        with UniverseUpdatesLock:
                            UniverseUpdatesPending[universeIndex] = True                        
        except Exception as err:
            print("error in main loop", err)
            # reconnect socket
            disconnect(socket)
            socket = connect()

def updateBlender():
    # runs in the main thread on a timer
    universesPending = []
    # find out which universes updated
    with UniverseUpdatesLock:
        for universeIndex in UniverseUpdatesPending:
            if (UniverseUpdatesPending[universeIndex]):
                # only list universes that we have fixtures for
                if (universeIndex in FixtureUniverses):
                    universesPending.append(universeIndex)
                UniverseUpdatesPending[universeIndex] = False
    
    for universeIndex in universesPending:
        fixtureUniverse = FixtureUniverses[universeIndex]
        universe = getUniverse(universeIndex-1)
        # push the data to blender objects
        for objName in fixtureUniverse:
            mapping = fixtureUniverse[objName]
            obj = mapping["object"]
            fixtureType = FixtureTypes[mapping["fixtureType"]]
            baseAddress = mapping["baseAddress"]                        
            # push the data
            obj.data.color = getColor(universe, baseAddress, fixtureType)
            obj.rotation_euler = getRotation(universe, baseAddress, fixtureType)
            obj.data.spot_size = getZoom(universe, baseAddress, fixtureType)
    return 0.03 # call again in 0.05 seconds - 30fps

def getZoom(universe, baseAddress, fixtureType):
    zoom = universe[baseAddress + fixtureType["zoom"]]
    min = fixtureType["minZoom"]
    max = fixtureType["maxZoom"]
    angle = min + zoom *(max-min)
    return math.radians(angle)

def getRotation(universe, baseAddress, fixtureType):
    pan = universe[baseAddress + fixtureType["pan"]]
    tilt = universe[baseAddress + fixtureType["tilt"]]    
    panRange = fixtureType["panRange"]
    tiltRange = fixtureType["tiltRange"]
    pan -= 0.5
    tilt -= 0.5
    pan *= panRange
    tilt *= tiltRange
    return [0, tilt, pan]

def getColor(universe, baseAddress, fixtureType):
    colorModel = fixtureType["color"]
    if (colorModel == "rgbw"):
        r = universe[baseAddress + fixtureType["red"]]
        g = universe[baseAddress + fixtureType["green"]]
        b = universe[baseAddress + fixtureType["blue"]]
        w = universe[baseAddress + fixtureType["white"]]
        return rgbwToRgb(r,g,b,w)
    elif (colorModel == "cmy"):
        c = universe[baseAddress + fixtureType["cyan"]]
        m = universe[baseAddress + fixtureType["magenta"]]
        y = universe[baseAddress + fixtureType["yellow"]]
        return cmyToRgb(c,m,y)
    
def register():
    init()

def unregister():
    disconnect(ArtNetSocket)

bl_info = {
    "name": "ArtNet Lighting Controller",
    "description": "Combine with Evee to get a real "
                    "time lighting visualizer, controlled "
                    "by any Artnet lighting desk. QLCPlus "
                    "is an example of an open source desk",
    "blender": (2, 80, 0),
    "category": "Lighting",
    "support": "COMMUNITY",
    "author": "Bryan Crotaz",
    "version": (0, 1),
    "wiki_url": "https://github.com/BryanCrotaz/blender-artnet"
}
