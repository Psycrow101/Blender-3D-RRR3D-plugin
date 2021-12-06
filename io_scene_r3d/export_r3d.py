import bpy
import bmesh
from mathutils import Vector
import os
import struct


R3D_MESH_VERSION = 0


def invalid_active_object(self, context):
    self.layout.label(text='You need to select the mesh to export')


def multiple_uv_loops(self, context):
    self.layout.label(text='Some vertices use multiple UV loops. Part of the UV map can be distorted')


def write_byte(fd, val):
    fd.write(struct.pack('<B', val))


def write_int(fd, val):
    fd.write(struct.pack('<i', val))


def write_vector2(fd, val):
    fd.write(struct.pack('<2f', *val))


def write_vector3(fd, val):
    fd.write(struct.pack('<3f', *val))


def write_ivector3(fd, val):
    fd.write(struct.pack('<3i', *val))


def export_r3d(filepath, context, use_split_normals):
    mesh_obj = context.view_layer.objects.active
    if not mesh_obj:
        context.window_manager.popup_menu(invalid_active_object, title='Error', icon='ERROR')
        return {'CANCELLED'}

    mesh = mesh_obj.data
    if type(mesh) != bpy.types.Mesh:
        context.window_manager.popup_menu(invalid_active_object, title='Error', icon='ERROR')
        return {'CANCELLED'}

    uv_not_splited = False
    uv_layer = mesh.uv_layers.active.data
    if uv_layer:
        uvs = [None for _ in range(len(mesh.vertices))]
        for face in mesh.polygons:
            for li in face.loop_indices:
                vi, uv = mesh.loops[li].vertex_index, uv_layer[li].uv
                if uvs[vi] is None:
                    uvs[vi] = uv
                elif uvs[vi] != uv:
                    uv_not_splited = True

    if uv_not_splited:
        context.window_manager.popup_menu(multiple_uv_loops, title='Warning', icon='ERROR')

    bm = bmesh.new()
    bm.from_mesh(mesh)
    faces = bmesh.ops.triangulate(bm, faces=bm.faces)['faces']
    num_faces = len(faces)

    get_verts = lambda face: [v.index for v in face.verts]
    get_faces = lambda mat_id: [get_verts(face) for face in faces if face.material_index == mat_id]
    mat_faces = [get_faces(mat_id) for mat_id in range(max(1, len(mesh.materials)))]

    bm.free()
    del bm

    if use_split_normals:
        mesh.calc_normals_split()
        normals = [Vector((0.0, 0.0, 0.0)) for _ in range(len(mesh.vertices))]
        for loop in mesh.loops:
            normals[loop.vertex_index] = (normals[loop.vertex_index] + loop.normal).normalized()
    else:
        normals = [v.normal for v in mesh.vertices]

    with open(filepath, 'wb') as fd:
        write_int(fd, R3D_MESH_VERSION)
        write_byte(fd, 0) # TODO: left_coord_sys
        write_byte(fd, 1 if uv_layer else 0)

        write_int(fd, len(mesh.vertices))
        for i, v in enumerate(mesh.vertices):
            write_vector3(fd, v.co)
            write_vector3(fd, normals[i])
            if uv_layer:
                u, v = uvs[i]
                write_vector2(fd, (u, 1.0 - v))

        write_int(fd, num_faces)
        for mat_face in mat_faces:
            for face in mat_face:
                write_ivector3(fd, face)

        start_face = 0
        write_int(fd, len(mat_faces))
        for mat_id, mat_face in enumerate(mat_faces):
            face_count = len(mat_face)
            write_int(fd, mat_id + 1)
            write_int(fd, start_face)
            write_int(fd, face_count)
            start_face += face_count

    return {'FINISHED'}


def save(context, filepath, use_split_normals):
    return export_r3d(filepath, context, use_split_normals)
