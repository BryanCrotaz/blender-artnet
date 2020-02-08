"""
This blender addon maps Art-Net DMX onto blender lights in real time. Use with Evee to live-preview your lighting.
"""

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

import socket
import threading
import math

import bpy

Universes = []  # float data 0-1
raw_universes = []  # byte data 0-255
ART_NET_SOCKET = None
UDP_IP = "0.0.0.0"
UDP_PORT = 6454


fixture_types = {
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
            0: [1, 1, 1],
            9: [1, 0, 0],
            18: [0, 0, 1],
            27: [0, 1, 1],
            37: [0.2, 1, 0.2],
            46: [1, 0, 1]
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

fixture_universes = {
    2: {
        "Spot.027": {
            "fixture_type": "wash",
            "base_address": 147
        },
        "Spot.028": {
            "fixture_type": "wash",
            "base_address": 180
        },
     #   "Spot.012": {
     #       "fixture_type": "wash",
     #       "base_address": 181
     #   },
        "Spot.026": {
            "fixture_type": "wash",
            "base_address": 246
        },
     #   "Spot.012": {
     #       "fixture_type": "wash",
      #      "base_address": 181
     #   }
    },
    3: {
        "Spot.015": {
            "fixture_type": "wash",
            "base_address": 247
        },
        "Spot.014": {
            "fixture_type": "wash",
            "base_address": 214
        },
        "Spot.012": {
            "fixture_type": "wash",
            "base_address": 181
        },
        "Spot.016": {
            "fixture_type": "wash",
            "base_address": 148
        },
        "Spot.013": {
            "fixture_type": "wash",
            "base_address": 115
        },
        "Spot.017": {
            "fixture_type": "wash",
            "base_address": 82
        },
        "Spot.018": {
            "fixture_type": "wash",
            "base_address": 49
        }
    },
    4: {
        "Spot.020": {
            "fixture_type": "wash",
            "base_address": 247
        },
        "Spot.019": {
            "fixture_type": "wash",
            "base_address": 214
        },
        "Spot.021": {
            "fixture_type": "wash",
            "base_address": 181
        },
        "Spot.022": {
            "fixture_type": "wash",
            "base_address": 148
        },
        "Spot.023": {
            "fixture_type": "wash",
            "base_address": 115
        },
        "Spot.024": {
            "fixture_type": "wash",
            "base_address": 82
        },
        "Spot.025": {
            "fixture_type": "wash",
            "base_address": 49
        }
    }
}

UniverseUpdatesPending = {} # map of universe indices : bool
UniverseUpdatesLock = threading.Lock()

def get_universe(index):
    while len(Universes) <= index:
        universe = []
        for _ in range(512):
            universe.append(0)
        Universes.append(universe)
        raw_universe = []
        for _ in range(512):
            raw_universe.append(0)
        raw_universes.append(raw_universe)
    return Universes[index]

def init():
    setup()
    global ART_NET_SOCKET
    ART_NET_SOCKET = connect()
    if ART_NET_SOCKET is not None:
        thread = threading.Thread(target=socketLoop, args=(ART_NET_SOCKET,))
        thread.start()
    bpy.app.timers.register(updateBlender, first_interval=0.1, persistent=True)

def connect():
    try:
        global ART_NET_SOCKET
        ART_NET_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        ART_NET_SOCKET.bind((UDP_IP, UDP_PORT))
        ART_NET_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # blocking socket as we're listening in a background thread
        ART_NET_SOCKET.setblocking(1)
        return ART_NET_SOCKET
    except Exception as err:
        print("error while connecting", err)
        disconnect(ART_NET_SOCKET)
        return None

def disconnect(a_socket):
    if a_socket is not None:
        a_socket.close()
    global ART_NET_SOCKET
    ART_NET_SOCKET = None

def isArtNet(packet):
    return (packet[0] == 65
            and packet[1] == 114
            and packet[2] == 116
            and packet[8] == 0
            and packet[9] == 80) # known header

def rgbwToRgb(red, green, blue, white):
    r = (red + white/3) * 3 / 4
    g = (green + white/3) * 3 / 4
    b = (blue + white/3) * 3 / 4
    return [r, g, b]    

def cmyToRgb(cyan, magenta, yellow):
    r = 1-cyan
    g = 1-magenta
    b = 1-yellow
    return [r, g, b]    

def setup():
    # grab the objects to be mapped to data
    objects = bpy.context.scene.objects
    for universe in fixture_universes:
        u = fixture_universes[universe]
        for name in u:
            # grab the blender named object so we don't need to do this every frame
            obj = objects[name]
            u[name]["object"] = obj
            # base address is 1-based so subtract 1 from it
            u[name]["base_address"] -= 1
            obj.rotation_mode = "XYZ"
    for fixture_type in fixture_types:
        ft = fixture_types[fixture_type]
        # convert degrees to radians so we don't do this every frame
        ft["panRange"] = math.radians(ft["panRange"])
        ft["tiltRange"] = math.radians(ft["tiltRange"])

def socketLoop(artNetSocket):
    # runs in a background thread
    # must not access blender directly
    thread_socket = artNetSocket
#    for t in range(10):
    while True:
        try:
            # read the packet
            packet, _addr = thread_socket.recvfrom(1024)
            if len(packet) > 18 and isArtNet(packet):
                # packet received describing a universe
                channels = packet[16]*256 + packet[17]
                # packets don't have to have all 512 channels
                if channels <= 512:
                    universe_index = packet[15]*256 + packet[14]   
                    # universe has float data 0-1
                    universe = get_universe(universe_index)
                    # raw_universe has byte data to detect changes
                    raw_universe = raw_universes[universe_index]
                    universe_changed = False
                    # loop through the channels
                    for i in range(channels):
                        raw_value = packet[i+18]
                        if raw_universe[i] != raw_value:
                            # data changed since last time
                            raw_universe[i] = raw_value
                            universe[i] = raw_value / 255.0
                            universe_changed = True
                        i += 1 # ++ operator doesn't exist in python
                    # let the main thread know that there's an update
                    if universe_changed:
                        with UniverseUpdatesLock:
                            UniverseUpdatesPending[universe_index] = True
        except Exception as err:
            print("error in main loop", err)
            # reconnect socket
            disconnect(thread_socket)
            thread_socket = connect()

def updateBlender():
    # runs in the main thread on a timer
    universes_pending = []
    # find out which universes updated
    with UniverseUpdatesLock:
        for universe_index in UniverseUpdatesPending:
            if UniverseUpdatesPending[universe_index]:
                # only list universes that we have fixtures for
                if universe_index in fixture_universes:
                    universes_pending.append(universe_index)
                UniverseUpdatesPending[universe_index] = False

    for universe_index in universes_pending:
        fixture_universe = fixture_universes[universe_index]
        universe = get_universe(universe_index-1)
        # push the data to blender objects
        for obj_name in fixture_universe:
            mapping = fixture_universe[obj_name]
            obj = mapping["object"]
            fixture_type = fixture_types[mapping["fixture_type"]]
            base_address = mapping["base_address"]                        
            # push the data
            obj.data.color = getColor(universe, base_address, fixture_type)
            obj.rotation_euler = getRotation(universe, base_address, fixture_type)
            obj.data.spot_size = getZoom(universe, base_address, fixture_type)
    return 0.03 # call again in 0.05 seconds - 30fps

def getZoom(universe, base_address, fixture_type):
    zoom = universe[base_address + fixture_type["zoom"]]
    min_zoom = fixture_type["minZoom"]
    max_zoom = fixture_type["maxZoom"]
    angle = min + zoom *(max_zoom-min_zoom)
    return math.radians(angle)

def getRotation(universe, base_address, fixture_type):
    pan = universe[base_address + fixture_type["pan"]]
    tilt = universe[base_address + fixture_type["tilt"]]    
    pan_range = fixture_type["panRange"]
    tilt_range = fixture_type["tiltRange"]
    pan -= 0.5
    tilt -= 0.5
    pan *= pan_range
    tilt *= tilt_range
    return [0, tilt, pan]

def getColor(universe, base_address, fixture_type):
    color_model = fixture_type["color"]
    if color_model == "rgbw":
        r = universe[base_address + fixture_type["red"]]
        g = universe[base_address + fixture_type["green"]]
        b = universe[base_address + fixture_type["blue"]]
        w = universe[base_address + fixture_type["white"]]
        return rgbwToRgb(r, g, b, w)
    elif color_model == "cmy":
        c = universe[base_address + fixture_type["cyan"]]
        m = universe[base_address + fixture_type["magenta"]]
        y = universe[base_address + fixture_type["yellow"]]
        return cmyToRgb(c, m, y)

def register():
    init()

def unregister():
    disconnect(ART_NET_SOCKET)

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
