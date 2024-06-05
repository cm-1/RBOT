import bpy
import numpy as np

#--------------------------------------------
#%%
# Unused functions

# def clamp(x, min_val, max_val):
    # return min(max_val, max(x, min_val))

# # Returns an RGBA pixel from an image.
# def pixelFromImg(image, x, y):
    # w, h = image.size[:2]
    # if x < 0 or x >= w or y < 0 or y >= h:
        # raise Exception("Coordinates out of bounds!")
    # index = y * w + x    # 1D index
    # # We assume RGBA.
    # return image.pixels[index * 4 : (index + 1) * 4]
#--------------------------------------------
#%%

# Make sure we are on the first animation frame!
bpy.context.scene.frame_set(1)

# Get the loaded image from Blender 
image = bpy.data.images["frameSmall.png"]
sdt = bpy.data.images["sdtSmall.png"]
xyImage = bpy.data.images["xyDeltaSmall.png"]

# TODO: Error out if not all image sizes match!
print("image size:", np.array(image.pixels).shape, image.channels, image.depth)
print("sdt size:", np.array(sdt.pixels).shape, sdt.channels, sdt.depth)

# SRGB conversion comes from:
# https://entropymine.com/imageworsener/srgbformula/
# https://stackoverflow.com/questions/39792163/vectorizing-srgb-to-linear-conversion-properly-in-numpy
def srgb2linear(img):
    return np.where(
        img >= 0.04045,
        ((img + 0.055) / 1.055)**2.4,
        img/12.92
    )

# Commenting out because unused for now.
# def linear2srgb(pixels_np):
    # pixels_lin2 = np.where(
        # pixels_np > 0.0031308,
        # ((pixels_np ** (1.0/2.4)) * 1.055) - 0.055,
        # pixels_np * 12.92
    # )
    # return pixels_lin2

# Blender stores image pixels as floats from 0 to 1, so we need to scale by 255
# back to int. Also, because we shifted SDT values up by 8 when saving
# (so that negatives would still be preserved rather than set to 0), we need to
# shift back down by 8 as a correction.
sdtData = 255 * np.array(sdt.pixels)[::4] - 8

# We'll save the indices of all pixels within 8 pixels distance of contour.
valid_pixels = abs(sdtData) < 8


# Pixels data is in row-major, whereas later it'll be more convenient to
# index by xy coordinate, so I transpose for now.
# Maybe not transposing and rewriting later code is more efficient, idk.
sdtData2D = sdtData.reshape((sdt.size[1], sdt.size[0])).transpose()

# xyData requires same scale/shift as SDT, plus explicit round/convert to int.
xyDataCorrected = np.round( (255 * np.array(xyImage.pixels)) - 8 ).astype(int)

# Similar conversion to 2D as SDT data, except for the fact that we want to
# keep more channels. We will keep three channels (junk, yDelta, xDelta)
# for debug convenience (mapping to x, y, z)
# TODO: Maybe reorder to (xDelta, yDelta, junk) here rather than at access,
# to protect against future errors.
xyDataRowsCols = xyDataCorrected.reshape(
    (xyImage.size[1], xyImage.size[0], xyImage.channels)
)[:,:,1:3]
xyData2D = xyDataRowsCols.transpose((1, 0, 2))

# Sanity check to make sure numpy reshapes/transposes worked okay.
print("xy2D shape:", xyData2D.shape)
print("sdt2D shape:", sdtData2D.shape)

# The array image.pixels contains all pixels in a flattened 1D array
# ordered in row-major form, with bottom-left pixel at index [0].
pixels_np = np.array(image.pixels)

# Looks wrong in Blender viewport otherwise.
pixels_lin = srgb2linear(pixels_np)

num_pixels = image.size[0] * image.size[1]

# np.indices() creates a grid of indices that you'd normally pass into
# another numpy array as actual, well, indices.
# E.g., `my_array[my_indices[0], my_indices[1]]`
# But to "join together" the "i[0]" and "i[1]", a transpose is needed.
pixel_indices_grid = np.indices(image.size[:2]).transpose((2,1,0))
# Then I flatten the 3-axis array into a 2-axis one (a list of index pairs)
pixel_coords_xy = pixel_indices_grid.reshape(num_pixels, 2)
# Then hstack is used to add a zero "channel" to the arrays.
# If this were a 2D image, one would use dstack instead.
zero_channel = np.zeros((num_pixels, 1))
pixel_coords2 = np.hstack((zero_channel, pixel_coords_xy))
print("indices:", pixel_coords2)

# Rather than transform each array for the raycast, which appens in object
# space, it's more convenient to create a copy of the mesh for which we'll
# apply the current transform (so that object space == world space).
# We'll then delete this copy object when we're done.
sqObjOrig = bpy.data.objects.get("squirrel_demo_low")
sqObj = sqObjOrig.copy()
sqObj.data = sqObj.data.copy() # Copy mesh before we alter all vertex locations in obj copy

# Apply transform to object so that vertex coords stay the same in world space, while now
# object space == world space.
# https://blender.stackexchange.com/questions/159538/how-to-apply-all-transformations-to-an-object-at-low-level
sqObj.data.transform(sqObj.matrix_basis)
sqObj.matrix_basis.identity()

# Needed for raycast and whatnot to work, I think.
bpy.context.collection.objects.link(sqObj)

# TODO: Fewer magic numbers here, particularly division by 4.
# If we work with smaller/larger images, would have to scale differently.
principal_point = np.array([324.328, 257.323])/4.0
fLen = 650.0/4.0

# Some helper functions for ray math.
def get_ray_xy(img_xy):
    # Because RBOT code has poses where y goes from top to bottom, we need
    # to flip the y coordinate for ray intersections.
    flipped_co = np.array((img_xy[0], image.size[1] - img_xy[1]))
    ray_dir_xy = flipped_co - principal_point
    return ray_dir_xy
    
# Constructs a new 3D ray whose z value is "depth" but that would pass through
# the specified xy pixel when raycasting from the origin.
def borrow_depth_for_xy(img_xy, depth):
    dir_xy = get_ray_xy(img_xy)

    x = dir_xy[0] * depth/fLen
    y = dir_xy[1] * depth/fLen
    return (x, y)
    
# Performs a raycast with the squirrel object, using a ray that goes through
# xy_coord pixel, and adds the result to the array "arr" if successful.
# A bool for whether the raycast was successful is returned.
# If xyOverwrite is specified, then we use the depth value from the raycast
# but pretend that the ray actually went through the pixel specified as 
# the "overwrite" when constructing our 3D hit point.
def add_ray_result_if_exists(xy_coord, arr, xyOverwrite = None):
    ray_dir_xy = get_ray_xy(xy_coord)
    ray_dir = np.array((ray_dir_xy[0], ray_dir_xy[1], fLen))
    hit, loc, norm, ind = sqObj.ray_cast((0,0,0), ray_dir)
    if (hit):
        if xyOverwrite is not None:
            xo, yo = borrow_depth_for_xy(xyOverwrite, loc[2]) 
            loc[0] = xo
            loc[1] = yo
        arr.append(loc)
    return hit


# List of pixel coords that we will use as vertices for the mesh that then
# gets converted to cubes/spheres/whatever through geometry nodes.
pixel_coords = []


# If all of our efforts of getting a raycast, even using the nearest contour
# pixel values, and _even_ going a bit "further" into the contour by scaling
# the delta, _all_ fail to get a raycast, we'll fill in the missing values
# at the end by looking at neighbours for whom a raycast succeeded.
# My current setup is not very memory or space efficient, but it works for now.
# In the future, should possibly just save the depth map from the C++ code and
# read from it, or just create all images from within Blender in a separate
# script.
ray_failures = np.full(valid_pixels.shape[0], False)
ray_fails_2D = np.full(sdtData2D.shape, False)
z_vals_2D = np.zeros(sdtData2D.shape)
for i, xy_co in enumerate(pixel_coords_xy[valid_pixels]):
    rayWorked = False

    if sdtData2D[xy_co[0], xy_co[1]] <= 0.0001:    
        rayWorked = add_ray_result_if_exists(xy_co, pixel_coords)
    if not rayWorked:
        xy_delta = xyData2D[xy_co[0], xy_co[1]]
        # OpenCV saves images "flipped" relative to Blender both in terms of
        # y-axis and in BGR/RGB channel order. So we must correct.
        xy_delta_blender = np.array((xy_delta[1], -xy_delta[0]))
        xy_near = xy_co + xy_delta_blender
        rayWorked = add_ray_result_if_exists(xy_near, pixel_coords, xy_co)
        if not rayWorked:
            delta_norm = np.linalg.norm(xy_delta_blender)
            resized_delta = (delta_norm + 1) * xy_delta_blender/delta_norm
            xy_near = xy_co + resized_delta
            rayWorked = add_ray_result_if_exists(xy_near, pixel_coords, xy_co)
            if not rayWorked:
                print("Failure for delta:", xy_delta_blender)
    if not rayWorked:
        pixel_coords.append((0, 0, 100))
        ray_failures[i] = True
        ray_fails_2D[xy_co[0], xy_co[1]] = True
    z_vals_2D[xy_co[0], xy_co[1]] = pixel_coords[-1][2]
    
# For pixels where raycasting didn't work, just borrow depth from neighbours.
for i, xy_co in enumerate(pixel_coords_xy[valid_pixels]):
    if ray_failures[i]:
        neighbour_found = False
        for xi in range(-1, 2):
            for yi in range(-1, 2):
                ind_x = xy_co[0] + xi
                ind_y = xy_co[1] + yi
                if not ray_fails_2D[ind_x, ind_y]:
                    zo = z_vals_2D[ind_x, ind_y]
                    xo, yo = borrow_depth_for_xy(
                        xy_co, zo
                    )
                    pixel_coords[i] = (xo, yo, zo)
                    neighbour_found = True
                    break
        if not neighbour_found:
            raise Exception("Found a pixel for which depth could not be set.")


# Remove the transformation-applied squirrel copy now that we're done with it.
bpy.data.objects.remove(sqObj)

# Use the results of raycasting to edit the vertices of the geom-node object.
dots_obj = bpy.data.objects.get("Cube")

# To replace all vertices in a mesh, it seems easiest to just
# create a new mesh and delete the old one.

dotsMesh = bpy.data.meshes.new('dotsMesh')
# Here, pixel_coords will be the verts; no edges and faces
dotsMesh.from_pydata(pixel_coords, [], [])
dotsMesh.update()

# Swap meshes and delete the old one.
mesh_to_del = dots_obj.data
dots_obj.data = dotsMesh
bpy.data.meshes.remove(mesh_to_del)

# Have the geom-node mesh share the transform of the squirrel.
dots_obj.data.transform(sqObjOrig.matrix_basis.inverted())
dots_obj.matrix_basis = sqObjOrig.matrix_basis

# If not already parented, parent dots to squirrel so that we can better
# visualize the effect of transformations.
dots_obj.parent = sqObjOrig
dots_obj.matrix_parent_inverse = sqObjOrig.matrix_world.inverted()

# Setting vertex colours is not _super_ straightforward and changes a lot
# between Blender versions. For 4.1, I followed along this link:
# https://blender.stackexchange.com/questions/280716/python-code-to-set-color-attributes-per-vertex-in-blender-3-5
colattr = dotsMesh.color_attributes.new(
    name="Color",
    type='FLOAT_COLOR',
    domain='POINT',
)

# We'll use the "ground truth" SDT to better display which pixels are
# part of the squirrel or not. We'll store this info in the alpha
# channel so that we can customize how we use it in our shader(s).
sdt_gt = bpy.data.images["sdtSmallGT.png"]
sdtDataGT = 255 * np.array(sdt_gt.pixels)[::4] - 8
sdtDataGT01 = (1/np.pi)*(np.arctan(1.2 * sdtDataGT) + np.pi/2)

# In foreach_set, pixel_colours must be flat/1D
col_vals = pixels_lin[np.repeat(valid_pixels, 4)]
col_vals[3::4] = sdtDataGT01[valid_pixels]
colattr.data.foreach_set("color", col_vals)

print("TODO:")
print("- May need to add (0.5,0.5) to xy coords when creating rays!")
raise Exception("Unifinished urgent TODO items; check printouts!")

# Some unused test/debug code to put somewhere:
#deltasFlatIsh = xyDataCorrected.reshape((xyImage.size[0]*xyImage.size[1], xyImage.channels))[:, [0,2,1]]
#deltasFlatIsh[:, 2] *= -1


#xyIndices = pixel_coords2[:]
#print("deltas shape:", deltasFlatIsh.shape)
#print("indices shape:", xyIndices.shape)

#pixel_coords = np.vstack((xyIndices, xyIndices + deltasFlatIsh)) + 0.5
#print("final shape:", pixel_coords.shape)

#numEdges = xyIndices.shape[0]
#edges = np.arange(numEdges).repeat(2).reshape((numEdges, 2))
#edges[:, 1] += numEdges


