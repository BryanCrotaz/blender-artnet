"""Write universe data to blender"""

import bpy

from .color_converter import ColorConverter

class BlenderSynchroniser:
    """Writes universe data to Blender"""

    artnet_control_state = 'listen'
    frame_current = 0

    def __init__(self, universe_store, fixture_store, fixture_type_store):
        self.universe_store = universe_store
        self.fixture_store = fixture_store
        self.fixture_type_store = fixture_type_store
        self.add_keyframes = False

        bpy.app.timers.register(self._update_blender, first_interval=0.1, persistent=True)

    def __del__(self):
        bpy.app.timers.unregister(self._update_blender)

    def _update_blender(self):
        """main loop"""
        # runs in the main thread on a timer
        # find out which universes updated
        # returns map of universe index to list of changed channels
        universe_changes_pending: {} = self.universe_store.get_pending_universes()

        # only deal with universes that we have fixtures for
        universes_pending = list(
            filter(lambda x: x in self.fixture_store.fixture_universe_ids, universe_changes_pending.keys())
        )

        control_state = self.artnet_control_state
        if control_state != 'play':
            if control_state == 'record':
                self.add_keyframes = True
                self.frame_current = bpy.context.scene.frame_current
            else:
                self.add_keyframes = False

            for universe_index in universes_pending:
                self._update_blender_from_universe(universe_index, universe_changes_pending[universe_index])

        return 0.03 # call again in 0.05 seconds - 30fps

    def _update_blender_from_universe(self, index, channels):
        fixtures = self.fixture_store.get_fixtures_for_universe(index)
        universe = self.universe_store.get_universe(index)
        raw_universe = self.universe_store.get_raw_universe(index)
        # push the data to blender objects
        deleted_object_names = []
        for obj_name in fixtures:
            # todo remove this try block for speed
            try:
                mapping = fixtures[obj_name]
                obj = mapping["object"]
                if obj is not None:
                    if obj.type == "LIGHT":
                        if obj.data.type == "SPOT":
                            self.update_spot_light(obj, mapping, universe, raw_universe, channels)
                        elif obj.data.type == "AREA":
                            self.update_area_light(obj, mapping, universe, raw_universe, channels)
                        elif obj.data.type == "POINT":
                            self.update_point_light(obj, mapping, universe, raw_universe, channels)
            except ReferenceError:
                # object got deleted
                deleted_object_names.append(obj_name)

        for name in deleted_object_names:
            self.fixture_store.remove_object_by_name(name)

    def update_spot_light(self, obj, mapping, universe, raw_universe, channels):
        fixture_type = self.fixture_type_store.get_fixture_type(mapping["fixture_type"])
        if fixture_type is not None:
            base_address = mapping["base_address"]
            # push the data
            color = self._get_color(universe, raw_universe, base_address, fixture_type, channels)
            if color is not None:
                obj.data.color = color
                if self.add_keyframes:
                    obj.data.keyframe_insert(data_path="color",
                                             frame=self.frame_current)

            energy = self._get_power(universe, base_address, fixture_type, channels)
            if energy is not None:
                obj.data.energy = energy
                if self.add_keyframes:
                    obj.data.keyframe_insert(data_path="energy",
                                            frame=self.frame_current)

            self._set_rotation(obj, universe, base_address, fixture_type, channels)

            zoom = self._get_zoom(universe, base_address, fixture_type, channels)
            if  zoom is not None:
                obj.data.spot_size = zoom
                if self.add_keyframes:
                    obj.data.keyframe_insert(data_path="spot_size",
                                             frame=self.frame_current)

    def update_area_light(self, obj, mapping, universe, raw_universe, channels):
        fixture_type = self.fixture_type_store.get_fixture_type(mapping["fixture_type"])
        if fixture_type is not None:
            base_address = mapping["base_address"]
            # push the data
            color = self._get_color(universe, raw_universe, base_address, fixture_type, channels)
            if color is not None:
                obj.data.color = color
                if self.add_keyframes:
                    obj.data.keyframe_insert(data_path="color",
                                            frame=self.frame_current)

            energy = self._get_power(universe, base_address, fixture_type, channels)
            if energy is not None:
                obj.data.energy = energy
                if self.add_keyframes:
                    obj.data.keyframe_insert(data_path="energy",
                                             frame=self.frame_current)
                                             
            self._set_rotation(obj, universe, base_address, fixture_type, channels)

    def update_point_light(self, obj, mapping, universe, raw_universe, channels):
        fixture_type = self.fixture_type_store.get_fixture_type(mapping["fixture_type"])
        if fixture_type is not None:
            base_address = mapping["base_address"]
            # push the data
            color = self._get_color(universe, raw_universe, base_address, fixture_type, channels)
            if color is not None:
                obj.data.color = color
                if self.add_keyframes:
                    obj.data.keyframe_insert(data_path="color",
                                             frame=self.frame_current)

            energy = self._get_power(universe, base_address, fixture_type, channels)
            if energy is not None:
                obj.data.energy = energy
                if self.add_keyframes:
                    obj.data.keyframe_insert(data_path="energy",
                                             frame=self.frame_current)

    def _get_zoom(self, universe, base_address, fixture_type, channels):
        # todo remove this try block for speed
        try:
            zoom_channel = base_address + fixture_type["zoom"]
            if zoom_channel in channels:
                min_zoom = fixture_type["minZoom"]
                max_zoom = fixture_type["maxZoom"]
                zoom = universe[zoom_channel]
                if "zoom_invert" in fixture_type and fixture_type["zoom_invert"]:
                    zoom = 1 - zoom
                angle = min_zoom + zoom *(max_zoom-min_zoom)
                return angle
            return None
        except IndexError:
            return None

    def _get_power(self, universe, base_address, fixture_type, channels):
        # todo remove this try block for speed
        try:
            dimmer_channel = base_address + fixture_type["dimmer"]
            if dimmer_channel in channels:
                dimmer = universe[dimmer_channel]
                lumens = fixture_type["lumens"]
                power = lumens * dimmer / 6.83
                return power
            return None
        except IndexError:
            return None

    def _get_rotation(self, universe, base_address, fixture_type, channels):
        pan = None
        tilt = None
        if base_address + fixture_type["pan"] in channels:
            pan = universe[base_address + fixture_type["pan"]]
            pan_range = fixture_type["panRange"]
            pan -= 0.5
            pan *= pan_range

        if base_address + fixture_type["tilt"] in channels:
            tilt = universe[base_address + fixture_type["tilt"]]
            tilt_range = fixture_type["tiltRange"]
            tilt -= 0.5
            tilt *= tilt_range
        return [pan, tilt]

    def _set_rotation(self, obj, universe, base_address, fixture_type, channels):
        if obj.data.artnet_old_pan_target != "none":
            self.set_rotation_on_target(obj, obj.data.artnet_old_pan_target, 0)
            obj.data.artnet_old_pan_target = "none"

        if obj.data.artnet_old_tilt_target != "none":
            self.set_rotation_on_target(obj, obj.data.artnet_old_tilt_target, 0)
            obj.data.artnet_old_tilt_target = "none"

        # todo remove this try block for speed
        try:
            rotation = self._get_rotation(universe, base_address, fixture_type, channels)
        except IndexError:
            print('_set_rotation error')
            return None # null movement, because no data yet
        pan = rotation[0]
        tilt = rotation[1]
        if pan is not None:
            self.set_rotation_on_target(obj, obj.data.artnet_pan_target, pan)
        if tilt is not None:
            self.set_rotation_on_target(obj, obj.data.artnet_tilt_target, tilt)

    def set_rotation_on_target(self, obj, target, rotation):
        kf_target = None
        if target == "lx":
            obj.rotation_euler.x = rotation
            kf_target = obj
            kf_index = 0
        elif target == "ly":
            obj.rotation_euler.y = rotation
            kf_target = obj
            kf_index = 1
        elif target == "lz":
            obj.rotation_euler.z = rotation
            kf_target = obj
            kf_index = 2
        elif obj.parent is not None:
            if target == "px":
                obj.parent.rotation_euler.x = rotation
                kf_target = obj.parent
                kf_index = 0
            elif target == "py":
                obj.parent.rotation_euler.y = rotation
                kf_target = obj.parent
                kf_index = 1
            elif target == "pz":
                obj.parent.rotation_euler.z = rotation
                kf_target = obj.parent
                kf_index = 2
            elif obj.parent.parent is not None:
                if target == "gpx":
                    obj.parent.parent.rotation_euler.x = rotation
                    kf_target = obj.parent.parent
                    kf_index = 0
                elif target == "gpy":
                    obj.parent.parent.rotation_euler.y = rotation
                    kf_target = obj.parent.parent
                    kf_index = 1
                elif target == "gpz":
                    obj.parent.parent.rotation_euler.z = rotation
                    kf_target = obj.parent.parent
                    kf_index = 2

        if (kf_target is not None) and self.add_keyframes:
            kf_target.keyframe_insert(data_path="rotation_euler",
                                      frame=self.frame_current,
                                      index = kf_index)

    def _get_color(self, universe, rawUniverse, base_address, fixture_type, channels):
        color_mode = fixture_type["colorMode"]
        # todo remove this try block for speed
        try:
            if color_mode == "rgbw":
                red_channel = base_address + fixture_type["red"]
                green_channel = base_address + fixture_type["green"]
                blue_channel = base_address + fixture_type["blue"]
                white_channel = base_address + fixture_type["white"]
                if (red_channel in channels or green_channel in channels or blue_channel in channels or white_channel in channels):
                    red = universe[red_channel]
                    green = universe[green_channel]
                    blue = universe[blue_channel]
                    white = universe[white_channel]
                    return ColorConverter.rgbw_to_rgb(red, green, blue, white)
                else:
                    return None
            elif color_mode == "cmy":
                cyan_channel = base_address + fixture_type["cyan"]
                magenta_channel = base_address + fixture_type["magenta"]
                yellow_channel = base_address + fixture_type["yellow"]
                if (cyan_channel in channels or magenta_channel in channels or yellow_channel in channels):
                    cyan = universe[cyan_channel]
                    magenta = universe[magenta_channel]
                    yellow = universe[yellow_channel]
                    return ColorConverter.cmy_to_rgb(cyan, magenta, yellow)
                else:
                    return None
            elif color_mode == "wheel":
                position_channel = base_address + fixture_type["color"]
                if (position_channel in channels):
                    position = rawUniverse[position_channel]
                    wheel = fixture_type["colorWheel"]
                    return ColorConverter.wheel_to_rgb(wheel, position, True)
                else:
                    return None
            else:
                return [1, 1, 1] # white
        except IndexError:
            return None
