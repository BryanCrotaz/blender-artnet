# blender-artnet
Blender script to push ArtNet data to Evee lights. Runs at 30fps with Evee rendering in the viewport.

Combine with QLCPlus to have a fully open source lighting system

Select a light in your scene and enable ArtNet Light Control in the properties. Assign a universe, base 
address and fixture type

Add your own fixture types in `src/fixture_type_store.py`

# Contributions wanted
Let's work out how to get fixture definitions in from an open source store
