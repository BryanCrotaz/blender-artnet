"""Color Converter"""

import math

class ColorConverter:
    """Converts color formats to rgb"""

    @staticmethod
    def rgbw_to_rgb(red, green, blue, white):
        """Convert RGBW to RGB"""
        return [
            (red + white/3) * 3 / 4,
            (green + white/3) * 3 / 4,
            (blue + white/3) * 3 / 4
        ]

    @staticmethod
    def cmy_to_rgb(cyan, magenta, yellow):
        """Convert CMY to RGB"""
        return [
            1-cyan,
            1-magenta,
            1-yellow
        ]

    @staticmethod
    def wheel_to_rgb(wheel_settings, position, continuous):
        """Convert Color Wheel to RGB"""
        # todo: handle continuous wheels
        positions = wheel_settings.keys()
        last = max(positions)
        previous = last
        for pos in positions:
            if position <= pos:
                ## we're between this one and the previous one
                return wheel_settings[pos]
            previous = position
        return wheel_settings[last]
