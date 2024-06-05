import bpy
import numpy as np

def insert_motion_keyframe(moving_object):
    moving_object.keyframe_insert(data_path = 'location')
    if moving_object.rotation_mode == "QUATERNION":
        moving_object.keyframe_insert(data_path = 'rotation_quaternion')
    else:
        moving_object.keyframe_insert(data_path = 'rotation_euler')
    moving_object.keyframe_insert(data_path = 'scale')

# Make sure we are on the first animation frame!
bpy.context.scene.frame_set(1)

sqObj = bpy.data.objects.get("squirrel_demo_low")
sqObj.animation_data_clear()


normMat = np.array([1, 0, 0, 9.1343307,
 0, 1, 0, 4.710125,
 0, 0, 1, 1105.3611,
 0, 0, 0, 1]).reshape((4,4)).transpose()

# Test if normalization was already applied.
# The unnormalized squirrel's z values are all extreme negative.
normApplied = np.array(sqObj.bound_box)[:,2].max() > 0

# If not, apply normalization.
if not normApplied:
    sqObj.data.transform(normMat)


firstPoseMat = np.array([-0.85165083, 0.39713106, -0.34202012, 15,
 0.011513352, -0.63824022, -0.76975113, -35,
 -0.52398312, -0.65949702, 0.53898555, 515,
 0, 0, 0, 1]).reshape((4,4)).transpose()

sqObj.matrix_world = firstPoseMat


insert_motion_keyframe(sqObj)
bpy.context.scene.frame_set(105)
insert_motion_keyframe(sqObj)


bpy.context.scene.frame_set(140)

single_it_mat = np.array([-0.84301674, 0.39918843, -0.36051536, 13.185945,
 0.045341276, -0.61511958, -0.78712898, -33.736732,
 -0.53597289, -0.67990917, 0.50045645, 498.3959,
 0, 0, 0, 1]).reshape((4,4)).transpose()

sqObj.matrix_world = single_it_mat


insert_motion_keyframe(sqObj)
bpy.context.scene.frame_set(175)
insert_motion_keyframe(sqObj)

bpy.context.scene.frame_set(210)

final_mat = np.array([-0.80551249, 0.39087358, -0.44538352, 5.929296,
 0.2176373, -0.50393355, -0.83587378, -30.149389,
 -0.55116373, -0.77023911, 0.32085621, 465.93689,
 0, 0, 0, 1]).reshape((4,4)).transpose()

sqObj.matrix_world = final_mat


insert_motion_keyframe(sqObj)

# Make sure we are on the first animation frame!
bpy.context.scene.frame_set(1)