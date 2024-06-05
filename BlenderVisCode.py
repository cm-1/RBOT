import bpy
import numpy as np

def clamp(x, min_val, max_val):
    return min(max_val, max(x, min_val))

# Returns an RGBA pixel from an image.
def pixelFromImg(image, x, y):
    w, h = image.size[:2]
    if x < 0 or x >= w or y < 0 or y >= h:
        raise Exception("Coordinates out of bounds!")
    index = y * w + x    # 1D index
    # We assume RGBA.
    return image.pixels[index * 4 : (index + 1) * 4]


# Get the loaded image from Blender 
image = bpy.data.images["frameSmall.png"]
sdt = bpy.data.images["sdtSmall.png"]
xyImage = bpy.data.images["xyDeltaSmall.png"]

print("image size:", np.array(image.pixels).shape, image.channels, image.depth)
print("sdt size:", np.array(sdt.pixels).shape, sdt.channels, sdt.depth)

# SRGB conversion comes from:
# https://entropymine.com/imageworsener/srgbformula/
# https://stackoverflow.com/questions/39792163/vectorizing-srgb-to-linear-conversion-properly-in-numpy
def to_srgb(img32):
    return np.where( img32 >= 0.04045,((img32 + 0.055) / 1.055)**2.4, img32/12.92 )

def to_rgb(pixels_np):
    pixels_srgb2 = np.where(
        pixels_np > 0.0031308,
        ((pixels_np ** (1.0/2.4)) * 1.055) - 0.055,
        pixels_np * 12.92
    )
    return pixels_srgb2

sdtData = 255 * np.array(sdt.pixels)[::4] - 8
print("sdtDataRange:", sdtData.min(), sdtData.max())
valid_pixels = abs(sdtData) < 8


# Pixels data is in row-major, whereas later it'll be more convenient to
# index by xy coordinate, so I transpose for now.
# Maybe not transposing and rewriting later code is more efficient, idk.
sdtData2D = sdtData.reshape((sdt.size[1], sdt.size[0])).transpose()

xyDataCorrected = np.round( (255 * np.array(xyImage.pixels)) - 8 ).astype(int)
xyDataRowsCols = xyDataCorrected.reshape(
    (xyImage.size[1], xyImage.size[0], xyImage.channels)
)[:,:,1:3]
xyData2D = xyDataRowsCols.transpose((1, 0, 2))
print("xy shape:", xyData2D.shape)
print("sdt2D shape:", sdtData2D.shape)
print("xy range:", xyData2D[:,:,1].min(), xyData2D[:,:,1].max())

# The array image.pixels contains all pixels in a flattened 1D array
# ordered in row-major form.
pixels_np = np.array(image.pixels)




pixels_srgb = to_srgb(pixels_np)

num_pixels =image.size[0] * image.size[1]

# Indices creates a grid of indices that you'd normally pass into
# another numpy array as actual, well, indices.
# E.g., `my_array[my_indices[0], my_indices[1]]`
# But to "join together" the "i[0]" and "i[1]", a transpose is needed.
pixel_indices_grid = np.indices(image.size[:2]).transpose((2,1,0))
# Then I flatten the 3-axis array into a 2-axis one (a list of index pairs)
pixel_coords_xy = pixel_indices_grid.reshape(num_pixels, 2)
# Then hstack is used to add a zero "channel" to the arrays.
# If this were a 2D image, one would use dstack instead.
zero_channel = np.ones((num_pixels, 1))
pixel_coords2 = np.hstack((zero_channel, pixel_coords_xy))
print("indices:", pixel_coords2)

sqObjOrig = bpy.data.objects.get("squirrel_demo_low")
sqObj = sqObjOrig.copy()
sqObj.data = sqObj.data.copy() # Copy mesh before we alter all vertex locations in obj copy

# https://blender.stackexchange.com/questions/159538/how-to-apply-all-transformations-to-an-object-at-low-level
sqObj.data.transform(sqObj.matrix_basis)
sqObj.matrix_basis.identity()
bpy.context.collection.objects.link(sqObj)

principal_point = np.array([324.328, 257.323])/4.0
def get_ray_xy(img_xy):
    flipped_co = np.array((img_xy[0], image.size[1] - img_xy[1]))
    ray_dir_xy = flipped_co - principal_point
    return ray_dir_xy

def add_ray_result_if_exists(xy_coord, arr, xyOverwrite = None):
    fLen = 650.0/4.0
    
    ray_dir_xy = get_ray_xy(xy_coord)
    ray_dir = np.array((ray_dir_xy[0], ray_dir_xy[1], fLen))
    hit, loc, norm, ind = sqObj.ray_cast((0,0,0), ray_dir)
    if (hit):
        if xyOverwrite is not None:
            overwrite_dir_xy = get_ray_xy(xyOverwrite)
            loc[0] = overwrite_dir_xy[0] * loc[2]/fLen
            loc[1] = overwrite_dir_xy[1] * loc[2]/fLen
        arr.append(loc)
    return hit



pixel_coords = []

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

ray_successes = np.full(valid_pixels.shape[0], True)
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
#        rayWorked = True
#        pixel_coords.append((xy_near[0], xy_near[1], 0))
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
        ray_successes[i] = False



bpy.data.objects.remove(sqObj)

# for x in range(image.size[0]):
#     for y in range(image.size[1]):
#         pixel_colours += (pixelFromImg(image, x, y))
#         pixel_coords.append((x, y, 0))


dots_obj = bpy.data.objects.get("Cube")

# To replace all vertices in a mesh, it seems easiest to just
# create a new mesh and delete the old one.

dotsMesh = bpy.data.meshes.new('dotsMesh')
# pixel_coords will be the verts; no edges and faces
dotsMesh.from_pydata(pixel_coords, [], [])
dotsMesh.update()

# Swap mesh and delete old.
mesh_to_del = dots_obj.data
dots_obj.data = dotsMesh
bpy.data.meshes.remove(mesh_to_del)

dots_obj.data.transform(sqObjOrig.matrix_basis.inverted())
dots_obj.matrix_basis = sqObjOrig.matrix_basis


# https://blender.stackexchange.com/questions/280716/python-code-to-set-color-attributes-per-vertex-in-blender-3-5
colattr = dotsMesh.color_attributes.new(
    name="Color",
    type='FLOAT_COLOR',
    domain='POINT',
)

# In foreach_set, pixel_colours must be flat/1D
colattr.data.foreach_set("color", pixels_srgb[np.repeat(valid_pixels, 4)])
print("Done!")



