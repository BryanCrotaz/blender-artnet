"""Write universe data to blender"""

import bpy

from .color_converter import ColorConverter

class BlenderSynchroniser:
    """Writes universe data to Blender"""

    artnet_enabled = True
    frame_current = 0

    def __init__(self, universe_store, fixture_store, fixture_type_store):
        self.universe_store = universe_store
        self.fixture_store = fixture_store
        self.fixture_type_store = fixture_type_store
        self.add_keyframes = False

        bpy.app.timers.register(self.timer_tick, first_interval=0.1, persistent=True)
        bpy.app.handlers.frame_change_pre.append(self.frame_change_pre)

    def __del__(self):
        bpy.app.timers.unregister(self.timer_tick)
        bpy.app.handlers.frame_change_pre.remove(self.frame_change_pre)

    def _update_blender(self):
        """main loop"""
        # runs in the main thread on a timer
        # find out which universes updated
        # returns map of universe index to list of changed channels
        universe_changes_pending: {} = self.universe_store.get_pending_universes()

        # only deal with universes that we have fixtures for
        universes_pending = list(
            filter(lambda x: x in self.fixture_store.fixture_universe_ids,
                   universe_changes_pending.keys())
        )

        if self.artnet_enabled:
            bpy.types.RenderSettings.use_lock_interface = True
            for universe_index in universes_pending:
                self._update_blender_from_universe(universe_index,
                                                   universe_changes_pending[universe_index])
            bpy.types.RenderSettings.use_lock_interface = False

    def frame_change_pre(self, scene, context):
        self.add_keyframes = scene.tool_settings.use_keyframe_insert_auto
        if self.add_keyframes:
            self.frame_current = scene.frame_current
            self._update_blender()

    def timer_tick(self):
        self.add_keyframes = bpy.context.scene.tool_settings.use_keyframe_insert_auto
        if not self.add_keyframes:
            self._update_blender()
            return 0.03 # call again in 0.03 seconds - 30fps
        return 0.01 # call again in 0.01 seconds - 10fps

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
        fixture_type = self.fixture_type_store.get_fixture_type(mapping.get("fixture_type", None))
        if fixture_type is None:
            return
        base_address = mapping.get("base_address", None)
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
        fixture_type = self.fixture_type_store.get_fixture_type(mapping.get("fixture_type", None))
        if fixture_type is None:
            return None

        base_address = mapping.get("base_address", None)
        if base_address is None:
            return None

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
        fixture_type = self.fixture_type_store.get_fixture_type(mapping.get("fixture_type", None))
        if fixture_type is None:
            return None
        base_address = mapping.get("base_address", None)
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
        zoom_channel = fixture_type.get("zoom", None)
        if zoom_channel is None:
            return None
        zoom_channel += base_address
        if zoom_channel in channels:
            min_zoom = fixture_type.get("minZoom", 0)
            max_zoom = fixture_type.get("maxZoom", 90)
            zoom = universe[zoom_channel]
            zoom_invert = fixture_type.get("zoom_invert", False)
            if zoom_invert:
                zoom = 1 - zoom
            angle = min_zoom + zoom *(max_zoom-min_zoom)
            return angle
        return None

    def _get_power(self, universe, base_address, fixture_type, channels):
        dimmer_channel = fixture_type.get("dimmer", None)
        if dimmer_channel is None:
            return None
        dimmer_channel += base_address
        if dimmer_channel in channels:
            dimmer = universe[dimmer_channel]
            lumens = fixture_type["lumens"]
            power = lumens * dimmer / 6.83
            return power
        return None

    def _get_rotation(self, universe, base_address, fixture_type, channels):
        pan = None
        tilt = None
        universe_len = len(universe)
        pan_channel = fixture_type.get("pan", None)
        if pan_channel is not None:
            pan_channel += base_address
            if pan_channel in channels:
                pan = universe[pan_channel] if (pan_channel < universe_len) else 0
                pan_range = fixture_type.get("panRange", 360)
                pan -= 0.5
                pan *= pan_range

        tilt_channel = fixture_type.get("tilt", None)
        if tilt_channel is not None:
            tilt_channel += base_address
            if tilt_channel in channels:
                tilt = universe[tilt_channel] if (tilt_channel < universe_len) else 0
                tilt_range = fixture_type.get("tiltRange", 360)
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

        rotation = self._get_rotation(universe, base_address, fixture_type, channels)
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
        color_mode = fixture_type.get("colorMode", None)
        if color_mode == "rgbw":
            red_channel = fixture_type.get("red", None)
            green_channel = fixture_type.get("green", None)
            blue_channel = fixture_type.get("blue", None)
            white_channel = fixture_type.get("white", None)
            if (red_channel is None
                    or green_channel is None
                    or blue_channel is None
                    or white_channel is None):
                return None
            red_channel += base_address
            green_channel += base_address
            blue_channel += base_address
            white_channel += base_address
            if (red_channel in channels
                    or green_channel in channels
                    or blue_channel in channels
                    or white_channel in channels):
                universe_len = len(universe)
                red = universe[red_channel] if (red_channel < universe_len) else 0
                green = universe[green_channel] if (green_channel < universe_len) else 0
                blue = universe[blue_channel] if (blue_channel < universe_len) else 0
                white = universe[white_channel] if (white_channel < universe_len) else 0
                return ColorConverter.rgbw_to_rgb(red, green, blue, white)
            return None

        elif color_mode == "cmy":
            cyan_channel = fixture_type.get("cyan", None)
            magenta_channel = fixture_type.get("magenta", None)
            yellow_channel = fixture_type.get("yellow", None)
            if (cyan_channel is None
                    or magenta_channel is None
                    or yellow_channel is None):
                return None
            cyan_channel += base_address
            magenta_channel += base_address
            yellow_channel += base_address
            if (cyan_channel in channels
                    or magenta_channel in channels
                    or yellow_channel in channels):
                universe_len = len(universe)
                cyan = universe[cyan_channel] if (cyan_channel < universe_len) else 0
                magenta = universe[magenta_channel] if (magenta_channel < universe_len) else 0
                yellow = universe[yellow_channel] if (yellow_channel < universe_len) else 0
                return ColorConverter.cmy_to_rgb(cyan, magenta, yellow)
            return None

        elif color_mode == "wheel":
            position_channel = fixture_type.get("color", None)
            if position_channel is None:
                return None
            position_channel += base_address
            if position_channel in channels:
                universe_len = len(universe)
                position = rawUniverse[position_channel] if (position_channel < universe_len) else 0
                wheel = fixture_type["colorWheel"]
                return ColorConverter.wheel_to_rgb(wheel, position, True)
            return None

        else:
            return None
