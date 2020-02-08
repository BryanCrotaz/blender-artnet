"""Fixture Store"""

import bpy

class FixtureStore:
    """Stores the fixtures mapped to Blender lights"""

    def __init__(self):
        self.load_objects_from_scene()

    def load_objects_from_scene(self):
        # grab the objects to be mapped to data
        objects = bpy.context.scene.objects
        for universe_index in self._fixture_universes:
            universe = self._fixture_universes[universe_index]
            for name in universe:
                # grab the blender named object so we don't need to do this every frame
                if name in objects:
                    obj = objects[name]
                    universe[name]["object"] = obj
                    # base address is 1-based so subtract 1 from it
                    universe[name]["base_address"] -= 1
                    obj.rotation_mode = "XYZ"
                else:
                    universe[name]["object"] = None

    # TODO: Add a ui to add lights to this dictionary
    _fixture_universes = {
        2: {
            "Spot.027": {
                "fixture_type": "wash",
                "base_address": 147
            },
            "Spot.028": {
                "fixture_type": "wash",
                "base_address": 180
            },
            "Spot.026": {
                "fixture_type": "wash",
                "base_address": 246
            },
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

    @property
    def fixture_universe_ids(self):
        """Returns a list of universe ids which have fixtures defined"""
        return self._fixture_universes.keys()

    def get_fixture_universe(self, index):
        """Get the fixtures defined for a particular universe"""
        return self._fixture_universes[index]
