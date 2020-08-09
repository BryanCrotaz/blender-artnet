"""Fixture Store"""

import bpy

class FixtureStore:
    """Stores the fixtures mapped to Blender lights"""

    def __init__(self):
        self.load_objects_from_scene()

    _fixture_universes = {}

    def load_objects_from_scene(self):
        """Find the ArtNet enabled objects in the scene"""
        objects = bpy.context.scene.objects
        for obj in objects:
            if obj.data and "artnet_enabled" in obj.data and obj.data.artnet_enabled:
                self._add_object(obj)

    @property
    def fixture_universe_ids(self):
        """Returns a list of universe ids which have fixtures defined"""
        return self._fixture_universes.keys()

    def get_universe_fixtures(self, index):
        """Get the fixtures defined for a particular universe"""
        return self._fixture_universes[index]

    def get_universe(self, obj: bpy.types.Object):
        """Get the universe index for a particular scene object"""
        for universe_index in self._fixture_universes:
            universe = self._fixture_universes[universe_index]
            for name in universe:
                if obj == universe[name]["object"]:
                    # found it
                    return universe_index
        # didn't find it
        return None

    def remove_object_by_name(self, name):
        """Remove a particular scene object"""
        for universe_index in self._fixture_universes:
            universe = self._fixture_universes[universe_index]
            if name in universe:
                del universe[name] # for safety look in all universes

    def _remove_object(self, obj: bpy.types.Object):
        """Remove a particular scene object"""
        for universe_index in self._fixture_universes:
            universe = self._fixture_universes[universe_index]
            for name in universe:
                if obj == universe[name]["object"]:
                    # found it
                    del universe[name]
                    return

    def _add_object(self, obj: bpy.types.Object):
        """Add a scene object"""
        if obj.data.artnet_universe is None:
            return
        if not obj.data.artnet_universe in self._fixture_universes:
            self._fixture_universes[obj.data.artnet_universe] = {}
        universe = self._fixture_universes[obj.data.artnet_universe]
        fixture = {}
        fixture["object"] = obj
        fixture["fixture_type"] = obj.data.artnet_fixture_type
        # base address is 1-based so subtract 1 from it
        fixture["base_address"] = obj.data.artnet_base_address - 1
        universe[obj.name] = fixture
        obj.rotation_mode = "XYZ"

    def update_object(self, obj: bpy.types.Object):
        """Update an object in our store after it was changed in the UI"""
        self._remove_object(obj)
        if obj.data.artnet_enabled:
            self._add_object(obj)
