"""Fixture Type Store"""

import math

class FixtureTypeStore:
    """Stores the fixture types from which to map the dmx data"""

    def __init__(self):
        for fixture_type in self._fixture_types:
            f_t = self._fixture_types[fixture_type]
            # convert degrees to radians so we don't do this every frame
           if "panRange" in f_t:
                f_t["panRange"] = math.radians(f_t["panRange"])
            if "tiltRange" in f_t:
                f_t["tiltRange"] = math.radians(f_t["tiltRange"])
            if "minZoom" in f_t:
                f_t["minZoom"] = math.radians(f_t["minZoom"])
            if "maxZoom" in f_t:
                f_t["maxZoom"] = math.radians(f_t["maxZoom"])

    # TODO: load these from a public store or provide a UI to edit them
    _fixture_types = {
        "wash": {
            "colorMode": "rgbw",
            "red": 4,
            "green": 6,
            "blue": 8,
            "white": 10,
            "pan": 0,
            "tilt": 2,
            "zoom": 15,
            "dimmer": 13,
            "panRange": 623,
            "tiltRange": 295,
            "minZoom": 7,
            "maxZoom": 50,
            "lumens": 5085
        },
        "spot": {
            "colorMode": "cmy",
            "cyan": 8,
            "magenta": 9,
            "yellow": 10,
            "pan": 0,
            "tilt": 2,
            "zoom": 24,
            "dimmer": 30,
            "panRange": 540,
            "tiltRange": 270,
            "minZoom": 10,
            "maxZoom": 45,
            "lumens": 41000
        },
        "pointe": {
            "colorMode": "wheel",
            "colorWheel": {
                0: [1, 1, 1],
                9: [1, 0, 0],
                18: [0, 0, 1],
                27: [0, 1, 1],
                37: [0.2, 1, 0.2],
                46: [1, 0, 1]
            },
            "color": 6,
            "pan": 0,
            "tilt": 2,
            "zoom": 15,
            "dimmer": 21,
            "panRange": 540,
            "tiltRange": 270,
            "minZoom": 5,
            "maxZoom": 20,
            "lumens": 5150
        }
    }

    def get_fixture_type(self, name):
        """Return a named fixture type"""
        if name in self._fixture_types:
            return self._fixture_types[name]
        return None
