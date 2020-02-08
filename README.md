# blender-artnet
Blender script to push artnet data to Evee lights. Runs at 30fps with Evee rendering in the viewport.

Combine with QLCPlus to have a fully open source lighting system

Replace `FixtureTypes` in `src/fixture_type_store.py` and `FixtureUniverses` in `src/fixture_store.py` 
with your data to use it in your own animations

# Contributions wanted
I'd like to add a UI panel in each light which allows you to set a fixture type, universe and base address
which get stored in the blend file.
