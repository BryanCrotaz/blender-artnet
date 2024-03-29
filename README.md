# blender-artnet
Blender script to push ArtNet data to Evee lights. Runs at 30fps with Evee rendering in the viewport.

Combine with QLCPlus to have a fully open source lighting system

# Install

In the `Code...` menu download this repo as a zip file and remember the folder where you put it

1. Install Blender 2.8 or higher.
2. `Edit | Preferences` menu opens the preferences dialog
3. Select the `Add-ons` tab
4. Press the `Install...` button
5. Select the zip file you downloaded
6. Press the `Install Addon` button
7. Close the preferences dialog
8. ...
9. Profit!

# Usage

Turn on Viewport Shading and Evee rendering

Select a light in your scene and enable ArtNet Light Control in the properties. Assign a universe, base 
address and fixture type

Add your own named fixture types in `src/fixture_type_store.py`

In the Window menu, the *Listen to ArtNet* checkbox enables or disables Artnet input to Blender. It's on by default.

## Keyframes

From version 1.6.2 this addon integrates with Blender *Auto Keyframing*. When this is enabled, the addon will append
keyframes to the timeline for all properties modified via Artnet.

![Editing in Blender](./images/Blender-artnet.png)

# DMX Support

Handles the following DMX channels (coarse only for now)
* RGBW (additive)
  * red
  * green
  * blue
  * white
* CMY (subtractive)
  * cyan
  * magenta
  * yellow
* Colour wheels
  * currently continuously varying wheels are not supported
* dimmer
* zoom (invertable for some fixtures)
* Movement
  * pan
  * tilt

# Pan, Tilt and fixture modelling

If fixtures are visible in the scene, you may wish to model the body of the
fixture. Typically it would have a panning section, containing a tilting
section with the lamp in it. If you parent the objects in this chain, you can
select the parent or grandparent to be animated with pan and tilt.

To use this method, select the light in Blender and select the Pan Target
and Tilt Target. Select which axis of the light, its parent, or its
grandparent to affect. You can also choose _Ignore_, for example if the
fixture has panning but no tilt motor.

Pan and tilt affect the rotation transform, so you can use the delta rotation
transform to set the centre position of your fixture models. 

# Future ideas

Focus can be handled by changing the spot size in Blender

Frost can be handled by changing the spot blend radius in Blender

Gobos can be handled by [https://www.youtube.com/watch?v=Af-yLsRpF7I]

# Versions
#### Version 1.6.3:

* Follow Blender's internal frame rate when recording auto keyframes, matching your animation framerate
* When not recording keyframes, run at 30fps for smooth previs

#### Version 1.6.2:

* Integrate with Auto Keyframing setting in Blender

#### Version 1.6.1:

* Only create key frames for channels that changed

#### Version 1.6:

* Save ArtNet animation to keyframes for playback later, e.g. rendering in Cycles
* Supports Point light type in Blender

#### Version 1.5:

* Target parent or grandparent object with pan and tilt settings - great for moving head modelling

#### Version 1.3:

* Supports Area light type in Blender
* Hides artnet panel for unsupported lights

#### Version 1.2:

* Supports Spot light type in Blender

# Contributions wanted
* Let's work out how to get fixture definitions in from an open source store

Please submit a PR if you have an improvement.

# Funding
I'm not a professional lighting designer - this came out of a hobby project to control 
lighting for an event I worked on for a friend. So I have no personal value gained by
working on improving it (unlike other open source software I work on), although it is
rather fun. If lighting professionals see a value in this plugin I would be happy to be
funded to work on it.

Alternatively, I would be very happy to accept high quality PRs to improve the plugin.

Many thanks to the below companies and individuals who have funded me to work on this addon.

* Skeldon Società Cooperativa, Italy
