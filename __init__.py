"""
This blender addon maps Art-Net DMX onto blender lights in real time.
Use with Evee to live-preview your lighting.
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

import bpy
from bpy.app.handlers import persistent

from .src.artnet_socket import ArtNetSocket
from .src.universe_store import UniverseStore
from .src.fixture_store import FixtureStore
from .src.fixture_type_store import FixtureTypeStore
from .src.blender_sync import BlenderSynchroniser

global_data = {
    ArtNetSocket: ArtNetSocket,
    BlenderSynchroniser: BlenderSynchroniser,
    FixtureStore: FixtureStore
}

bl_info = {
    "name": "ArtNet Lighting Controller",
    "description": "Combine with Evee to get a real "
                   "time lighting visualizer, controlled "
                   "by any Artnet lighting desk. QLCPlus "
                   "is an example of an open source desk "
                   "you can use with this.",
    "blender": (2, 80, 0),
    "category": "Lighting",
    "support": "COMMUNITY",
    "author": "Bryan Crotaz",
    "version": (1,0),
    "wiki_url": "https://github.com/BryanCrotaz/blender-artnet"
}

def _setup():
    # can't get at scene in initialization so run from a timer
    global_data["FixtureStore"] = FixtureStore()
    fixture_types = FixtureTypeStore()
    universes = UniverseStore()
    global_data["ArtNetSocket"] = ArtNetSocket(universes)
    global_data["BlenderSynchroniser"] = BlenderSynchroniser(universes, global_data["FixtureStore"], fixture_types)
    return None

@persistent
def _load_objects_from_scene(_, __):
    global_data["FixtureStore"].load_objects_from_scene()

def register():
    """Called from Blender"""
    global_data["ArtNetSocket"] = None
    global_data["BlenderSynchroniser"] = None
    bpy.app.timers.register(_setup, first_interval=0.1)
    bpy.app.handlers.load_post.append(_load_objects_from_scene)

def unregister():
    """Called from Blender"""
    if global_data["ArtNetSocket"] is not None:
        global_data["ArtNetSocket"].disconnect()
    if bpy.app.timers.is_registered(_setup):
        bpy.app.timers.unregister(_setup)
