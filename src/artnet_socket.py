"""ArtNet Socket implementation"""

import socket
import threading
import time

UDP_IP = "0.0.0.0"
UDP_PORT = 6454

class ArtNetSocket:
    """Connects to ArtNet"""

    _shutdown = False
    _thread: threading.Thread

    def __init__(self, universe_store):
        self._socket = self.connect()
        self.universe_store = universe_store
        if self._socket is not None:
            self._thread = threading.Thread(target=self.socket_loop)
            self._thread.daemon = True
            self._thread.start()

    def connect(self):
        """Connect to Artnet UDP socket"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((UDP_IP, UDP_PORT))
            # blocking socket as we're listening in a background thread
            self._socket.setblocking(1)
            self._socket.settimeout(1) # 1 second timeout
            return self._socket
        except Exception as err:
            print("error while connecting", err)
            self.disconnect()
            return None

    def disconnect(self):
        """Disconnect from Artnet UDP socket"""
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    def shutdown(self):
        """Kill the internal thread and wait for it to exit"""
        self._shutdown = True
        self._thread.join()

    @staticmethod
    def is_art_net(packet):
        """Return true if packet is valid ArtNet packet"""
        return (packet[0] == 65
                and packet[1] == 114
                and packet[2] == 116
                and packet[8] == 0
                and packet[9] == 80) # known header

    def socket_loop(self):
        """Thread loop"""
        # runs in a background thread
        # must not access blender directly

        # avoid setting up exception blocks inside the main loop
        while True:
            try:
                while True:
                    # read the packet in a tight loop
                    if self._shutdown:
                        self.disconnect()
                        return
                    if self._socket is None:
                        time.sleep(0.5)
                    else:
                        self.read_packet()
            except socket.timeout:
                # do nothing
                pass
            except socket.error:
                # reconnect socket
                self.disconnect()
                self._socket = self.connect()
            except Exception:
                pass

    def read_packet(self):
        packet, _addr = self._socket.recvfrom(1024)
        if len(packet) > 18 and ArtNetSocket.is_art_net(packet):
            self.parse_packet(packet)

    def parse_packet(self, packet):
        """Parse a valid artnet universe packet"""
        channels = packet[16]*256 + packet[17]
        # packets don't have to have all 512 channels
        if channels <= 512:
            universe_index = packet[15]*256 + packet[14] + 1  # 1-based everywhere except in packet
            # universe has float data 0-1
            universe = self.universe_store.get_universe(universe_index)
            # raw_universe has byte data to detect changes
            raw_universe = self.universe_store.get_raw_universe(universe_index)
            universe_changes = []
            # loop through the channels
            for i in range(channels):
                raw_value = packet[i+18]
                if raw_universe[i] != raw_value:
                    # data changed since last time
                    raw_universe[i] = raw_value
                    universe[i] = raw_value / 255.0
                    universe_changes.append(i)
            # let the main thread know that there's an update
            if len(universe_changes) > 0:
                self.universe_store.notify_universe_change(universe_index, universe_changes)
