"""Color Converter"""
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