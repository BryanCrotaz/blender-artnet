"""Fixture Type Store"""

import math

class FixtureTypeStore:
    """Stores the fixture types from which to map the dmx data"""

    def __init__(self):
        for fixture_type in self._fixture_types:
            f_t = self._fixture_types[fixture_type]
            # convert degrees to radians so we don't do this every frame
            f_t["panRange"] = math.radians(f_t["panRange"])
            f_t["tiltRange"] = math.radians(f_t["tiltRange"])
            f_t["minZoom"] = math.radians(f_t["minZoom"])
            f_t["maxZoom"] = math.radians(f_t["maxZoom"])

    # TODO: load these from a public store or provide a UI to edit them
    _fixture_types = {
        "wash": {
            "power": 1000,
            "color": "rgbw",
            "red": 4,
            "green": 6,
            "blue": 8,
            "white": 10,
            "pan": 0,
            "tilt": 2,
            "zoom": 15,
            "panRange": 623,
            "tiltRange": 295,
            "minZoom": 7,
            "maxZoom": 50
        },
        "spot": {
            "power": 1000,
            "color": "cmy",
            "cyan": 8,
            "magenta": 9,
            "yellow": 10,
            "pan": 0,
            "tilt": 2,
            "zoom": 21,
            "panRange": 540,
            "tiltRange": 270,
            "minZoom": 10,
            "maxZoom": 45
        },
        "pointe": {
            "power": 1000,
            "color": "wheel",
            "colorWheel": {
                0: [1, 1, 1],
                9: [1, 0, 0],
                18: [0, 0, 1],
                27: [0, 1, 1],
                37: [0.2, 1, 0.2],
                46: [1, 0, 1]
            },
            "pan": 0,
            "tilt": 2,
            "zoom": 16,
            "panRange": 540,
            "tiltRange": 270,
            "minZoom": 5,
            "maxZoom": 20
        }
    }

    def get_fixture_type(self, name):
        """Return a named fixture type"""
        if name in self._fixture_types:
            return self._fixture_types[name]
        return None
