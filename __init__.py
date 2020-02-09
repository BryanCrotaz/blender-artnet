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
from bpy.props import BoolProperty, IntProperty, StringProperty

from .src.artnet_socket import ArtNetSocket
from .src.universe_store import UniverseStore, ALL_UNIVERSES
from .src.fixture_store import FixtureStore
from .src.fixture_type_store import FixtureTypeStore
from .src.blender_sync import BlenderSynchroniser

from .src.ui.light_panel import LightArtNetPanel

GLOBAL_DATA = {
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
    "version": (1, 0),
    "wiki_url": "https://github.com/BryanCrotaz/blender-artnet"
}

def _setup():
    # can't get at scene in initialization so run from a timer
    fixture_store = FixtureStore()
    GLOBAL_DATA["FixtureStore"] = fixture_store
    fixture_types = FixtureTypeStore()
    GLOBAL_DATA["UniverseStore"] = UniverseStore()
    universes = GLOBAL_DATA["UniverseStore"]
    GLOBAL_DATA["ArtNetSocket"] = ArtNetSocket(universes)
    GLOBAL_DATA["BlenderSynchroniser"] = BlenderSynchroniser(
        universes,
        fixture_store,
        fixture_types
    )
    fixture_store.load_objects_from_scene()
    universes.notify_universe_change(ALL_UNIVERSES)
    return None

@persistent
def _on_file_loaded(_, __):
    if "FixtureStore" in GLOBAL_DATA:
        GLOBAL_DATA["FixtureStore"].load_objects_from_scene()
        universes = GLOBAL_DATA["UniverseStore"]
        universes.notify_universe_change(ALL_UNIVERSES)

def register():
    """Called from Blender"""
    GLOBAL_DATA["ArtNetSocket"] = None
    GLOBAL_DATA["BlenderSynchroniser"] = None
    bpy.app.timers.register(_setup, first_interval=0.1)
    # load objects when file is loaded
    bpy.app.handlers.load_post.append(_on_file_loaded)
    # add light properties
    bpy.types.Light.artnet_enabled = BoolProperty(
        name="artnet_enabled",
        update=_light_data_change
    )
    bpy.types.Light.artnet_universe = IntProperty(
        name="artnet_universe",
        update=_light_data_change
    )
    bpy.types.Light.artnet_fixture_type = StringProperty(
        name="artnet_fixture_type",
        update=_light_data_change
    )
    bpy.types.Light.artnet_base_address = IntProperty(
        name="artnet_base_address",
        update=_light_data_change
    )
    # register UI Panel
    bpy.utils.register_class(LightArtNetPanel)

def unregister():
    """Called from Blender"""
    if GLOBAL_DATA["ArtNetSocket"] is not None:
        GLOBAL_DATA["ArtNetSocket"].disconnect()
    if bpy.app.timers.is_registered(_setup):
        bpy.app.timers.unregister(_setup)
    # unregister ui panel
    bpy.utils.unregister_class(LightArtNetPanel)
    # remove light properties
    del bpy.types.Light.artnet_enabled
    del bpy.types.Light.artnet_fixture_type
    del bpy.types.Light.artnet_universe
    del bpy.types.Light.artnet_base_address

def _light_data_change(data, context):
    """One of the lights changed in the scene - update our internal data"""
    fixtures = GLOBAL_DATA["FixtureStore"]
    old_universe = fixtures.get_universe(context.object)
    fixtures.update_object(context.object)
    # apply the DMX data to get it up to date
    universes = GLOBAL_DATA["UniverseStore"]
    if old_universe is not None:
        universes.notify_universe_change(old_universe)
    if data.artnet_enabled:
        universes.notify_universe_change(data.artnet_universe)
