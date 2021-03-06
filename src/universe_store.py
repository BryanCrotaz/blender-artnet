"""Universe Store"""

import threading

ALL_UNIVERSES = -1

class UniverseStore:
    """Stores universe data with thread locking"""

    UpdatesPending = {} # map of universe indices : list of updated channels
    UpdatesLock = threading.Lock()

    _universes = []  # float data 0-1
    _raw_universes = []  # byte data 0-255

    def get_universe(self, index):
        """Returns a universe with float 0-1 values"""
        self._ensure_universe_exists(index)
        return self._universes[index]

    def get_raw_universe(self, index):
        """Returns a universe with raw byte values"""
        self._ensure_universe_exists(index)
        return self._raw_universes[index]

    def notify_universe_change(self, index, changes):
        """Threadsafe notify that a universe is dirty"""
        with self.UpdatesLock:
            if index == ALL_UNIVERSES:
                for i in range(len(self._universes)):
                    self.UpdatesPending[i] = range(0, 511)
            else:
                self.UpdatesPending[index] = changes

    def get_pending_universes(self):
        """Returns a list of universes that need to be synced to Blender"""
        universes_pending = {}
        with self.UpdatesLock:
            for universe_index in self.UpdatesPending:
                if self.UpdatesPending[universe_index] is not None:
                    universes_pending[universe_index] = self.UpdatesPending[universe_index]
                    self.UpdatesPending[universe_index] = None
        return universes_pending

    def _ensure_universe_exists(self, index):
        while len(self._universes) <= index:
            universe = []
            for _ in range(512):
                universe.append(0)
            self._universes.append(universe)
            raw_universe = []
            for _ in range(512):
                raw_universe.append(0)
            self._raw_universes.append(raw_universe)
