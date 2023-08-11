import bmesh
import bpy
import math
from mathutils import Vector, Matrix


# Parameters
STAIR_WIDTH = 1.2
POLE_RADIUS = 0.075
POLE_GAP = 0.01
TREAD_DEPTH = 0.25
TREAD_THICKNESS = 0.05

TREAD_HEIGHT = 0.15
FLOOR_HEIGHT = 3
RAILING_HEIGHT = 0.875
RAILING_RADIUS = 0.0375

step_count = round(FLOOR_HEIGHT / TREAD_HEIGHT)
tread_height = FLOOR_HEIGHT / step_count


# Calculating Angle of Rotation
useful_circum = 2 * math.pi * (POLE_RADIUS + POLE_GAP + STAIR_WIDTH / 3 * 2)
segments = round(useful_circum / TREAD_DEPTH)
angle_rot = (2 * math.pi) / segments

bm = bmesh.new()

# Creating a vertex at point A
vec_a = Vector((POLE_RADIUS + POLE_GAP, 0, 0))
matrix_rot = Matrix.Rotation(angle_rot/2, 4, (0, 0, 1))
vec_a.rotate(matrix_rot)

vert_a = bm.verts.new(vec_a)

# Creating a vertex at point B
return_geo = bmesh.ops.extrude_vert_indiv(bm, verts=[vert_a])
vert_b = return_geo['verts'][0]

scale_factor = (vec_a.magnitude + STAIR_WIDTH) / vec_a.magnitude
vec_b = vert_a.co * scale_factor

vert_b.co = vec_b

# Creating a vertex at point C
return_geo = bmesh.ops.spin(
    bm,
    geom=[vert_b],
    angle=-angle_rot,
    steps=8,
    cent=(0, 0, 0),
    axis=(0, 0, 1)
)

vert_c = return_geo['geom_last'][0]
del return_geo

# Creating a vertex at point D
vec_d = vert_a.co.copy()
vec_d.y *= -1

return_geo = bmesh.ops.extrude_vert_indiv(bm, verts=[vert_c])
vert_d = return_geo['verts'][0]
del return_geo

vert_d.co = vec_d

# Creating a face and addint thickness
stair_profile = bm.faces.new(bm.verts)
return_geo = bmesh.ops.extrude_face_region(bm, geom=[stair_profile])
verts = [elem for elem in return_geo['geom'] if type(elem) == bmesh.types.BMVert]
bmesh.ops.translate(bm, verts=verts, vec=(0, 0, -TREAD_THICKNESS))

stair_geo = bm.verts[:] + bm.edges[:] + bm.faces[:]

for i in range(1, step_count + 1):
    return_geo = bmesh.ops.duplicate(bm, geom=stair_geo)
    
    verts = [elem for elem in return_geo['geom'] \
                            if type(elem) == bmesh.types.BMVert]
    bmesh.ops.translate(bm, verts=verts, vec=(0, 0, i * tread_height))
    
    matrix_rot = Matrix.Rotation(i * angle_rot, 3, (0, 0, 1))
    bmesh.ops.transform(bm, matrix=matrix_rot, verts=verts)

bmesh.ops.delete(bm, geom=stair_geo)

del return_geo

return_geo = bmesh.ops.create_circle(
    bm,
    cap_ends=True,
    segments=32,
    radius=POLE_RADIUS
)

circle_face = return_geo['verts'][0].link_faces[0]

return_geo = bmesh.ops.extrude_face_region(bm, \
                geom=return_geo['verts'] + [circle_face])
            
verts = [elem for elem in return_geo['geom'] \
            if type(elem) == bmesh.types.BMVert]
            
bmesh.ops.translate(bm, verts=verts, vec=(0, 0, FLOOR_HEIGHT))

del return_geo

return_geo = bmesh.ops.create_circle(
    bm,
    cap_ends=True,
    segments=16,
    radius=0.025
)

matrix_rot = Matrix.Rotation(math.radians(-90), 3, (1, 0, 0))
bmesh.ops.transform(bm, matrix=matrix_rot, verts=return_geo['verts'])

stair_diameter = POLE_RADIUS + POLE_GAP + STAIR_WIDTH
railing_distance = stair_diameter - RAILING_RADIUS - 0.05

bmesh.ops.translate(
    bm, verts=return_geo['verts'],
    vec=(railing_distance, 0, RAILING_HEIGHT + tread_height)
)

matrix_rot = Matrix.Rotation(angle_rot/2, 4, (0, 0, 1))
bmesh.ops.transform(bm, matrix=matrix_rot, verts=return_geo['verts'])

circle_face = circle_face = return_geo['verts'][0].link_faces[0]

bmesh.ops.spin(
    bm,
    geom=return_geo['verts'] + [circle_face],
    axis=(0, 0, 1),
    cent=(0, 0, 0),
    steps=step_count * 4,
    angle=angle_rot * step_count,
    dvec=(0, 0, tread_height/4)
)

# Balusters
angle_offset = angle_rot / 4
slope = tread_height / angle_rot

for i in range(1, step_count + 1):
    for j in range(1, 3):
        return_geo = bmesh.ops.create_circle(
            bm,
            cap_ends=True,
            segments=12, 
            radius=.0125
        )
        
        bmesh.ops.translate(
            bm,
            verts=return_geo['verts'],
            vec=(stair_diameter - RAILING_RADIUS - 0.05, 0, i * tread_height)
        )

        if j == 1:
            angle = i * angle_rot + angle_offset
            height_offset = (angle_rot / 2 + angle_offset) * slope
        else:
            angle = i * angle_rot + angle_offset * -1
            height_offset = (angle_rot / 2 - angle_offset) * slope
            
        matrix_rot = Matrix.Rotation(angle, 4, (0, 0, 1))      
        bmesh.ops.transform(bm, verts=return_geo['verts'], matrix=matrix_rot)
        circle_face = circle_face = return_geo['verts'][0].link_faces[0]

        return_geo = bmesh.ops.extrude_face_region(
            bm, 
            geom=return_geo['verts'] + [circle_face]
        )
        
        verts = [elem for elem in return_geo['geom'] \
                        if type(elem) == bmesh.types.BMVert]         
        bmesh.ops.translate(
            bm, 
            verts=verts,
            vec=(0, 0, RAILING_HEIGHT + height_offset)
        )


bm.to_mesh(bpy.data.objects['Staircase'].data)
bpy.data.objects['Staircase'].data.update()
bm.free()
