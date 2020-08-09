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
from bpy.props import BoolProperty, IntProperty, StringProperty, EnumProperty

from .src.artnet_socket import ArtNetSocket
from .src.universe_store import UniverseStore, ALL_UNIVERSES
from .src.fixture_store import FixtureStore
from .src.fixture_type_store import FixtureTypeStore
from .src.blender_sync import BlenderSynchroniser

from .src.ui.light_panel import LightArtNetPanel

GLOBAL_DATA = {
    ArtNetSocket: ArtNetSocket,
    BlenderSynchroniser: BlenderSynchroniser,
    FixtureStore: FixtureStore,
}

PAN_TILT_TARGETS = [
    ('lx', 'Light x', 'tilt around light x axis', 0),
    ('ly', 'Light y', 'tilt around light y axis', 1),
    ('lz', 'Light z', 'tilt around light z axis', 2),
    None,
    ('px', 'Parent x', 'tilt around parent x axis', 3),
    ('py', 'Parent y', 'tilt around parent y axis', 4),
    ('pz', 'Parent z', 'tilt around parent z axis', 5),
    None,
    ('gpx', 'Grandparent x', 'tilt around grandparent x axis', 6),
    ('gpy', 'Grandparent y', 'tilt around grandparent y axis', 7),
    ('gpz', 'Grandparent z', 'tilt around grandparent z axis', 8),
    None,
    ('none', 'Ignore', 'ignore tilt from Artnet', 9)
]

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
    "version": (1, 5),
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
        name="Enabled",
        update=_light_data_change
    )
    bpy.types.Light.artnet_universe = IntProperty(
        name="Universe",
        update=_light_data_change
    )
    bpy.types.Light.artnet_fixture_type = StringProperty(
        name="Fixture Type",
        update=_light_data_change
    )
    bpy.types.Light.artnet_base_address = IntProperty(
        name="Base DMX Address",
        update=_light_data_change
    )
    bpy.types.Light.artnet_pan_target = EnumProperty(
        name="Pan Target",
        items=PAN_TILT_TARGETS,
        default="lx",
        update=_light_data_change,
        get=get_pan_target,
        set=set_pan_target
    )
    bpy.types.Light.artnet_tilt_target = EnumProperty(   
        name="Tilt Target",
        items=PAN_TILT_TARGETS,
        default="lz",
        update=_light_data_change,
        get=get_tilt_target,
        set=set_tilt_target
    )
    bpy.types.Light.artnet_old_pan_target = EnumProperty(
        name="Old Pan Target",
        items=PAN_TILT_TARGETS,
        default="none"
    )
    bpy.types.Light.artnet_old_tilt_target = EnumProperty(
        name="Old Tilt Target",
        items=PAN_TILT_TARGETS,
        default="none"
    )
    # register UI Panel
    bpy.utils.register_class(LightArtNetPanel)

def get_pan_target(self):
    return self.get("artnet_pan_target", 2)

def set_pan_target(self, value):
    self.artnet_old_pan_target = get_pan_tilt_target_from_int(self.get("artnet_pan_target", 9))   
    self["artnet_pan_target"] = value

def get_pan_tilt_target_from_int(value):
    for target in PAN_TILT_TARGETS:
        if target is not None:
            if target[3] == value:
                return target[0]

def get_tilt_target(self):
    return self.get("artnet_tilt_target", 0)

def set_tilt_target(self, value):
    self.artnet_old_tilt_target = get_pan_tilt_target_from_int(self.get("artnet_tilt_target", 9))   
    self["artnet_tilt_target"] = value

def unregister():
    """Called from Blender"""
    if GLOBAL_DATA["ArtNetSocket"] is not None:
        GLOBAL_DATA["ArtNetSocket"].disconnect()
        GLOBAL_DATA["ArtNetSocket"].shutdown()
    if bpy.app.timers.is_registered(_setup):
        bpy.app.timers.unregister(_setup)
    # unregister ui panel
    bpy.utils.unregister_class(LightArtNetPanel)
    # remove light properties
    del bpy.types.Light.artnet_enabled
    del bpy.types.Light.artnet_fixture_type
    del bpy.types.Light.artnet_universe
    del bpy.types.Light.artnet_base_address
    del bpy.types.Light.artnet_pan_target
    del bpy.types.Light.artnet_tilt_target

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
