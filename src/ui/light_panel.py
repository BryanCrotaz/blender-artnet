import bpy

class LightArtNetPanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_light_artnet"
    bl_label = "ArtNet Light Control"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    #bl_options = {}

    @classmethod
    def poll(cls, context):
        """Only show panel for light objects"""
        if context.object.type != 'LIGHT':
            return False
        light_type = context.object.data.type
        return light_type == "SPOT" or light_type == "AREA"

    def draw_header(self, context):
        layout = self.layout
        data = context.object.data
        layout.prop(data, "artnet_enabled", text="")

    def draw(self, context):
        data = context.object.data
        enabled = data.artnet_enabled
        if not enabled:
            return

        layout = self.layout
        layout.prop(data, "artnet_fixture_type")
        layout.prop(data, "artnet_universe")
        layout.prop(data, "artnet_base_address")
        layout.prop(data, "artnet_pan_target")
        layout.prop(data, "artnet_tilt_target")
