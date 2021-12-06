import bpy
from bpy.props import (
    BoolProperty,
    StringProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    axis_conversion,
)

bl_info = {
    "name": "R3D Mesh",
    "author": "Psycrow",
    "version": (0, 0, 1),
    "blender": (2, 81, 0),
    "location": "File > Import-Export",
    "description": "Import / Export Rock3dEngine mesh file (.r3d)",
    "warning": "",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Import-Export"
}

if "bpy" in locals():
    import importlib
    if "import_r3d" in locals():
        importlib.reload(import_r3d)
    if "export_r3d" in locals():
        importlib.reload(export_r3d)


@orientation_helper(axis_forward='Y', axis_up='Z')
class ImportR3D(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.r3d"
    bl_label = "Import R3D Mesh"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".r3d"
    filter_glob: StringProperty(default="*.r3d", options={'HIDDEN'})

    def execute(self, context):
        from . import import_r3d

        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            ))
        keywords["global_matrix"] = axis_conversion(from_forward=self.axis_forward,
                                                    from_up=self.axis_up,
                                                    ).to_4x4()

        return import_r3d.load(context, **keywords)


class ExportR3D(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.r3d"
    bl_label = "Export R3D Mesh"
    bl_options = {'PRESET'}

    filename_ext = ".r3d"
    filter_glob: StringProperty(default="*.r3d", options={'HIDDEN'})

    use_split_normals: BoolProperty(
        name="Use Split Normals",
        description="Use the average of Split Normals instead of Vertex Normals",
        default=True,
    )

    def execute(self, context):
        from . import export_r3d

        keywords = self.as_keywords(ignore=("filter_glob",
                                            ))

        return export_r3d.save(context, keywords['filepath'], keywords['use_split_normals'])


def menu_func_import(self, context):
    self.layout.operator(ImportR3D.bl_idname,
                         text="R3D Mesh (.r3d)")


def menu_func_export(self, context):
    self.layout.operator(ExportR3D.bl_idname,
                         text="R3D Mesh (.r3d)")


classes = (
    ImportR3D,
    ExportR3D,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
