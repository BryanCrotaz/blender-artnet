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
        raw_universe = self.universe_store.get_raw_universe(index)
        # push the data to blender objects
        deleted_object_names = []
        for obj_name in fixtures:
            try:
                mapping = fixtures[obj_name]
                obj = mapping["object"]
                if obj is not None:
                    if obj.type == "LIGHT":
                        if obj.data.type == "SPOT":
                            self.update_spot_light(obj, mapping, universe, raw_universe)
                        elif obj.data.type == "AREA":
                            self.update_area_light(obj, mapping, universe, raw_universe)
            except ReferenceError:
                # object got deleted
                deleted_object_names.append(obj_name)

        for name in deleted_object_names:
            self.fixture_store.remove_object_by_name(name)

    def update_spot_light(self, obj, mapping, universe, raw_universe):
        fixture_type = self.fixture_type_store.get_fixture_type(mapping["fixture_type"])
        if fixture_type is not None:
            base_address = mapping["base_address"]
            # push the data
            obj.data.color = self._get_color(universe, raw_universe, base_address, fixture_type) or [0, 0, 0]
            obj.data.energy = self._get_power(universe, base_address, fixture_type)
            self._set_rotation(obj, universe, base_address, fixture_type)
            obj.data.spot_size = self._get_zoom(universe, base_address, fixture_type) or 0

    def update_area_light(self, obj, mapping, universe, raw_universe):
        fixture_type = self.fixture_type_store.get_fixture_type(mapping["fixture_type"])
        if fixture_type is not None:
            base_address = mapping["base_address"]
            # push the data
            obj.data.color = self._get_color(universe, raw_universe, base_address, fixture_type) or [0, 0, 0]
            obj.data.energy = self._get_power(universe, base_address, fixture_type)
            self._set_rotation(obj, universe, base_address, fixture_type)

    def _get_zoom(self, universe, base_address, fixture_type):
        try:
            zoom = universe[base_address + fixture_type["zoom"]]
            if "zoom_invert" in fixture_type and fixture_type["zoom_invert"]:
                zoom = 1 - zoom
            min_zoom = fixture_type["minZoom"]
            max_zoom = fixture_type["maxZoom"]
            angle = min_zoom + zoom *(max_zoom-min_zoom)
            return angle
        except IndexError:
            return min_zoom # because no data yet

    def _get_power(self, universe, base_address, fixture_type):
        try:
            dimmer = universe[base_address + fixture_type["dimmer"]]
            lumens = fixture_type["lumens"]
            power = lumens * dimmer / 6.83
            return power
        except IndexError:
            return 1000 # because no data yet

    def _get_rotation(self, universe, base_address, fixture_type):
        pan = universe[base_address + fixture_type["pan"]]
        tilt = universe[base_address + fixture_type["tilt"]]
        pan_range = fixture_type["panRange"]
        tilt_range = fixture_type["tiltRange"]
        pan -= 0.5
        tilt -= 0.5
        pan *= pan_range
        tilt *= tilt_range
        return [pan, tilt]

    def _set_rotation(self, obj, universe, base_address, fixture_type):
        if obj.data.artnet_old_pan_target != "none":
            self.set_rotation_on_target(obj, obj.data.artnet_old_pan_target, 0)
            obj.data.artnet_old_pan_target = "none"

        if obj.data.artnet_old_tilt_target != "none":
            self.set_rotation_on_target(obj, obj.data.artnet_old_tilt_target, 0)
            obj.data.artnet_old_tilt_target = "none"

        try:
            rotation = self._get_rotation(universe, base_address, fixture_type)
        except IndexError:
            print ('_set_rotation error')
            pass # null movement, because no data yet
        pan = rotation[0]
        tilt = rotation[1]
        self.set_rotation_on_target(obj, obj.data.artnet_pan_target, pan)
        self.set_rotation_on_target(obj, obj.data.artnet_tilt_target, tilt)

    def set_rotation_on_target(self, obj, target, rotation):
        if target == "lx":
            obj.rotation_euler.x = rotation
        elif target == "ly":
            obj.rotation_euler.y = rotation
        elif target == "lz":
            obj.rotation_euler.z = rotation
        elif obj.parent is not None:
            if target == "px":
                obj.parent.rotation_euler.x = rotation
            elif target == "py":
                obj.parent.rotation_euler.y = rotation
            elif target == "pz":
                obj.parent.rotation_euler.z = rotation
            elif obj.parent.parent is not None:
                if target == "gpx":
                    obj.parent.parent.rotation_euler.x = rotation
                elif target == "gpy":
                    obj.parent.parent.rotation_euler.y = rotation
                elif target == "gpz":
                    obj.parent.parent.rotation_euler.z = rotation

    def _get_color(self, universe, rawUniverse, base_address, fixture_type):
        color_mode = fixture_type["colorMode"]
        try:
            if color_mode == "rgbw":
                red = universe[base_address + fixture_type["red"]]
                green = universe[base_address + fixture_type["green"]]
                blue = universe[base_address + fixture_type["blue"]]
                white = universe[base_address + fixture_type["white"]]
                return ColorConverter.rgbw_to_rgb(red, green, blue, white)
            elif color_mode == "cmy":
                cyan = universe[base_address + fixture_type["cyan"]]
                magenta = universe[base_address + fixture_type["magenta"]]
                yellow = universe[base_address + fixture_type["yellow"]]
                return ColorConverter.cmy_to_rgb(cyan, magenta, yellow)
            elif color_mode == "wheel":
                position = rawUniverse[base_address + fixture_type["color"]]
                wheel = fixture_type["colorWheel"]
                return ColorConverter.wheel_to_rgb(wheel, position, True)
            else:
                return [1, 1, 1] # white
        except IndexError:
            return [0, 0, 0] # black, because no data yet
