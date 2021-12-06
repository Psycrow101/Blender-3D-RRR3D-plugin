import bpy
import os
import struct


def unknown_mesh_version(self, context):
    self.layout.label(text='Unknown R3D Mesh version')


def read_byte(file, num=1):
    data = struct.unpack(f'<{num}B', file.read(num))
    if num == 1:
        data = data[0]
    return data


def read_int(file, num=1):
    data = struct.unpack(f'<{num}i', file.read(4 * num))
    if num == 1:
        data = data[0]
    return data


def read_float(file, num=1):
    data = struct.unpack(f'<{num}f', file.read(4 * num))
    if num == 1:
        data = data[0]
    return data


def import_r3d(filepath, context, global_matrix):
    view_layer = context.view_layer

    with open(filepath, 'rb') as fd:
        version = read_int(fd)
        if version != 0:
            context.window_manager.popup_menu(unknown_mesh_version, title='Error', icon='ERROR')
            return {'CANCELLED'}

        left_coord_sys = read_byte(fd) # TODO
        stored_tex_coord = read_byte(fd)

        num_verts = read_int(fd)
        vertices, normals, uvs = [], [], []

        for _ in range(num_verts):
            vertices.append(read_float(fd, 3))
            normals.append(read_float(fd, 3))

            if stored_tex_coord:
                uvs.append([read_float(fd), 1.0 - read_float(fd)])

        num_faces = read_int(fd)
        faces = [read_int(fd, 3) for _ in range(num_faces)]

        mesh = bpy.data.meshes.new('R3D Mesh')
        mesh.from_pydata(vertices, [], faces)
        mesh.use_auto_smooth = True
        mesh.normals_split_custom_set_from_vertices(normals)

        if uvs:
            uv_layer = mesh.uv_layers.new()
            for f, face in enumerate(mesh.polygons):
                for i, loop in enumerate(face.loop_indices):
                    uv_layer.data[loop].uv = uvs[faces[f][i]]

        mesh_obj = bpy.data.objects.new('R3D Object', mesh)
        mesh_obj.matrix_world = global_matrix

        collection = bpy.data.collections.new(os.path.basename(filepath))
        collection.objects.link(mesh_obj)
        context.scene.collection.children.link(collection)
        
        num_materials = read_int(fd)
        for _ in range(num_materials):
            mat_id, start_face, face_count = read_int(fd, 3)

            for p in mesh.polygons[start_face:start_face+face_count]:
                p.material_index = mat_id - 1

            mat = bpy.data.materials.new(name='R3d Material %d' % mat_id)
            mesh.materials.append(mat)

        mesh.validate()
        mesh.update()

        view_layer.update()

    return {'FINISHED'}


def load(context, filepath, *, global_matrix=None):
    if filepath.lower().endswith('.r3d'):
        return import_r3d(filepath, context, global_matrix)

    return {'CANCELLED'}
