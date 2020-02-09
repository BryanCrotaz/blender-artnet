"""Write universe data to blender"""

import bpy

from .color_converter import ColorConverter

class BlenderSynchroniser:
    """Writes universe data to Blender"""

    def __init__(self, universe_store, fixture_store, fixture_type_store):
        self.universe_store = universe_store
        self.fixture_store = fixture_store
        self.fixture_type_store = fixture_type_store
        bpy.app.timers.register(self._update_blender, first_interval=0.1, persistent=True)


    def _update_blender(self):
        """main loop"""
        # runs in the main thread on a timer
        # find out which universes updated
        universes_pending = self.universe_store.get_pending_universes()

        # only deal with universes that we have fixtures for
        universes_pending = list(
            filter(lambda x: x in self.fixture_store.fixture_universe_ids, universes_pending)
        )

        for universe_index in universes_pending:
            self._update_blender_from_universe(universe_index)
        return 0.03 # call again in 0.05 seconds - 30fps

    def _update_blender_from_universe(self, index):
        fixtures = self.fixture_store.get_universe_fixtures(index)
        universe = self.universe_store.get_universe(index)
        # push the data to blender objects
        for obj_name in fixtures:
            mapping = fixtures[obj_name]
            obj = mapping["object"]
            if obj is not None:
                fixture_type = self.fixture_type_store.get_fixture_type(mapping["fixture_type"])
                base_address = mapping["base_address"]
                # push the data
                obj.data.color = self._get_color(universe, base_address, fixture_type)
                obj.rotation_euler = self._get_rotation(universe, base_address, fixture_type)
                obj.data.spot_size = self._get_zoom(universe, base_address, fixture_type)

    def _get_zoom(self, universe, base_address, fixture_type):
        zoom = universe[base_address + fixture_type["zoom"]]
        min_zoom = fixture_type["minZoom"]
        max_zoom = fixture_type["maxZoom"]
        angle = min_zoom + zoom *(max_zoom-min_zoom)
        return angle

    def _get_rotation(self, universe, base_address, fixture_type):
        pan = universe[base_address + fixture_type["pan"]]
        tilt = universe[base_address + fixture_type["tilt"]]
        pan_range = fixture_type["panRange"]
        tilt_range = fixture_type["tiltRange"]
        pan -= 0.5
        tilt -= 0.5
        pan *= pan_range
        tilt *= tilt_range
        return [0, tilt, pan]

    def _get_color(self, universe, base_address, fixture_type):
        color_model = fixture_type["color"]
        if color_model == "rgbw":
            red = universe[base_address + fixture_type["red"]]
            green = universe[base_address + fixture_type["green"]]
            blue = universe[base_address + fixture_type["blue"]]
            white = universe[base_address + fixture_type["white"]]
            return ColorConverter.rgbw_to_rgb(red, green, blue, white)
        elif color_model == "cmy":
            cyan = universe[base_address + fixture_type["cyan"]]
            magenta = universe[base_address + fixture_type["magenta"]]
            yellow = universe[base_address + fixture_type["yellow"]]
            return ColorConverter.cmy_to_rgb(cyan, magenta, yellow)
