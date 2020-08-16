from .artnet_socket import ArtNetSocket
from .fixture_store import FixtureStore
from .blender_sync import BlenderSynchroniser

GLOBAL_DATA = {
    ArtNetSocket: ArtNetSocket,
    BlenderSynchroniser: BlenderSynchroniser,
    FixtureStore: FixtureStore,
}
