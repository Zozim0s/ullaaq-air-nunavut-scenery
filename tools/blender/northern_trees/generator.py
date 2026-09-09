import bpy
import math
from pathlib import Path


# ============================================================
# Northern Trees
# v0.8c MID TEXTURE ATLAS PROOF - ROOT/TIP ANCHORED MID
#
# Fresh fork from the known-good v0.4a botanical master.
#
# Purpose:
#     prove a Laminar-style runtime tree representation in which
#     each furnished primary branch is replaced by one folded
#     two-triangle spray primitive.
#
# This file intentionally retains the v0.4a botanical machinery
# below as source/reference code, but the runtime build path does
# not instantiate modeled secondaries, short shoots, or needles.
#
# Runtime path:
#     leader/trunk geometry
#       + crown stations
#       + LOW / MID / TOP branch habit
#       + one 2-triangle folded spray per primary branch
#       + existing deterministic whole-tree variation
#
# This pass adds a self-contained diagnostic 3-cell UV atlas so we can prove
# that LOW / MID / TOP spray archetypes retain the intended atlas island
# through Geometry Nodes, instancing, variation, and final realization.
# ============================================================

# ============================================================
# Botanical source code inherited from v0.4a
#
# Mini-whorl tamarack rosette.
#
# v0.3c keeps the v0.3b woody / foliage-station architecture,
# but changes the foliage primitive again.
#
# Problem exposed by v0.3b:
#
#     one foliage station still read as one visible starburst
#
# New grammar:
#
#     short-shoot axis
#         |
#         +-- needle whorl
#         |
#         +-- needle whorl
#         |
#         +-- needle whorl
#         |
#         +-- needle whorl
#
# Each whorl is a small near-radial ring of needles. Successive
# rings are clocked around the short-shoot axis, which should
# hide the center of the individual rosette and produce a tiny
# bottle-brush tuft.
#
# Per-needle bounded length and azimuth variation remain.
#
# Secondary length remains decoupled from rosette size.
#
# Same parameters + same Seed = same tree.
# ============================================================

OBJECT_NAME = "NORTHERN_TREE_MID_TEXTURE_PROOF_V08C"
GROUP_NAME = "NorthernTree_Mid_Texture_Proof_V08C_GN"
MODIFIER_NAME = "Northern Trees MID Texture Proof v0.8c"

SPRAY_SOURCE_PREFIX = "NORTHERN_TREE_RUNTIME_SPRAY"
SPRAY_MESH_PREFIX = "NORTHERN_TREE_RUNTIME_SPRAY_MESH"

ATLAS_IMAGE_NAME = "NORTHERN_TREE_V08_ATLAS"
ATLAS_MATERIAL_NAME = "NORTHERN_TREE_V08_ATLAS_MAT"
ATLAS_SIZE = 1024
MID_SOURCE_FILENAME = "tamarack_mid_spray_source.png"
ATLAS_FILENAME = "tamarack_runtime_atlas_v0.8c.png"

# Three padded atlas islands in normalized UV coordinates.  The unused
# fourth quadrant gives us room for a later crown-tip/special archetype.
ATLAS_CELLS = {
    "LOW": (0.04, 0.54, 0.46, 0.96),
    "MID": (0.54, 0.54, 0.96, 0.96),
    "TOP": (0.04, 0.04, 0.46, 0.46),
}

# Stock-spruce forensic work showed a common folded two-triangle
# foliage primitive with about 110 degrees between face normals.
SPRAY_FOLD_DEGREES = 110.0
SPRAY_WING_RADIUS = 0.45       # relative to unit branch length
SPRAY_WING_STATION = 0.55      # position along the shared root-tip edge


def add_input(tree, name, socket_type, default, minimum=None, maximum=None,
              panel=None, description=""):
    sock = tree.interface.new_socket(
        name=name,
        in_out='INPUT',
        socket_type=socket_type,
        parent=panel,
        description=description,
    )
    sock.default_value = default
    if minimum is not None:
        sock.min_value = minimum
    if maximum is not None:
        sock.max_value = maximum
    return sock


def math_node(nodes, operation, name, x=0.0, y=0.0):
    node = nodes.new("ShaderNodeMath")
    node.name = name
    node.label = name
    node.operation = operation
    node.inputs[0].default_value = x
    node.inputs[1].default_value = y
    return node


def get_or_create_host():
    obj = bpy.data.objects.get(OBJECT_NAME)
    if obj is None:
        mesh = bpy.data.meshes.new(f"{OBJECT_NAME}_HOST")
        obj = bpy.data.objects.new(OBJECT_NAME, mesh)
        bpy.context.collection.objects.link(obj)

    for modifier in list(obj.modifiers):
        if modifier.name == MODIFIER_NAME:
            obj.modifiers.remove(modifier)

    return obj


# ============================================================
# Runtime folded-spray source
# ============================================================


def resolve_render_dir():
    """Return the working render/atlas directory and create it."""
    if bpy.data.filepath:
        output_dir = Path(bpy.data.filepath).resolve().parent / "renders"
    else:
        output_dir = (
            Path.home()
            / "linGames"
            / "Ullaaq-Air-Nunavik"
            / "work"
            / "Objects"
            / "Northern_Trees"
            / "renders"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def resolve_mid_source_path():
    """Find the clean RGBA MID source render made by v0.7c."""
    candidates = []

    if bpy.data.filepath:
        blend_dir = Path(bpy.data.filepath).resolve().parent
        candidates.extend([
            blend_dir / "renders" / MID_SOURCE_FILENAME,
            blend_dir / MID_SOURCE_FILENAME,
        ])

    fallback = (
        Path.home()
        / "linGames"
        / "Ullaaq-Air-Nunavik"
        / "work"
        / "Objects"
        / "Northern_Trees"
        / "renders"
        / MID_SOURCE_FILENAME
    )
    candidates.append(fallback)

    for path in candidates:
        if path.exists():
            return path

    checked = "\n".join(f"  {p}" for p in candidates)
    raise RuntimeError(
        "MID source render not found. Checked:\n" + checked
    )


def rect_pixels(rect):
    """Normalized atlas rectangle -> integer pixel bounds, end-exclusive."""
    u0, v0, u1, v1 = rect
    x0 = max(0, min(ATLAS_SIZE, round(u0 * ATLAS_SIZE)))
    y0 = max(0, min(ATLAS_SIZE, round(v0 * ATLAS_SIZE)))
    x1 = max(0, min(ATLAS_SIZE, round(u1 * ATLAS_SIZE)))
    y1 = max(0, min(ATLAS_SIZE, round(v1 * ATLAS_SIZE)))
    return x0, y0, x1, y1


def fill_diagnostic_cell(pixels, rect, base_color):
    """Fill LOW/TOP cells and retain the fold markers from v0.6a."""
    x0, y0, x1, y1 = rect_pixels(rect)
    w = max(1, x1 - x0)
    h = max(1, y1 - y0)

    for py in range(y0, y1):
        lv = (py - y0 + 0.5) / h
        for px in range(x0, x1):
            lu = (px - x0 + 0.5) / w
            color = list(base_color)

            if abs(lu - lv) < 0.025:
                color = [1.0, 1.0, 1.0, 1.0]

            if lu < 0.08 and lv < 0.08:
                color = [0.0, 0.0, 0.0, 1.0]

            if lu > 0.92 and lv > 0.92:
                color = [1.0, 1.0, 1.0, 1.0]

            i = (py * ATLAS_SIZE + px) * 4
            pixels[i:i+4] = color


def sample_source_bilinear(src, sw, sh, x, y):
    if x < 0.0 or y < 0.0 or x > sw - 1 or y > sh - 1:
        return (0.0, 0.0, 0.0, 0.0)

    x0 = int(math.floor(x))
    y0 = int(math.floor(y))
    x1 = min(sw - 1, x0 + 1)
    y1 = min(sh - 1, y0 + 1)

    tx = x - x0
    ty = y - y0

    def px(ix, iy):
        i = (iy * sw + ix) * 4
        return src[i:i+4]

    c00 = px(x0, y0)
    c10 = px(x1, y0)
    c01 = px(x0, y1)
    c11 = px(x1, y1)

    out = []
    for k in range(4):
        top = c00[k] * (1.0 - tx) + c10[k] * tx
        bot = c01[k] * (1.0 - tx) + c11[k] * tx
        out.append(top * (1.0 - ty) + bot * ty)
    return tuple(out)


def detect_root_tip_from_alpha(src, sw, sh, alpha_threshold=0.08):
    """Detect the source branch's root and tip from its clean alpha sprite.

    The v0.7 source is authored left-to-right:
        root = leftmost opaque end
        tip  = rightmost opaque end

    We average a narrow alpha-weighted band at each extreme rather than
    trusting a single antialiased pixel.
    """
    opaque = []

    for y in range(sh):
        for x in range(sw):
            i = (y * sw + x) * 4
            a = src[i + 3]
            if a > alpha_threshold:
                opaque.append((x, y, a))

    if not opaque:
        raise RuntimeError("MID source image contains no opaque pixels")

    min_x = min(p[0] for p in opaque)
    max_x = max(p[0] for p in opaque)
    width = max(1, max_x - min_x)

    band = max(3, int(width * 0.025))

    root_pts = [p for p in opaque if p[0] <= min_x + band]
    tip_pts = [p for p in opaque if p[0] >= max_x - band]

    def weighted_center(points):
        w = sum(p[2] for p in points)
        if w <= 1e-8:
            return (0.0, 0.0)
        return (
            sum(p[0] * p[2] for p in points) / w,
            sum(p[1] * p[2] for p in points) / w,
        )

    return weighted_center(root_pts), weighted_center(tip_pts), opaque


def blit_image_to_cell_root_anchored(pixels, source_image, rect):
    """Map the real MID sprite so its root lands on the runtime spray root
    and its root->tip chord follows the spray's shared UV diagonal.

    This deliberately prioritizes attachment continuity at the trunk.
    """
    source_image.colorspace_settings.name = 'sRGB'

    sw, sh = source_image.size
    if sw < 1 or sh < 1:
        raise RuntimeError("MID source image has invalid dimensions")

    src = [0.0] * (sw * sh * 4)
    source_image.pixels.foreach_get(src)

    root, tip, opaque = detect_root_tip_from_alpha(src, sw, sh)

    vx = tip[0] - root[0]
    vy = tip[1] - root[1]
    source_angle = math.atan2(vy, vx)

    target_angle = math.radians(45.0)
    rotate_by = target_angle - source_angle

    cr = math.cos(rotate_by)
    sr = math.sin(rotate_by)

    # Rotated opaque extents relative to the detected root.
    rotated = []
    for x, y, a in opaque:
        dx = x - root[0]
        dy = y - root[1]
        rx = cr * dx - sr * dy
        ry = sr * dx + cr * dy
        rotated.append((rx, ry))

    min_rx = min(p[0] for p in rotated)
    max_rx = max(p[0] for p in rotated)
    min_ry = min(p[1] for p in rotated)
    max_ry = max(p[1] for p in rotated)

    x0, y0, x1, y1 = rect_pixels(rect)
    dw = max(1, x1 - x0)
    dh = max(1, y1 - y0)

    # Root maps to the lower-left atlas corner because runtime vertex 0
    # maps there.  Fit the positive extents to the available cell.
    # Any small negative extent is reported; it represents source foliage
    # that reaches behind/below the branch root and may be clipped.
    avail_x = max(1.0, dw - 1.0)
    avail_y = max(1.0, dh - 1.0)

    positive_x = max(1.0, max_rx)
    positive_y = max(1.0, max_ry)

    scale = 0.94 * min(avail_x / positive_x, avail_y / positive_y)

    root_dx = 0.0
    root_dy = 0.0

    # Inverse rotation for destination -> source sampling.
    ci = math.cos(-rotate_by)
    si = math.sin(-rotate_by)

    for dy in range(dh):
        py = y0 + dy
        yy = (dy - root_dy) / scale

        for dx in range(dw):
            px = x0 + dx
            xx = (dx - root_dx) / scale

            sx_rel = ci * xx - si * yy
            sy_rel = si * xx + ci * yy

            sx = sx_rel + root[0]
            sy = sy_rel + root[1]

            rgba = sample_source_bilinear(src, sw, sh, sx, sy)
            di = (py * ATLAS_SIZE + px) * 4
            pixels[di:di+4] = rgba

    print(f"  MID detected root: ({root[0]:.1f}, {root[1]:.1f}) px")
    print(f"  MID detected tip : ({tip[0]:.1f}, {tip[1]:.1f}) px")
    print(f"  MID source root->tip angle: {math.degrees(source_angle):.2f} deg")
    print(f"  MID rotation applied       : {math.degrees(rotate_by):.2f} deg")
    print(f"  MID scale into cell        : {scale:.4f}")
    print(
        "  MID rotated extents rel root:"
        f" x={min_rx:.1f}..{max_rx:.1f},"
        f" y={min_ry:.1f}..{max_ry:.1f}"
    )
    if min_rx < -2.0 or min_ry < -2.0:
        print(
            "  NOTE: some source foliage extends behind/below the detected root;"
            " minor clipping is possible in this proof."
        )


def ensure_mixed_atlas():
    """Build one real shared atlas.

    LOW  = diagnostic warm cell
    MID  = actual v0.7c RGBA botanical branch render
    TOP  = diagnostic blue cell

    Everything outside those cells remains transparent.
    """
    mid_path = resolve_mid_source_path()

    old = bpy.data.images.get(ATLAS_IMAGE_NAME)
    if old is not None:
        bpy.data.images.remove(old)

    image = bpy.data.images.new(
        ATLAS_IMAGE_NAME,
        width=ATLAS_SIZE,
        height=ATLAS_SIZE,
        alpha=True,
        float_buffer=False,
    )

    # Transparent atlas background is required now that MID contains
    # a real alpha-cutout branch.
    pixels = [0.0, 0.0, 0.0, 0.0] * (ATLAS_SIZE * ATLAS_SIZE)

    fill_diagnostic_cell(
        pixels,
        ATLAS_CELLS["LOW"],
        (0.80, 0.22, 0.10, 1.0),
    )
    fill_diagnostic_cell(
        pixels,
        ATLAS_CELLS["TOP"],
        (0.18, 0.32, 0.82, 1.0),
    )

    mid_source = bpy.data.images.load(str(mid_path), check_existing=True)
    blit_image_to_cell_root_anchored(
        pixels,
        mid_source,
        ATLAS_CELLS["MID"],
    )

    image.pixels.foreach_set(pixels)
    image.update()

    output_path = resolve_render_dir() / ATLAS_FILENAME
    image.filepath_raw = str(output_path)
    image.file_format = 'PNG'
    image.save()

    print("")
    print("Runtime atlas:")
    print(f"  MID source : {mid_path}")
    print(f"  atlas      : {output_path}")
    print(f"  size       : {ATLAS_SIZE} x {ATLAS_SIZE}")
    print("  LOW        : diagnostic warm")
    print("  MID        : real RGBA branch (root/tip anchored to fold diagonal)")
    print("  TOP        : diagnostic blue")

    return image


def ensure_atlas_material(image):
    old = bpy.data.materials.get(ATLAS_MATERIAL_NAME)
    if old is not None:
        bpy.data.materials.remove(old)

    mat = bpy.data.materials.new(ATLAS_MATERIAL_NAME)
    mat.use_nodes = True

    # Blender 4.2+ / 5.x uses a surface render method rather than the
    # older blend_method property. Guard both so the proof is portable.
    if hasattr(mat, "surface_render_method"):
        try:
            mat.surface_render_method = 'DITHERED'
        except Exception:
            pass

    if hasattr(mat, "blend_method"):
        try:
            mat.blend_method = 'HASHED'
        except Exception:
            pass

    nt = mat.node_tree
    nt.nodes.clear()

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    output.location = (420, 0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (160, 0)
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = 0.8

    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.location = (-180, 0)
    tex.image = image
    tex.interpolation = 'Linear'
    tex.extension = 'CLIP'

    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    if "Alpha" in bsdf.inputs:
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])

    nt.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat


def ensure_runtime_spray_source(tag, uv_rect, material):
    """Create one reusable folded spray with an atlas-specific UV island.

    Geometry is identical for LOW/MID/TOP.  Only the UV rectangle differs.

    The two triangles share vertices 0 and 1.  In UV space those vertices
    occupy opposite corners of the atlas cell, so the shared 3-D fold edge
    is also the diagonal that splits the rectangular atlas island:

        uv2 -------- uv1 (tip)
         |          / |
         |        /   |
         |      /     |
         |    /       |
         |  /         |
        uv0 -------- uv3
       (root)

    Thus one ordinary rectangular branch image can be bent across the
    two-triangle spray without duplicating texture artwork.
    """

    obj_name = f"{SPRAY_SOURCE_PREFIX}_{tag}"
    mesh_name = f"{SPRAY_MESH_PREFIX}_{tag}"

    old_obj = bpy.data.objects.get(obj_name)
    if old_obj is not None:
        old_mesh = old_obj.data if old_obj.type == 'MESH' else None
        bpy.data.objects.remove(old_obj, do_unlink=True)
        if old_mesh is not None and old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)

    half = math.radians(SPRAY_FOLD_DEGREES * 0.5)
    y = SPRAY_WING_RADIUS * math.cos(half)
    z = SPRAY_WING_RADIUS * math.sin(half)

    verts = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (SPRAY_WING_STATION, y,  z),
        (SPRAY_WING_STATION, y, -z),
    ]

    faces = [
        (0, 1, 2),
        (3, 1, 0),
    ]

    mesh = bpy.data.meshes.new(mesh_name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # A rectangular atlas cell split along the root->tip diagonal.
    u0, v0, u1, v1 = uv_rect
    uv_by_vertex = {
        0: (u0, v0),       # root = lower-left
        1: (u1, v1),       # tip  = upper-right
        2: (u0, v1),       # upper-left
        3: (u1, v0),       # lower-right
    }

    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uv_by_vertex[vertex_index]

    mesh.materials.append(material)
    for poly in mesh.polygons:
        poly.material_index = 0

    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.display_type = 'WIRE'
    obj.hide_render = True
    obj.hide_set(True)

    return obj

def build_runtime_spray(nodes, links, group_in, source_obj, tag,
                        rise_input_name, base_y):
    """Return one adjustable folded runtime spray archetype.

    The botanical furnished branch remains available elsewhere in this
    file for later texture baking.  This representation deliberately
    collapses the entire visible branch system into two triangles.
    """

    object_info = nodes.new("GeometryNodeObjectInfo")
    object_info.location = (1500, base_y)
    object_info.label = f"{tag} Runtime Spray Source"
    object_info.inputs["Object"].default_value = source_obj
    if "As Instance" in object_info.inputs:
        object_info.inputs["As Instance"].default_value = False

    scale_xyz = nodes.new("ShaderNodeCombineXYZ")
    scale_xyz.location = (1700, base_y - 200)
    scale_xyz.label = f"{tag} Spray Scale"
    links.new(group_in.outputs["Primary Length"], scale_xyz.inputs["X"])
    links.new(group_in.outputs["Primary Length"], scale_xyz.inputs["Y"])
    links.new(group_in.outputs["Primary Length"], scale_xyz.inputs["Z"])

    rise_radians = math_node(
        nodes, 'MULTIPLY', f"{tag} Runtime Rise Degrees -> Radians",
        0.0, -math.pi / 180.0,
    )
    rise_radians.location = (1700, base_y - 400)
    links.new(group_in.outputs[rise_input_name], rise_radians.inputs[0])

    euler = nodes.new("ShaderNodeCombineXYZ")
    euler.location = (1900, base_y - 400)
    euler.label = f"{tag} Runtime Spray Euler"
    links.new(rise_radians.outputs[0], euler.inputs["Y"])

    rotation = nodes.new("FunctionNodeEulerToRotation")
    rotation.location = (2100, base_y - 400)
    rotation.label = f"{tag} Runtime Spray Rotation"
    links.new(euler.outputs["Vector"], rotation.inputs["Euler"])

    transform = nodes.new("GeometryNodeTransform")
    transform.location = (2300, base_y)
    transform.label = f"{tag} Two-Triangle Furnished Spray"
    links.new(object_info.outputs["Geometry"], transform.inputs["Geometry"])
    links.new(scale_xyz.outputs["Vector"], transform.inputs["Scale"])
    links.new(rotation.outputs["Rotation"], transform.inputs["Rotation"])

    return transform.outputs["Geometry"]


# ============================================================
# Leader
# ============================================================


def build_leader(nodes, links, group_in):
    end_xyz = nodes.new("ShaderNodeCombineXYZ")
    end_xyz.location = (-1000, 300)
    end_xyz.label = "Tree Height"
    links.new(group_in.outputs["Height"], end_xyz.inputs["Z"])

    leader = nodes.new("GeometryNodeCurvePrimitiveLine")
    leader.location = (-800, 300)
    leader.label = "Leader"
    leader.inputs["Start"].default_value = (0.0, 0.0, 0.0)
    links.new(end_xyz.outputs["Vector"], leader.inputs["End"])

    resample = nodes.new("GeometryNodeResampleCurve")
    resample.location = (-600, 300)
    resample.label = "Leader Segments"
    resample.inputs["Mode"].default_value = 'Count'
    links.new(leader.outputs["Curve"], resample.inputs["Curve"])
    links.new(group_in.outputs["Leader Points"], resample.inputs["Count"])

    factor = nodes.new("GeometryNodeSplineParameter")
    factor.location = (-600, -100)
    factor.label = "Height Factor"

    x_freq = math_node(nodes, 'MULTIPLY', "X Wander Frequency", 0.0, 11.0)
    x_freq.location = (-350, -250)
    links.new(factor.outputs["Factor"], x_freq.inputs[0])

    x_sin = nodes.new("ShaderNodeMath")
    x_sin.operation = 'SINE'
    x_sin.location = (-150, -250)
    x_sin.label = "X Wander"
    links.new(x_freq.outputs[0], x_sin.inputs[0])

    x_amp = math_node(nodes, 'MULTIPLY', "X Wander Amount")
    x_amp.location = (50, -250)
    links.new(x_sin.outputs[0], x_amp.inputs[0])
    links.new(group_in.outputs["Leader Wander"], x_amp.inputs[1])

    x_root = math_node(nodes, 'MULTIPLY', "Plant Root X")
    x_root.location = (250, -250)
    links.new(x_amp.outputs[0], x_root.inputs[0])
    links.new(factor.outputs["Factor"], x_root.inputs[1])

    y_freq = math_node(nodes, 'MULTIPLY', "Y Wander Frequency", 0.0, 17.0)
    y_freq.location = (-350, -450)
    links.new(factor.outputs["Factor"], y_freq.inputs[0])

    y_phase = math_node(nodes, 'ADD', "Y Phase", 0.0, 1.7)
    y_phase.location = (-150, -450)
    links.new(y_freq.outputs[0], y_phase.inputs[0])

    y_sin = nodes.new("ShaderNodeMath")
    y_sin.operation = 'SINE'
    y_sin.location = (50, -450)
    y_sin.label = "Y Wander"
    links.new(y_phase.outputs[0], y_sin.inputs[0])

    y_amp = math_node(nodes, 'MULTIPLY', "Y Wander Amount")
    y_amp.location = (250, -450)
    links.new(y_sin.outputs[0], y_amp.inputs[0])
    links.new(group_in.outputs["Leader Wander"], y_amp.inputs[1])

    y_root = math_node(nodes, 'MULTIPLY', "Plant Root Y")
    y_root.location = (450, -450)
    links.new(y_amp.outputs[0], y_root.inputs[0])
    links.new(factor.outputs["Factor"], y_root.inputs[1])

    wander_xyz = nodes.new("ShaderNodeCombineXYZ")
    wander_xyz.location = (500, -200)
    wander_xyz.label = "Leader Offset"
    links.new(x_root.outputs[0], wander_xyz.inputs["X"])
    links.new(y_root.outputs[0], wander_xyz.inputs["Y"])

    set_position = nodes.new("GeometryNodeSetPosition")
    set_position.location = (700, 300)
    set_position.label = "Crooked Leader"
    links.new(resample.outputs["Curve"], set_position.inputs["Geometry"])
    links.new(wander_xyz.outputs["Vector"], set_position.inputs["Offset"])

    half_diameter = math_node(nodes, 'MULTIPLY', "Diameter -> Radius", 0.0, 0.5)
    half_diameter.location = (700, 100)
    links.new(group_in.outputs["Base Diameter"], half_diameter.inputs[0])

    profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    profile.location = (900, 100)
    profile.label = "Cheap Trunk Profile"
    profile.inputs["Resolution"].default_value = 4
    links.new(half_diameter.outputs[0], profile.inputs["Radius"])

    taper = nodes.new("ShaderNodeMapRange")
    taper.location = (900, -100)
    taper.label = "Leader Taper"
    taper.inputs["From Min"].default_value = 0.0
    taper.inputs["From Max"].default_value = 1.0
    taper.inputs["To Min"].default_value = 1.0
    taper.inputs["To Max"].default_value = 0.10
    links.new(factor.outputs["Factor"], taper.inputs["Value"])

    leader_mesh = nodes.new("GeometryNodeCurveToMesh")
    leader_mesh.location = (1150, 300)
    leader_mesh.label = "Leader Mesh"
    links.new(set_position.outputs["Geometry"], leader_mesh.inputs["Curve"])
    links.new(profile.outputs["Curve"], leader_mesh.inputs["Profile Curve"])
    links.new(taper.outputs["Result"], leader_mesh.inputs["Scale"])
    if "Fill Caps" in leader_mesh.inputs:
        leader_mesh.inputs["Fill Caps"].default_value = True

    return leader_mesh.outputs["Mesh"], set_position.outputs["Geometry"]


# ============================================================
# Crown stations
# ============================================================


def build_crown_stations(nodes, links, group_in, leader_curve_socket):
    """
    Build crown stations with bounded deterministic spacing variation.

    The underlying station set remains lawful:
        - Crown Start fixed
        - Crown End fixed
        - Tier Count fixed
        - nominal mean spacing fixed

    Only the interior station heights receive a small deterministic
    offset.  End-point weighting forces the first and last crown
    stations to remain exactly anchored.

    v0.1m uses a global-Z offset.  With the intentionally restrained
    leader wander this is effectively along the leader while keeping
    the node graph simple and stable.
    """

    crown_trim = nodes.new("GeometryNodeTrimCurve")
    crown_trim.location = (900, 550)
    crown_trim.label = "Crown Zone"
    crown_trim.mode = 'FACTOR'
    links.new(leader_curve_socket, crown_trim.inputs["Curve"])
    links.new(group_in.outputs["Crown Start"], crown_trim.inputs["Start"])
    links.new(group_in.outputs["Crown End"], crown_trim.inputs["End"])

    crown_points = nodes.new("GeometryNodeCurveToPoints")
    crown_points.location = (1150, 550)
    crown_points.label = "Nominal Crown Stations"
    crown_points.mode = 'COUNT'
    links.new(crown_trim.outputs["Curve"], crown_points.inputs["Curve"])
    links.new(group_in.outputs["Tier Count"], crown_points.inputs["Count"])

    # --------------------------------------------------------
    # Tier identity and normalized crown position
    # --------------------------------------------------------

    tier_index = nodes.new("GeometryNodeInputIndex")
    tier_index.location = (1350, 250)
    tier_index.label = "Spacing Tier Index"

    last_index = math_node(
        nodes, 'SUBTRACT', "Spacing Last Tier Index", 0.0, 1.0,
    )
    last_index.location = (1350, 50)
    links.new(group_in.outputs["Tier Count"], last_index.inputs[0])

    tier_factor = nodes.new("ShaderNodeMapRange")
    tier_factor.location = (1550, 150)
    tier_factor.label = "Spacing Crown Factor"
    tier_factor.inputs["From Min"].default_value = 0.0
    tier_factor.inputs["To Min"].default_value = 0.0
    tier_factor.inputs["To Max"].default_value = 1.0
    links.new(tier_index.outputs["Index"], tier_factor.inputs["Value"])
    links.new(last_index.outputs[0], tier_factor.inputs["From Max"])

    # --------------------------------------------------------
    # Endpoint protection:
    #
    #     4 * t * (1 - t)
    #
    # Gives 0 at crown start/end and 1 at crown midpoint.
    # --------------------------------------------------------

    one_minus_t = math_node(
        nodes, 'SUBTRACT', "1 - Spacing Crown Factor", 1.0, 0.0,
    )
    one_minus_t.location = (1750, 50)
    links.new(tier_factor.outputs["Result"], one_minus_t.inputs[1])

    endpoint_product = math_node(
        nodes, 'MULTIPLY', "Spacing Endpoint Product",
    )
    endpoint_product.location = (1950, 100)
    links.new(tier_factor.outputs["Result"], endpoint_product.inputs[0])
    links.new(one_minus_t.outputs[0], endpoint_product.inputs[1])

    endpoint_weight = math_node(
        nodes, 'MULTIPLY', "Spacing Endpoint Weight", 0.0, 4.0,
    )
    endpoint_weight.location = (2150, 100)
    links.new(endpoint_product.outputs[0], endpoint_weight.inputs[0])

    # --------------------------------------------------------
    # Nominal crown spacing in metres:
    #
    #     Height * (Crown End - Crown Start) / (Tier Count - 1)
    # --------------------------------------------------------

    crown_fraction = math_node(
        nodes, 'SUBTRACT', "Crown Fraction Length",
    )
    crown_fraction.location = (1550, -100)
    links.new(group_in.outputs["Crown End"], crown_fraction.inputs[0])
    links.new(group_in.outputs["Crown Start"], crown_fraction.inputs[1])

    crown_height = math_node(
        nodes, 'MULTIPLY', "Approx Crown Height",
    )
    crown_height.location = (1750, -100)
    links.new(group_in.outputs["Height"], crown_height.inputs[0])
    links.new(crown_fraction.outputs[0], crown_height.inputs[1])

    nominal_spacing = math_node(
        nodes, 'DIVIDE', "Nominal Tier Spacing",
    )
    nominal_spacing.location = (1950, -100)
    links.new(crown_height.outputs[0], nominal_spacing.inputs[0])
    links.new(last_index.outputs[0], nominal_spacing.inputs[1])

    jitter_limit = math_node(
        nodes, 'MULTIPLY', "Tier Spacing Jitter Limit",
    )
    jitter_limit.location = (2150, -100)
    links.new(nominal_spacing.outputs[0], jitter_limit.inputs[0])
    links.new(group_in.outputs["Tier Spacing Variation"], jitter_limit.inputs[1])

    # --------------------------------------------------------
    # Deterministic signed tier hash, decorrelated from branch
    # length and branch azimuth channels.
    # --------------------------------------------------------

    seed_offset = math_node(
        nodes, 'MULTIPLY', "Spacing Seed Offset", 0.0, 131.0,
    )
    seed_offset.location = (1550, -300)
    links.new(group_in.outputs["Seed"], seed_offset.inputs[0])

    seeded_tier = math_node(
        nodes, 'ADD', "Spacing Tier + Seed",
    )
    seeded_tier.location = (1750, -300)
    links.new(tier_index.outputs["Index"], seeded_tier.inputs[0])
    links.new(seed_offset.outputs[0], seeded_tier.inputs[1])

    spacing_key = math_node(
        nodes, 'ADD', "Spacing Variation Key", 0.0, 23.719,
    )
    spacing_key.location = (1950, -300)
    links.new(seeded_tier.outputs[0], spacing_key.inputs[0])

    spacing_hash = build_hash_01(
        nodes, links, spacing_key.outputs[0],
        "Tier Spacing Variation", 2150, -300,
        frequency=41.731,
        multiplier=27183.391,
        phase=9.137,
    )

    hash_times_two = math_node(
        nodes, 'MULTIPLY', "Spacing Hash x2", 0.0, 2.0,
    )
    hash_times_two.location = (2950, -300)
    links.new(spacing_hash, hash_times_two.inputs[0])

    signed_hash = math_node(
        nodes, 'SUBTRACT', "Signed Spacing Hash", 0.0, 1.0,
    )
    signed_hash.location = (3150, -300)
    links.new(hash_times_two.outputs[0], signed_hash.inputs[0])

    jitter_distance = math_node(
        nodes, 'MULTIPLY', "Raw Tier Spacing Jitter",
    )
    jitter_distance.location = (3350, -250)
    links.new(signed_hash.outputs[0], jitter_distance.inputs[0])
    links.new(jitter_limit.outputs[0], jitter_distance.inputs[1])

    protected_jitter = math_node(
        nodes, 'MULTIPLY', "Protected Tier Spacing Jitter",
    )
    protected_jitter.location = (3550, -200)
    links.new(jitter_distance.outputs[0], protected_jitter.inputs[0])
    links.new(endpoint_weight.outputs[0], protected_jitter.inputs[1])

    # --------------------------------------------------------
    # Apply station-height offset.
    # --------------------------------------------------------

    jitter_vector = nodes.new("ShaderNodeCombineXYZ")
    jitter_vector.location = (3750, -150)
    jitter_vector.label = "Tier Spacing Offset"
    links.new(protected_jitter.outputs[0], jitter_vector.inputs["Z"])

    jittered_points = nodes.new("GeometryNodeSetPosition")
    jittered_points.location = (3950, 550)
    jittered_points.label = "Jittered Crown Stations"
    links.new(crown_points.outputs["Points"], jittered_points.inputs["Geometry"])
    links.new(jitter_vector.outputs["Vector"], jittered_points.inputs["Offset"])

    return jittered_points.outputs["Geometry"], crown_points.outputs["Rotation"]


# ============================================================
# Primary branch habits
# ============================================================


def build_primary_branch(nodes, links, group_in, tag, rise_input_name,
                         curvature_input_name=None, curvature_default=1.0,
                         base_y=1100):
    rise_radians = math_node(
        nodes, 'MULTIPLY', f"{tag} Rise Degrees -> Radians",
        0.0, math.pi / 180.0,
    )
    rise_radians.location = (-1100, base_y - 300)
    links.new(group_in.outputs[rise_input_name], rise_radians.inputs[0])

    rise_cos = nodes.new("ShaderNodeMath")
    rise_cos.operation = 'COSINE'
    rise_cos.location = (-900, base_y - 300)
    rise_cos.label = f"{tag} Rise Cosine"
    links.new(rise_radians.outputs[0], rise_cos.inputs[0])

    rise_sin = nodes.new("ShaderNodeMath")
    rise_sin.operation = 'SINE'
    rise_sin.location = (-900, base_y - 500)
    rise_sin.label = f"{tag} Rise Sine"
    links.new(rise_radians.outputs[0], rise_sin.inputs[0])

    horizontal_length = math_node(nodes, 'MULTIPLY', f"{tag} Horizontal Length")
    horizontal_length.location = (-700, base_y - 250)
    links.new(group_in.outputs["Primary Length"], horizontal_length.inputs[0])
    links.new(rise_cos.outputs[0], horizontal_length.inputs[1])

    vertical_rise = math_node(nodes, 'MULTIPLY', f"{tag} Vertical Rise")
    vertical_rise.location = (-700, base_y - 500)
    links.new(group_in.outputs["Primary Length"], vertical_rise.inputs[0])
    links.new(rise_sin.outputs[0], vertical_rise.inputs[1])

    branch_end = nodes.new("ShaderNodeCombineXYZ")
    branch_end.location = (-500, base_y)
    branch_end.label = f"{tag} Branch Length"
    links.new(horizontal_length.outputs[0], branch_end.inputs["X"])

    branch_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    branch_line.location = (-300, base_y)
    branch_line.label = f"{tag} Primary Branch"
    branch_line.inputs["Start"].default_value = (0.0, 0.0, 0.0)
    links.new(branch_end.outputs["Vector"], branch_line.inputs["End"])

    branch_resample = nodes.new("GeometryNodeResampleCurve")
    branch_resample.location = (-100, base_y)
    branch_resample.label = f"{tag} Branch Segments"
    branch_resample.inputs["Mode"].default_value = 'Count'
    branch_resample.inputs["Count"].default_value = 8
    links.new(branch_line.outputs["Curve"], branch_resample.inputs["Curve"])

    branch_factor = nodes.new("GeometryNodeSplineParameter")
    branch_factor.location = (-100, base_y - 250)
    branch_factor.label = f"{tag} Branch Factor"

    departure = math_node(nodes, 'MULTIPLY', f"{tag} Departure Rise")
    departure.location = (100, base_y - 500)
    links.new(branch_factor.outputs["Factor"], departure.inputs[0])
    links.new(vertical_rise.outputs[0], departure.inputs[1])

    sag_amount_base = math_node(nodes, 'MULTIPLY', f"{tag} Sag Amount")
    sag_amount_base.location = (100, base_y - 200)
    links.new(group_in.outputs["Branch Sag"], sag_amount_base.inputs[0])
    if curvature_input_name is None:
        sag_amount_base.inputs[1].default_value = curvature_default
    else:
        links.new(group_in.outputs[curvature_input_name], sag_amount_base.inputs[1])

    one_minus_t = math_node(nodes, 'SUBTRACT', f"{tag} 1 - Factor", 1.0, 0.0)
    one_minus_t.location = (100, base_y - 50)
    links.new(branch_factor.outputs["Factor"], one_minus_t.inputs[1])

    sag_product = math_node(nodes, 'MULTIPLY', f"{tag} Sag Product")
    sag_product.location = (300, base_y - 50)
    links.new(branch_factor.outputs["Factor"], sag_product.inputs[0])
    links.new(one_minus_t.outputs[0], sag_product.inputs[1])

    sag_four = math_node(nodes, 'MULTIPLY', f"{tag} Sag x4", 0.0, 4.0)
    sag_four.location = (500, base_y - 50)
    links.new(sag_product.outputs[0], sag_four.inputs[0])

    sag_magnitude = math_node(nodes, 'MULTIPLY', f"{tag} Apply Sag")
    sag_magnitude.location = (700, base_y - 50)
    links.new(sag_four.outputs[0], sag_magnitude.inputs[0])
    links.new(sag_amount_base.outputs[0], sag_magnitude.inputs[1])

    sag_down = math_node(nodes, 'MULTIPLY', f"{tag} Sag Downward", 0.0, -1.0)
    sag_down.location = (900, base_y - 50)
    links.new(sag_magnitude.outputs[0], sag_down.inputs[0])

    recovery_amount = math_node(nodes, 'MULTIPLY', f"{tag} Recovery Amount")
    recovery_amount.location = (300, base_y - 300)
    links.new(group_in.outputs["Tip Recovery"], recovery_amount.inputs[0])
    if curvature_input_name is None:
        recovery_amount.inputs[1].default_value = curvature_default
    else:
        links.new(group_in.outputs[curvature_input_name], recovery_amount.inputs[1])

    recovery = math_node(nodes, 'MULTIPLY', f"{tag} Tip Recovery")
    recovery.location = (500, base_y - 300)
    links.new(branch_factor.outputs["Factor"], recovery.inputs[0])
    links.new(recovery_amount.outputs[0], recovery.inputs[1])

    rise_plus_sag = math_node(nodes, 'ADD', f"{tag} Rise + Sag")
    rise_plus_sag.location = (1100, base_y - 200)
    links.new(departure.outputs[0], rise_plus_sag.inputs[0])
    links.new(sag_down.outputs[0], rise_plus_sag.inputs[1])

    branch_z = math_node(nodes, 'ADD', f"{tag} Final Vertical Shape")
    branch_z.location = (1300, base_y - 200)
    links.new(rise_plus_sag.outputs[0], branch_z.inputs[0])
    links.new(recovery.outputs[0], branch_z.inputs[1])

    branch_offset = nodes.new("ShaderNodeCombineXYZ")
    branch_offset.location = (1500, base_y - 200)
    branch_offset.label = f"{tag} Branch Offset"
    links.new(branch_z.outputs[0], branch_offset.inputs["Z"])

    branch_set_position = nodes.new("GeometryNodeSetPosition")
    branch_set_position.location = (1700, base_y)
    branch_set_position.label = f"{tag} Shaped Branch"
    links.new(branch_resample.outputs["Curve"], branch_set_position.inputs["Geometry"])
    links.new(branch_offset.outputs["Vector"], branch_set_position.inputs["Offset"])

    branch_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    branch_profile.location = (1700, base_y - 250)
    branch_profile.label = f"{tag} Branch Profile"
    branch_profile.inputs["Resolution"].default_value = 3
    links.new(group_in.outputs["Branch Base Radius"], branch_profile.inputs["Radius"])

    branch_taper = nodes.new("ShaderNodeMapRange")
    branch_taper.location = (1900, base_y - 250)
    branch_taper.label = f"{tag} Branch Taper"
    branch_taper.inputs["From Min"].default_value = 0.0
    branch_taper.inputs["From Max"].default_value = 1.0
    branch_taper.inputs["To Min"].default_value = 1.0
    branch_taper.inputs["To Max"].default_value = 0.12
    links.new(branch_factor.outputs["Factor"], branch_taper.inputs["Value"])

    branch_mesh = nodes.new("GeometryNodeCurveToMesh")
    branch_mesh.location = (2100, base_y)
    branch_mesh.label = f"{tag} Branch Mesh"
    links.new(branch_set_position.outputs["Geometry"], branch_mesh.inputs["Curve"])
    links.new(branch_profile.outputs["Curve"], branch_mesh.inputs["Profile Curve"])
    links.new(branch_taper.outputs["Result"], branch_mesh.inputs["Scale"])
    if "Fill Caps" in branch_mesh.inputs:
        branch_mesh.inputs["Fill Caps"].default_value = True

    return branch_mesh.outputs["Mesh"], branch_set_position.outputs["Geometry"]



# ============================================================
# Tamarack rosette primitive
# ============================================================


def build_rosette_primitive(nodes, links, group_in):
    """
    Build one tamarack short-shoot rosette as several tiny needle whorls.

    Local frame:

        local Z
            supporting shoot tangent / short-shoot axis

        local XY
            radial needle plane

    Each foliage station produces one short woody spur carrying multiple
    clocked whorls.  The goal is to make the tuft read as a tiny
    bottle-brush cluster rather than a single obvious star.
    """

    # --------------------------------------------------------
    # One tapered needle, pointing local +X
    # --------------------------------------------------------

    needle_end = nodes.new("ShaderNodeCombineXYZ")
    needle_end.location = (1500, 5200)
    needle_end.label = "Needle Length"

    links.new(
        group_in.outputs["Needle Length"],
        needle_end.inputs["X"],
    )

    needle_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    needle_line.location = (1700, 5200)
    needle_line.label = "Needle"
    needle_line.inputs["Start"].default_value = (0.0, 0.0, 0.0)

    links.new(
        needle_end.outputs["Vector"],
        needle_line.inputs["End"],
    )

    needle_factor = nodes.new("GeometryNodeSplineParameter")
    needle_factor.location = (1700, 5000)
    needle_factor.label = "Needle Factor"

    needle_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    needle_profile.location = (1900, 5000)
    needle_profile.label = "Needle Profile"
    needle_profile.inputs["Resolution"].default_value = 3

    links.new(
        group_in.outputs["Needle Radius"],
        needle_profile.inputs["Radius"],
    )

    needle_taper = nodes.new("ShaderNodeMapRange")
    needle_taper.location = (2100, 5000)
    needle_taper.label = "Needle Taper"
    needle_taper.inputs["From Min"].default_value = 0.0
    needle_taper.inputs["From Max"].default_value = 1.0
    needle_taper.inputs["To Min"].default_value = 1.0
    needle_taper.inputs["To Max"].default_value = 0.10

    links.new(
        needle_factor.outputs["Factor"],
        needle_taper.inputs["Value"],
    )

    needle_mesh = nodes.new("GeometryNodeCurveToMesh")
    needle_mesh.location = (2300, 5200)
    needle_mesh.label = "Needle Mesh"

    links.new(
        needle_line.outputs["Curve"],
        needle_mesh.inputs["Curve"],
    )
    links.new(
        needle_profile.outputs["Curve"],
        needle_mesh.inputs["Profile Curve"],
    )
    links.new(
        needle_taper.outputs["Result"],
        needle_mesh.inputs["Scale"],
    )

    if "Fill Caps" in needle_mesh.inputs:
        needle_mesh.inputs["Fill Caps"].default_value = True

    # --------------------------------------------------------
    # Tiny woody short-shoot axis along local Z
    # --------------------------------------------------------

    spur_end = nodes.new("ShaderNodeCombineXYZ")
    spur_end.location = (1500, 5550)
    spur_end.label = "Short Shoot Length"

    links.new(
        group_in.outputs["Short Shoot Length"],
        spur_end.inputs["Z"],
    )

    spur_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    spur_line.location = (1700, 5550)
    spur_line.label = "Short Shoot Axis"
    spur_line.inputs["Start"].default_value = (0.0, 0.0, 0.0)

    links.new(
        spur_end.outputs["Vector"],
        spur_line.inputs["End"],
    )

    spur_radius = math_node(
        nodes,
        'MULTIPLY',
        "Short Shoot Radius",
        0.0,
        1.6,
    )
    spur_radius.location = (1700, 5350)

    links.new(
        group_in.outputs["Needle Radius"],
        spur_radius.inputs[0],
    )

    spur_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    spur_profile.location = (1900, 5350)
    spur_profile.label = "Short Shoot Profile"
    spur_profile.inputs["Resolution"].default_value = 3

    links.new(
        spur_radius.outputs[0],
        spur_profile.inputs["Radius"],
    )

    spur_factor = nodes.new("GeometryNodeSplineParameter")
    spur_factor.location = (1900, 5650)
    spur_factor.label = "Short Shoot Factor"

    spur_taper = nodes.new("ShaderNodeMapRange")
    spur_taper.location = (2100, 5350)
    spur_taper.label = "Short Shoot Taper"
    spur_taper.inputs["From Min"].default_value = 0.0
    spur_taper.inputs["From Max"].default_value = 1.0
    spur_taper.inputs["To Min"].default_value = 1.0
    spur_taper.inputs["To Max"].default_value = 0.45

    links.new(
        spur_factor.outputs["Factor"],
        spur_taper.inputs["Value"],
    )

    spur_mesh = nodes.new("GeometryNodeCurveToMesh")
    spur_mesh.location = (2300, 5550)
    spur_mesh.label = "Short Shoot Mesh"

    links.new(
        spur_line.outputs["Curve"],
        spur_mesh.inputs["Curve"],
    )
    links.new(
        spur_profile.outputs["Curve"],
        spur_mesh.inputs["Profile Curve"],
    )
    links.new(
        spur_taper.outputs["Result"],
        spur_mesh.inputs["Scale"],
    )

    if "Fill Caps" in spur_mesh.inputs:
        spur_mesh.inputs["Fill Caps"].default_value = True

    # --------------------------------------------------------
    # Total needle count:
    #
    #     Rosette Rings * Needles Per Ring
    # --------------------------------------------------------

    total_needles = math_node(
        nodes,
        'MULTIPLY',
        "Total Needles Per Rosette",
    )
    total_needles.location = (2500, 5450)

    links.new(
        group_in.outputs["Rosette Rings"],
        total_needles.inputs[0],
    )
    links.new(
        group_in.outputs["Needles Per Ring"],
        total_needles.inputs[1],
    )

    needle_points = nodes.new("GeometryNodeMeshLine")
    needle_points.location = (2700, 5200)
    needle_points.label = "Rosette Needle Origins"
    needle_points.mode = 'OFFSET'
    needle_points.count_mode = 'TOTAL'
    needle_points.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
    needle_points.inputs["Offset"].default_value = (0.0, 0.0, 0.0)

    links.new(
        total_needles.outputs[0],
        needle_points.inputs["Count"],
    )

    needle_index = nodes.new("GeometryNodeInputIndex")
    needle_index.location = (2700, 4950)
    needle_index.label = "Rosette Needle Index"

    # --------------------------------------------------------
    # Split global needle index into:
    #
    #     ring index
    #     needle index within ring
    # --------------------------------------------------------

    ring_divide = math_node(
        nodes,
        'DIVIDE',
        "Rosette Ring Index Raw",
    )
    ring_divide.location = (2900, 4950)

    links.new(
        needle_index.outputs["Index"],
        ring_divide.inputs[0],
    )
    links.new(
        group_in.outputs["Needles Per Ring"],
        ring_divide.inputs[1],
    )

    ring_index = nodes.new("ShaderNodeMath")
    ring_index.operation = 'FLOOR'
    ring_index.location = (3100, 4950)
    ring_index.label = "Rosette Ring Index"

    links.new(
        ring_divide.outputs[0],
        ring_index.inputs[0],
    )

    needle_in_ring = math_node(
        nodes,
        'MODULO',
        "Needle Index Within Ring",
        0.0,
        6.0,
    )
    needle_in_ring.location = (2900, 4750)

    links.new(
        needle_index.outputs["Index"],
        needle_in_ring.inputs[0],
    )
    links.new(
        group_in.outputs["Needles Per Ring"],
        needle_in_ring.inputs[1],
    )

    # --------------------------------------------------------
    # Place whorls along the short-shoot axis.
    #
    # Ring centers sit at:
    #
    #     (ring + 0.5) / ring_count
    #
    # so neither first nor last whorl lands exactly on an endpoint.
    # --------------------------------------------------------

    ring_plus_half = math_node(
        nodes,
        'ADD',
        "Rosette Ring + Half",
        0.0,
        0.5,
    )
    ring_plus_half.location = (3300, 4950)

    links.new(
        ring_index.outputs[0],
        ring_plus_half.inputs[0],
    )

    ring_factor = math_node(
        nodes,
        'DIVIDE',
        "Rosette Ring Position 0..1",
    )
    ring_factor.location = (3500, 4950)

    links.new(
        ring_plus_half.outputs[0],
        ring_factor.inputs[0],
    )
    links.new(
        group_in.outputs["Rosette Rings"],
        ring_factor.inputs[1],
    )

    ring_z = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Ring Z",
    )
    ring_z.location = (3700, 4950)

    links.new(
        ring_factor.outputs[0],
        ring_z.inputs[0],
    )
    links.new(
        group_in.outputs["Short Shoot Length"],
        ring_z.inputs[1],
    )

    ring_position = nodes.new("ShaderNodeCombineXYZ")
    ring_position.location = (3900, 4950)
    ring_position.label = "Rosette Ring Position"

    links.new(
        ring_z.outputs[0],
        ring_position.inputs["Z"],
    )

    place_needle_points = nodes.new("GeometryNodeSetPosition")
    place_needle_points.location = (4100, 5200)
    place_needle_points.label = "Place Needle Whorls"

    links.new(
        needle_points.outputs["Mesh"],
        place_needle_points.inputs["Geometry"],
    )
    links.new(
        ring_position.outputs["Vector"],
        place_needle_points.inputs["Position"],
    )

    # --------------------------------------------------------
    # Base angular position inside each whorl
    # --------------------------------------------------------

    ring_step = math_node(
        nodes,
        'DIVIDE',
        "Needle Step Within Whorl",
        math.tau,
        6.0,
    )
    ring_step.location = (3300, 4700)

    links.new(
        group_in.outputs["Needles Per Ring"],
        ring_step.inputs[1],
    )

    needle_base_azimuth = math_node(
        nodes,
        'MULTIPLY',
        "Needle Base Azimuth",
    )
    needle_base_azimuth.location = (3500, 4700)

    links.new(
        needle_in_ring.outputs[0],
        needle_base_azimuth.inputs[0],
    )
    links.new(
        ring_step.outputs[0],
        needle_base_azimuth.inputs[1],
    )

    # --------------------------------------------------------
    # Successive-ring clocking
    # --------------------------------------------------------

    ring_clock_rad = math_node(
        nodes,
        'MULTIPLY',
        "Ring Clock Degrees -> Radians",
        0.0,
        math.pi / 180.0,
    )
    ring_clock_rad.location = (3300, 4500)

    links.new(
        group_in.outputs["Ring Clock Step"],
        ring_clock_rad.inputs[0],
    )

    ring_clock_angle = math_node(
        nodes,
        'MULTIPLY',
        "Successive Rosette Ring Clock",
    )
    ring_clock_angle.location = (3500, 4500)

    links.new(
        ring_index.outputs[0],
        ring_clock_angle.inputs[0],
    )
    links.new(
        ring_clock_rad.outputs[0],
        ring_clock_angle.inputs[1],
    )

    base_clocked_azimuth = math_node(
        nodes,
        'ADD',
        "Clocked Needle Azimuth",
    )
    base_clocked_azimuth.location = (3700, 4600)

    links.new(
        needle_base_azimuth.outputs[0],
        base_clocked_azimuth.inputs[0],
    )
    links.new(
        ring_clock_angle.outputs[0],
        base_clocked_azimuth.inputs[1],
    )

    # --------------------------------------------------------
    # Deterministic per-needle key
    # --------------------------------------------------------

    rosette_seed = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Seed Offset",
        0.0,
        617.0,
    )
    rosette_seed.location = (2900, 4250)

    links.new(
        group_in.outputs["Seed"],
        rosette_seed.inputs[0],
    )

    needle_key_base = math_node(
        nodes,
        'ADD',
        "Rosette Needle Index + Seed",
    )
    needle_key_base.location = (3100, 4250)

    links.new(
        needle_index.outputs["Index"],
        needle_key_base.inputs[0],
    )
    links.new(
        rosette_seed.outputs[0],
        needle_key_base.inputs[1],
    )

    # --------------------------------------------------------
    # Per-needle azimuth jitter
    # --------------------------------------------------------

    az_key = math_node(
        nodes,
        'ADD',
        "Rosette Azimuth Key",
        0.0,
        11.0,
    )
    az_key.location = (3300, 4250)

    links.new(
        needle_key_base.outputs[0],
        az_key.inputs[0],
    )

    az_hash = build_hash_01(
        nodes,
        links,
        az_key.outputs[0],
        "Rosette Azimuth",
        3500,
        4250,
        frequency=41.173,
        multiplier=13849.257,
        phase=7.1,
    )

    az_hash_two = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Azimuth Hash x2",
        0.0,
        2.0,
    )
    az_hash_two.location = (4300, 4250)

    links.new(
        az_hash,
        az_hash_two.inputs[0],
    )

    az_signed = math_node(
        nodes,
        'SUBTRACT',
        "Rosette Signed Azimuth Hash",
        0.0,
        1.0,
    )
    az_signed.location = (4500, 4250)

    links.new(
        az_hash_two.outputs[0],
        az_signed.inputs[0],
    )

    az_jitter_deg = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Azimuth Jitter Degrees",
    )
    az_jitter_deg.location = (4700, 4250)

    links.new(
        az_signed.outputs[0],
        az_jitter_deg.inputs[0],
    )
    links.new(
        group_in.outputs["Needle Azimuth Variation"],
        az_jitter_deg.inputs[1],
    )

    az_jitter_rad = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Azimuth Jitter Radians",
        0.0,
        math.pi / 180.0,
    )
    az_jitter_rad.location = (4900, 4250)

    links.new(
        az_jitter_deg.outputs[0],
        az_jitter_rad.inputs[0],
    )

    final_azimuth = math_node(
        nodes,
        'ADD',
        "Final Needle Azimuth",
    )
    final_azimuth.location = (5100, 4600)

    links.new(
        base_clocked_azimuth.outputs[0],
        final_azimuth.inputs[0],
    )
    links.new(
        az_jitter_rad.outputs[0],
        final_azimuth.inputs[1],
    )

    # --------------------------------------------------------
    # Per-needle length variation
    # --------------------------------------------------------

    len_key = math_node(
        nodes,
        'ADD',
        "Rosette Length Key",
        0.0,
        29.0,
    )
    len_key.location = (3300, 4050)

    links.new(
        needle_key_base.outputs[0],
        len_key.inputs[0],
    )

    len_hash = build_hash_01(
        nodes,
        links,
        len_key.outputs[0],
        "Rosette Length",
        3500,
        4050,
        frequency=53.917,
        multiplier=16703.629,
        phase=3.9,
    )

    len_hash_two = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Length Hash x2",
        0.0,
        2.0,
    )
    len_hash_two.location = (4300, 4050)

    links.new(
        len_hash,
        len_hash_two.inputs[0],
    )

    len_signed = math_node(
        nodes,
        'SUBTRACT',
        "Rosette Signed Length Hash",
        0.0,
        1.0,
    )
    len_signed.location = (4500, 4050)

    links.new(
        len_hash_two.outputs[0],
        len_signed.inputs[0],
    )

    len_variation = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Needle Length Variation",
    )
    len_variation.location = (4700, 4050)

    links.new(
        len_signed.outputs[0],
        len_variation.inputs[0],
    )
    links.new(
        group_in.outputs["Needle Length Variation"],
        len_variation.inputs[1],
    )

    length_scale = math_node(
        nodes,
        'ADD',
        "Rosette Needle Length Scale",
        1.0,
        0.0,
    )
    length_scale.location = (4900, 4050)

    links.new(
        len_variation.outputs[0],
        length_scale.inputs[1],
    )

    # --------------------------------------------------------
    # Mild alternating cone angle for 3D tuft depth
    # --------------------------------------------------------

    parity = math_node(
        nodes,
        'MODULO',
        "Rosette Needle Parity",
        0.0,
        2.0,
    )
    parity.location = (4300, 4950)

    links.new(
        needle_index.outputs["Index"],
        parity.inputs[0],
    )

    parity_two = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Parity x2",
        0.0,
        2.0,
    )
    parity_two.location = (4500, 4950)

    links.new(
        parity.outputs[0],
        parity_two.inputs[0],
    )

    signed_parity = math_node(
        nodes,
        'SUBTRACT',
        "Rosette Signed Parity",
        0.0,
        1.0,
    )
    signed_parity.location = (4700, 4950)

    links.new(
        parity_two.outputs[0],
        signed_parity.inputs[0],
    )

    cone_degrees = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Cone Angle Degrees",
    )
    cone_degrees.location = (4900, 4950)

    links.new(
        signed_parity.outputs[0],
        cone_degrees.inputs[0],
    )
    links.new(
        group_in.outputs["Rosette Cone Angle"],
        cone_degrees.inputs[1],
    )

    cone_rad = math_node(
        nodes,
        'MULTIPLY',
        "Rosette Cone Angle Radians",
        0.0,
        math.pi / 180.0,
    )
    cone_rad.location = (5100, 4950)

    links.new(
        cone_degrees.outputs[0],
        cone_rad.inputs[0],
    )

    # --------------------------------------------------------
    # Needle transform
    # --------------------------------------------------------

    needle_euler = nodes.new("ShaderNodeCombineXYZ")
    needle_euler.location = (5300, 4850)
    needle_euler.label = "Rosette Needle Euler"

    links.new(
        cone_rad.outputs[0],
        needle_euler.inputs["Y"],
    )
    links.new(
        final_azimuth.outputs[0],
        needle_euler.inputs["Z"],
    )

    needle_rotation = nodes.new("FunctionNodeEulerToRotation")
    needle_rotation.location = (5500, 4850)
    needle_rotation.label = "Rosette Needle Rotation"

    links.new(
        needle_euler.outputs["Vector"],
        needle_rotation.inputs["Euler"],
    )

    needle_scale_xyz = nodes.new("ShaderNodeCombineXYZ")
    needle_scale_xyz.location = (5300, 4550)
    needle_scale_xyz.label = "Rosette Needle Length Scale"

    links.new(
        length_scale.outputs[0],
        needle_scale_xyz.inputs["X"],
    )
    needle_scale_xyz.inputs["Y"].default_value = 1.0
    needle_scale_xyz.inputs["Z"].default_value = 1.0

    needle_instances = nodes.new("GeometryNodeInstanceOnPoints")
    needle_instances.location = (5700, 5200)
    needle_instances.label = "Clocked Needle Whorls"

    links.new(
        place_needle_points.outputs["Geometry"],
        needle_instances.inputs["Points"],
    )
    links.new(
        needle_mesh.outputs["Mesh"],
        needle_instances.inputs["Instance"],
    )
    links.new(
        needle_rotation.outputs["Rotation"],
        needle_instances.inputs["Rotation"],
    )
    links.new(
        needle_scale_xyz.outputs["Vector"],
        needle_instances.inputs["Scale"],
    )

    # --------------------------------------------------------
    # Final rosette
    # --------------------------------------------------------

    rosette_join = nodes.new("GeometryNodeJoinGeometry")
    rosette_join.location = (5900, 5350)
    rosette_join.label = "Short Shoot + Clocked Needle Whorls"

    links.new(
        spur_mesh.outputs["Mesh"],
        rosette_join.inputs["Geometry"],
    )
    links.new(
        needle_instances.outputs["Instances"],
        rosette_join.inputs["Geometry"],
    )

    return rosette_join.outputs["Geometry"]


# ============================================================
# Secondary long-shoot diagnostic
# ============================================================


def build_foliage_branch(
    nodes, links, group_in, primary_mesh_socket, primary_curve_socket,
):
    """
    Furnish one primary branch with tamarack-style secondaries and foliage.

    v0.4a lifts the proven v0.3c branch/foliage system out of the
    side diagnostic and turns it into a reusable furnished branch
    archetype for the actual tree crown.

    Structural rules:

        - attachments follow the actual shaped primary curve
        - the primary is given a Z-Up frame
        - station spacing is lawful but slightly irregular
        - shoots are shorter near the primary root
        - several substantial shoots occur through the middle
        - shoots diminish again toward the primary tip
        - each shoot gets bounded deterministic length variation
        - shoot azimuths occupy a broad range around the primary
        - the population has a downward bias
        - longer shoots receive more downward bias
        - each shoot has a small amount of intrinsic sag

    Terminal foliage is now represented by clocked mini-whorl clusters.
    """

    # --------------------------------------------------------
    # Give the primary a stable frame for child attachment.
    #
    # Curve to Points builds Rotation from:
    #
    #     local X = curve normal
    #     local Y = curve binormal
    #     local Z = curve tangent
    #
    # Z-Up normal mode keeps the frame useful on our mostly
    # horizontal LOW primary:
    #
    #     local X ≈ horizontal lateral
    #     local Y ≈ vertical
    #     local Z ≈ along the primary
    # --------------------------------------------------------

    sec_normal = nodes.new("GeometryNodeSetCurveNormal")
    sec_normal.location = (2250, 3300)
    sec_normal.label = "Primary Z-Up Frame"

    # Blender 5.2 moved Set Curve Normal's mode from the old
    # node RNA property to a menu input socket.
    #
    # The menu is backed by rna_enum_curve_normal_mode_items,
    # whose identifier for Z-Up is Z_UP.
    sec_normal.inputs["Mode"].default_value = 'Z Up'

    links.new(primary_curve_socket, sec_normal.inputs["Curve"])

    # --------------------------------------------------------
    # Shared foliage primitive
    # --------------------------------------------------------

    foliage_rosette = build_rosette_primitive(
        nodes,
        links,
        group_in,
    )

    # ========================================================
    # PRIMARY foliage stations
    # ========================================================

    primary_fol_trim = nodes.new("GeometryNodeTrimCurve")
    primary_fol_trim.location = (2450, 3650)
    primary_fol_trim.label = "Primary Foliage Zone"
    primary_fol_trim.mode = 'FACTOR'

    links.new(
        sec_normal.outputs["Curve"],
        primary_fol_trim.inputs["Curve"],
    )
    links.new(
        group_in.outputs["Primary Foliage Start"],
        primary_fol_trim.inputs["Start"],
    )
    links.new(
        group_in.outputs["Primary Foliage End"],
        primary_fol_trim.inputs["End"],
    )

    primary_fol_points = nodes.new("GeometryNodeCurveToPoints")
    primary_fol_points.location = (2650, 3650)
    primary_fol_points.label = "Primary Foliage Stations"
    primary_fol_points.mode = 'COUNT'

    links.new(
        primary_fol_trim.outputs["Curve"],
        primary_fol_points.inputs["Curve"],
    )
    links.new(
        group_in.outputs["Primary Foliage Count"],
        primary_fol_points.inputs["Count"],
    )

    primary_fol_index = nodes.new("GeometryNodeInputIndex")
    primary_fol_index.location = (2650, 3450)
    primary_fol_index.label = "Primary Foliage Index"

    primary_fol_last = math_node(
        nodes,
        'SUBTRACT',
        "Last Primary Foliage Index",
        0.0,
        1.0,
    )
    primary_fol_last.location = (2850, 3375)

    links.new(
        group_in.outputs["Primary Foliage Count"],
        primary_fol_last.inputs[0],
    )

    primary_fol_factor = nodes.new("ShaderNodeMapRange")
    primary_fol_factor.location = (3050, 3450)
    primary_fol_factor.label = "Primary Foliage Position 0..1"
    primary_fol_factor.inputs["From Min"].default_value = 0.0
    primary_fol_factor.inputs["To Min"].default_value = 0.0
    primary_fol_factor.inputs["To Max"].default_value = 1.0

    links.new(
        primary_fol_index.outputs["Index"],
        primary_fol_factor.inputs["Value"],
    )
    links.new(
        primary_fol_last.outputs[0],
        primary_fol_factor.inputs["From Max"],
    )

    # Deterministic station key.
    primary_fol_seed = math_node(
        nodes,
        'MULTIPLY',
        "Primary Foliage Seed Offset",
        0.0,
        401.0,
    )
    primary_fol_seed.location = (2850, 3225)

    links.new(
        group_in.outputs["Seed"],
        primary_fol_seed.inputs[0],
    )

    primary_fol_key_base = math_node(
        nodes,
        'ADD',
        "Primary Foliage Index + Seed",
    )
    primary_fol_key_base.location = (3050, 3225)

    links.new(
        primary_fol_index.outputs["Index"],
        primary_fol_key_base.inputs[0],
    )
    links.new(
        primary_fol_seed.outputs[0],
        primary_fol_key_base.inputs[1],
    )

    primary_fol_key = math_node(
        nodes,
        'ADD',
        "Primary Foliage Key",
        0.0,
        59.0,
    )
    primary_fol_key.location = (3250, 3225)

    links.new(
        primary_fol_key_base.outputs[0],
        primary_fol_key.inputs[0],
    )

    primary_fol_hash = build_hash_01(
        nodes,
        links,
        primary_fol_key.outputs[0],
        "Primary Foliage Spacing",
        3450,
        3375,
        frequency=53.713,
        multiplier=21971.317,
        phase=11.53,
    )

    primary_fol_hash_two = math_node(
        nodes,
        'MULTIPLY',
        "Primary Foliage Hash x2",
        0.0,
        2.0,
    )
    primary_fol_hash_two.location = (4250, 3375)

    links.new(
        primary_fol_hash,
        primary_fol_hash_two.inputs[0],
    )

    primary_fol_signed = math_node(
        nodes,
        'SUBTRACT',
        "Signed Primary Foliage Hash",
        0.0,
        1.0,
    )
    primary_fol_signed.location = (4450, 3375)

    links.new(
        primary_fol_hash_two.outputs[0],
        primary_fol_signed.inputs[0],
    )

    # Nominal spacing in metres.
    primary_fol_usable_fraction = math_node(
        nodes,
        'SUBTRACT',
        "Primary Foliage Usable Fraction",
    )
    primary_fol_usable_fraction.location = (3450, 3175)

    links.new(
        group_in.outputs["Primary Foliage End"],
        primary_fol_usable_fraction.inputs[0],
    )
    links.new(
        group_in.outputs["Primary Foliage Start"],
        primary_fol_usable_fraction.inputs[1],
    )

    primary_fol_usable_length = math_node(
        nodes,
        'MULTIPLY',
        "Primary Foliage Usable Length",
    )
    primary_fol_usable_length.location = (3650, 3175)

    links.new(
        group_in.outputs["Primary Length"],
        primary_fol_usable_length.inputs[0],
    )
    links.new(
        primary_fol_usable_fraction.outputs[0],
        primary_fol_usable_length.inputs[1],
    )

    primary_fol_spacing = math_node(
        nodes,
        'DIVIDE',
        "Nominal Primary Foliage Spacing",
    )
    primary_fol_spacing.location = (3850, 3175)

    links.new(
        primary_fol_usable_length.outputs[0],
        primary_fol_spacing.inputs[0],
    )
    links.new(
        primary_fol_last.outputs[0],
        primary_fol_spacing.inputs[1],
    )

    primary_fol_jitter_limit = math_node(
        nodes,
        'MULTIPLY',
        "Primary Foliage Jitter Limit",
    )
    primary_fol_jitter_limit.location = (4050, 3175)

    links.new(
        primary_fol_spacing.outputs[0],
        primary_fol_jitter_limit.inputs[0],
    )
    links.new(
        group_in.outputs["Foliage Spacing Variation"],
        primary_fol_jitter_limit.inputs[1],
    )

    # Endpoint weighting: 4*t*(1-t)
    primary_fol_one_minus = math_node(
        nodes,
        'SUBTRACT',
        "1 - Primary Foliage Factor",
        1.0,
        0.0,
    )
    primary_fol_one_minus.location = (3450, 2975)

    links.new(
        primary_fol_factor.outputs["Result"],
        primary_fol_one_minus.inputs[1],
    )

    primary_fol_endpoint_product = math_node(
        nodes,
        'MULTIPLY',
        "Primary Foliage Endpoint Product",
    )
    primary_fol_endpoint_product.location = (3650, 2975)

    links.new(
        primary_fol_factor.outputs["Result"],
        primary_fol_endpoint_product.inputs[0],
    )
    links.new(
        primary_fol_one_minus.outputs[0],
        primary_fol_endpoint_product.inputs[1],
    )

    primary_fol_endpoint_weight = math_node(
        nodes,
        'MULTIPLY',
        "Primary Foliage Endpoint Weight x4",
        0.0,
        4.0,
    )
    primary_fol_endpoint_weight.location = (3850, 2975)

    links.new(
        primary_fol_endpoint_product.outputs[0],
        primary_fol_endpoint_weight.inputs[0],
    )

    primary_fol_jitter_signed = math_node(
        nodes,
        'MULTIPLY',
        "Primary Foliage Signed Jitter",
    )
    primary_fol_jitter_signed.location = (4650, 3275)

    links.new(
        primary_fol_signed.outputs[0],
        primary_fol_jitter_signed.inputs[0],
    )
    links.new(
        primary_fol_jitter_limit.outputs[0],
        primary_fol_jitter_signed.inputs[1],
    )

    primary_fol_jitter = math_node(
        nodes,
        'MULTIPLY',
        "Primary Foliage Endpoint-Pinned Jitter",
    )
    primary_fol_jitter.location = (4850, 3275)

    links.new(
        primary_fol_jitter_signed.outputs[0],
        primary_fol_jitter.inputs[0],
    )
    links.new(
        primary_fol_endpoint_weight.outputs[0],
        primary_fol_jitter.inputs[1],
    )

    primary_fol_tangent_offset = nodes.new("ShaderNodeVectorMath")
    primary_fol_tangent_offset.operation = 'SCALE'
    primary_fol_tangent_offset.location = (5050, 3275)
    primary_fol_tangent_offset.label = "Jitter Primary Foliage Along Tangent"

    links.new(
        primary_fol_points.outputs["Tangent"],
        primary_fol_tangent_offset.inputs["Vector"],
    )
    links.new(
        primary_fol_jitter.outputs[0],
        primary_fol_tangent_offset.inputs["Scale"],
    )

    primary_fol_jittered = nodes.new("GeometryNodeSetPosition")
    primary_fol_jittered.location = (5250, 3650)
    primary_fol_jittered.label = "Irregular Primary Foliage Stations"

    links.new(
        primary_fol_points.outputs["Points"],
        primary_fol_jittered.inputs["Geometry"],
    )
    links.new(
        primary_fol_tangent_offset.outputs["Vector"],
        primary_fol_jittered.inputs["Offset"],
    )

    primary_fol_instances = nodes.new("GeometryNodeInstanceOnPoints")
    primary_fol_instances.location = (5450, 3650)
    primary_fol_instances.label = "Primary Needle Rosettes"

    links.new(
        primary_fol_jittered.outputs["Geometry"],
        primary_fol_instances.inputs["Points"],
    )
    links.new(
        foliage_rosette,
        primary_fol_instances.inputs["Instance"],
    )
    links.new(
        primary_fol_points.outputs["Rotation"],
        primary_fol_instances.inputs["Rotation"],
    )

    # --------------------------------------------------------
    # Trim usable secondary-bearing portion of the primary
    # --------------------------------------------------------

    sec_trim = nodes.new("GeometryNodeTrimCurve")
    sec_trim.location = (2450, 3300)
    sec_trim.label = "Secondary Bearing Zone"
    sec_trim.mode = 'FACTOR'
    links.new(sec_normal.outputs["Curve"], sec_trim.inputs["Curve"])
    links.new(group_in.outputs["Secondary Start"], sec_trim.inputs["Start"])
    links.new(group_in.outputs["Secondary End"], sec_trim.inputs["End"])

    sec_points = nodes.new("GeometryNodeCurveToPoints")
    sec_points.location = (2650, 3300)
    sec_points.label = "Secondary Stations"
    sec_points.mode = 'COUNT'
    links.new(sec_trim.outputs["Curve"], sec_points.inputs["Curve"])
    links.new(group_in.outputs["Secondary Count"], sec_points.inputs["Count"])

    sec_index = nodes.new("GeometryNodeInputIndex")
    sec_index.location = (2650, 3000)
    sec_index.label = "Secondary Index"

    # --------------------------------------------------------
    # Normalized station factor 0..1
    # --------------------------------------------------------

    sec_last = math_node(
        nodes, 'SUBTRACT', "Last Secondary Index", 0.0, 1.0,
    )
    sec_last.location = (2850, 2875)
    links.new(group_in.outputs["Secondary Count"], sec_last.inputs[0])

    sec_factor = nodes.new("ShaderNodeMapRange")
    sec_factor.location = (3050, 2975)
    sec_factor.label = "Secondary Position 0..1"
    sec_factor.inputs["From Min"].default_value = 0.0
    sec_factor.inputs["To Min"].default_value = 0.0
    sec_factor.inputs["To Max"].default_value = 1.0
    links.new(sec_index.outputs["Index"], sec_factor.inputs["Value"])
    links.new(sec_last.outputs[0], sec_factor.inputs["From Max"])

    # --------------------------------------------------------
    # Deterministic station key
    # --------------------------------------------------------

    sec_seed_offset = math_node(
        nodes, 'MULTIPLY', "Secondary Seed Offset", 0.0, 211.0,
    )
    sec_seed_offset.location = (2850, 2675)
    links.new(group_in.outputs["Seed"], sec_seed_offset.inputs[0])

    sec_key_base = math_node(
        nodes, 'ADD', "Secondary Index + Seed",
    )
    sec_key_base.location = (3050, 2675)
    links.new(sec_index.outputs["Index"], sec_key_base.inputs[0])
    links.new(sec_seed_offset.outputs[0], sec_key_base.inputs[1])

    sec_key = math_node(
        nodes, 'ADD', "Secondary Variation Key", 0.0, 31.0,
    )
    sec_key.location = (3250, 2675)
    links.new(sec_key_base.outputs[0], sec_key.inputs[0])

    # ========================================================
    # Station-spacing variation
    # ========================================================
    #
    # Jitter is measured as a fraction of nominal spacing.
    # The endpoint weighting 4*t*(1-t) pins the first and last
    # stations while allowing the middle stations to wander.
    # ========================================================

    spacing_hash = build_hash_01(
        nodes, links, sec_key.outputs[0],
        "Secondary Spacing", 3450, 2575,
        frequency=29.157,
        multiplier=31821.413,
        phase=7.31,
    )

    spacing_hash_two = math_node(
        nodes, 'MULTIPLY', "Secondary Spacing Hash x2", 0.0, 2.0,
    )
    spacing_hash_two.location = (4250, 2575)
    links.new(spacing_hash, spacing_hash_two.inputs[0])

    spacing_signed = math_node(
        nodes, 'SUBTRACT', "Signed Secondary Spacing Hash", 0.0, 1.0,
    )
    spacing_signed.location = (4450, 2575)
    links.new(spacing_hash_two.outputs[0], spacing_signed.inputs[0])

    usable_fraction = math_node(
        nodes, 'SUBTRACT', "Secondary Usable Fraction",
    )
    usable_fraction.location = (3450, 2375)
    links.new(group_in.outputs["Secondary End"], usable_fraction.inputs[0])
    links.new(group_in.outputs["Secondary Start"], usable_fraction.inputs[1])

    usable_length = math_node(
        nodes, 'MULTIPLY', "Secondary Usable Length",
    )
    usable_length.location = (3650, 2375)
    links.new(group_in.outputs["Primary Length"], usable_length.inputs[0])
    links.new(usable_fraction.outputs[0], usable_length.inputs[1])

    nominal_spacing = math_node(
        nodes, 'DIVIDE', "Nominal Secondary Spacing",
    )
    nominal_spacing.location = (3850, 2375)
    links.new(usable_length.outputs[0], nominal_spacing.inputs[0])
    links.new(sec_last.outputs[0], nominal_spacing.inputs[1])

    jitter_limit = math_node(
        nodes, 'MULTIPLY', "Secondary Jitter Limit",
    )
    jitter_limit.location = (4050, 2375)
    links.new(nominal_spacing.outputs[0], jitter_limit.inputs[0])
    links.new(group_in.outputs["Secondary Spacing Variation"], jitter_limit.inputs[1])

    one_minus_sec = math_node(
        nodes, 'SUBTRACT', "1 - Secondary Factor", 1.0, 0.0,
    )
    one_minus_sec.location = (3450, 2175)
    links.new(sec_factor.outputs["Result"], one_minus_sec.inputs[1])

    endpoint_product = math_node(
        nodes, 'MULTIPLY', "Secondary Endpoint Product",
    )
    endpoint_product.location = (3650, 2175)
    links.new(sec_factor.outputs["Result"], endpoint_product.inputs[0])
    links.new(one_minus_sec.outputs[0], endpoint_product.inputs[1])

    endpoint_weight = math_node(
        nodes, 'MULTIPLY', "Secondary Endpoint Weight x4", 0.0, 4.0,
    )
    endpoint_weight.location = (3850, 2175)
    links.new(endpoint_product.outputs[0], endpoint_weight.inputs[0])

    jitter_signed = math_node(
        nodes, 'MULTIPLY', "Secondary Signed Jitter",
    )
    jitter_signed.location = (4650, 2475)
    links.new(spacing_signed.outputs[0], jitter_signed.inputs[0])
    links.new(jitter_limit.outputs[0], jitter_signed.inputs[1])

    jitter_distance = math_node(
        nodes, 'MULTIPLY', "Secondary Endpoint-Pinned Jitter",
    )
    jitter_distance.location = (4850, 2475)
    links.new(jitter_signed.outputs[0], jitter_distance.inputs[0])
    links.new(endpoint_weight.outputs[0], jitter_distance.inputs[1])

    tangent_offset = nodes.new("ShaderNodeVectorMath")
    tangent_offset.operation = 'SCALE'
    tangent_offset.location = (5050, 2475)
    tangent_offset.label = "Jitter Along Primary Tangent"
    links.new(sec_points.outputs["Tangent"], tangent_offset.inputs["Vector"])
    links.new(jitter_distance.outputs[0], tangent_offset.inputs["Scale"])

    jittered_points = nodes.new("GeometryNodeSetPosition")
    jittered_points.location = (5250, 3300)
    jittered_points.label = "Irregular Secondary Stations"
    links.new(sec_points.outputs["Points"], jittered_points.inputs["Geometry"])
    links.new(tangent_offset.outputs["Vector"], jittered_points.inputs["Offset"])

    # ========================================================
    # Asymmetric secondary-length envelope
    # ========================================================
    #
    #   usable-zone root  -> 0.35
    #   factor 0.58       -> 1.00
    #   usable-zone tip   -> 0.25
    #
    # This is intentionally not a symmetric bell.
    # ========================================================

    sec_lower = nodes.new("ShaderNodeMapRange")
    sec_lower.location = (3450, 3200)
    sec_lower.label = "Secondary Lower Envelope"
    sec_lower.inputs["From Min"].default_value = 0.0
    sec_lower.inputs["From Max"].default_value = 0.58
    sec_lower.inputs["To Min"].default_value = 0.50
    sec_lower.inputs["To Max"].default_value = 1.0
    links.new(sec_factor.outputs["Result"], sec_lower.inputs["Value"])

    sec_upper = nodes.new("ShaderNodeMapRange")
    sec_upper.location = (3450, 3000)
    sec_upper.label = "Secondary Upper Envelope"
    sec_upper.inputs["From Min"].default_value = 0.58
    sec_upper.inputs["From Max"].default_value = 1.0
    sec_upper.inputs["To Min"].default_value = 1.0
    sec_upper.inputs["To Max"].default_value = 0.40
    links.new(sec_factor.outputs["Result"], sec_upper.inputs["Value"])

    sec_envelope = math_node(
        nodes, 'MINIMUM', "Secondary Length Envelope",
    )
    sec_envelope.location = (3650, 3100)
    links.new(sec_lower.outputs["Result"], sec_envelope.inputs[0])
    links.new(sec_upper.outputs["Result"], sec_envelope.inputs[1])

    # --------------------------------------------------------
    # Bounded individual secondary-length variation
    # --------------------------------------------------------

    length_hash = build_hash_01(
        nodes, links, sec_key.outputs[0],
        "Secondary Length", 3850, 3500,
        frequency=41.731,
        multiplier=27183.193,
        phase=19.17,
    )

    sec_min_scale = math_node(
        nodes, 'SUBTRACT', "Minimum Secondary Length Scale", 1.0, 0.0,
    )
    sec_min_scale.location = (4650, 3500)
    links.new(group_in.outputs["Secondary Length Variation"], sec_min_scale.inputs[1])

    sec_var_span = math_node(
        nodes, 'MULTIPLY', "Secondary Length Variation Span", 0.0, 2.0,
    )
    sec_var_span.location = (4650, 3350)
    links.new(group_in.outputs["Secondary Length Variation"], sec_var_span.inputs[0])

    sec_random_part = math_node(
        nodes, 'MULTIPLY', "Secondary Random Length Offset",
    )
    sec_random_part.location = (4850, 3450)
    links.new(length_hash, sec_random_part.inputs[0])
    links.new(sec_var_span.outputs[0], sec_random_part.inputs[1])

    sec_random_scale = math_node(
        nodes, 'ADD', "Secondary Random Length Scale",
    )
    sec_random_scale.location = (5050, 3450)
    links.new(sec_min_scale.outputs[0], sec_random_scale.inputs[0])
    links.new(sec_random_part.outputs[0], sec_random_scale.inputs[1])

    sec_final_scale = math_node(
        nodes, 'MULTIPLY', "Final Secondary Length Scale",
    )
    sec_final_scale.location = (5250, 3450)
    links.new(sec_envelope.outputs[0], sec_final_scale.inputs[0])
    links.new(sec_random_scale.outputs[0], sec_final_scale.inputs[1])

    sec_scale_vector = nodes.new("ShaderNodeCombineXYZ")
    sec_scale_vector.location = (5450, 3450)
    sec_scale_vector.label = "Secondary Uniform Scale"
    links.new(sec_final_scale.outputs[0], sec_scale_vector.inputs["X"])
    links.new(sec_final_scale.outputs[0], sec_scale_vector.inputs["Y"])
    links.new(sec_final_scale.outputs[0], sec_scale_vector.inputs["Z"])

    # ========================================================
    # Secondary azimuth and droop
    # ========================================================
    #
    # The primitive points along local +X.
    #
    # Rotation around local Z (the primary tangent) selects where
    # around the primary the shoot departs.
    #
    # angle =
    #
    #     signed_hash * Secondary Azimuth Spread
    #     - (
    #         Secondary Base Droop
    #         + final_length_scale * Secondary Long Shoot Droop
    #       )
    #
    # Short shoots therefore have relatively free orientation.
    # Long shoots are progressively biased into the lower half.
    # ========================================================

    azimuth_hash = build_hash_01(
        nodes, links, sec_key.outputs[0],
        "Secondary Azimuth", 3850, 3850,
        frequency=73.417,
        multiplier=15731.743,
        phase=43.9,
    )

    azimuth_two = math_node(
        nodes, 'MULTIPLY', "Secondary Azimuth Hash x2", 0.0, 2.0,
    )
    azimuth_two.location = (4650, 3850)
    links.new(azimuth_hash, azimuth_two.inputs[0])

    azimuth_signed = math_node(
        nodes, 'SUBTRACT', "Signed Secondary Azimuth Hash", 0.0, 1.0,
    )
    azimuth_signed.location = (4850, 3850)
    links.new(azimuth_two.outputs[0], azimuth_signed.inputs[0])

    azimuth_spread = math_node(
        nodes, 'MULTIPLY', "Secondary Azimuth Spread",
    )
    azimuth_spread.location = (5050, 3850)
    links.new(azimuth_signed.outputs[0], azimuth_spread.inputs[0])
    links.new(group_in.outputs["Secondary Azimuth Spread"], azimuth_spread.inputs[1])

    long_droop = math_node(
        nodes, 'MULTIPLY', "Length-Dependent Secondary Droop",
    )
    long_droop.location = (5050, 3700)
    links.new(sec_final_scale.outputs[0], long_droop.inputs[0])
    links.new(group_in.outputs["Secondary Long Shoot Droop"], long_droop.inputs[1])

    total_droop = math_node(
        nodes, 'ADD', "Total Secondary Droop",
    )
    total_droop.location = (5250, 3700)
    links.new(group_in.outputs["Secondary Base Droop"], total_droop.inputs[0])
    links.new(long_droop.outputs[0], total_droop.inputs[1])

    sec_angle_deg = math_node(
        nodes, 'SUBTRACT', "Secondary Departure Angle Degrees",
    )
    sec_angle_deg.location = (5450, 3800)
    links.new(azimuth_spread.outputs[0], sec_angle_deg.inputs[0])
    links.new(total_droop.outputs[0], sec_angle_deg.inputs[1])

    sec_angle_rad = math_node(
        nodes, 'MULTIPLY', "Secondary Departure Angle Radians",
        0.0, math.pi / 180.0,
    )
    sec_angle_rad.location = (5650, 3800)
    links.new(sec_angle_deg.outputs[0], sec_angle_rad.inputs[0])

    sec_euler = nodes.new("ShaderNodeCombineXYZ")
    sec_euler.location = (5850, 3800)
    sec_euler.label = "Secondary Local-Z Euler"
    links.new(sec_angle_rad.outputs[0], sec_euler.inputs["Z"])

    sec_rotation = nodes.new("FunctionNodeEulerToRotation")
    sec_rotation.location = (6050, 3800)
    sec_rotation.label = "Secondary Local-Z Rotation"
    links.new(sec_euler.outputs["Vector"], sec_rotation.inputs["Euler"])

    # ========================================================
    # Secondary long-shoot primitive
    # ========================================================
    #
    # Local frame:
    #
    #     +X = outward from primary
    #     +Y = nominal vertical
    #     +Z = forward along primary
    #
    # The primitive includes a mild sag.  Its major departure
    # orientation is supplied later by local-Z rotation.
    # ========================================================

    sec_forward = math_node(
        nodes, 'MULTIPLY', "Secondary Forward Distance",
    )
    sec_forward.location = (2650, 4200)
    links.new(group_in.outputs["Secondary Max Length"], sec_forward.inputs[0])
    links.new(group_in.outputs["Secondary Forward Sweep"], sec_forward.inputs[1])

    sec_end = nodes.new("ShaderNodeCombineXYZ")
    sec_end.location = (2850, 4200)
    sec_end.label = "Secondary Long-Shoot End"
    links.new(group_in.outputs["Secondary Max Length"], sec_end.inputs["X"])
    links.new(sec_forward.outputs[0], sec_end.inputs["Z"])

    sec_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    sec_line.location = (3050, 4200)
    sec_line.label = "Secondary Long Shoot"
    sec_line.inputs["Start"].default_value = (0.0, 0.0, 0.0)
    links.new(sec_end.outputs["Vector"], sec_line.inputs["End"])

    sec_resample = nodes.new("GeometryNodeResampleCurve")
    sec_resample.location = (3250, 4200)
    sec_resample.label = "Secondary Segments"
    sec_resample.inputs["Mode"].default_value = 'Count'
    sec_resample.inputs["Count"].default_value = 6
    links.new(sec_line.outputs["Curve"], sec_resample.inputs["Curve"])

    sec_spline_factor = nodes.new("GeometryNodeSplineParameter")
    sec_spline_factor.location = (3250, 4000)
    sec_spline_factor.label = "Secondary Factor"

    sec_one_minus = math_node(
        nodes, 'SUBTRACT', "1 - Secondary Spline Factor", 1.0, 0.0,
    )
    sec_one_minus.location = (3450, 4000)
    links.new(sec_spline_factor.outputs["Factor"], sec_one_minus.inputs[1])

    sec_sag_product = math_node(
        nodes, 'MULTIPLY', "Secondary Sag Product",
    )
    sec_sag_product.location = (3650, 4000)
    links.new(sec_spline_factor.outputs["Factor"], sec_sag_product.inputs[0])
    links.new(sec_one_minus.outputs[0], sec_sag_product.inputs[1])

    sec_sag_four = math_node(
        nodes, 'MULTIPLY', "Secondary Sag x4", 0.0, 4.0,
    )
    sec_sag_four.location = (3850, 4000)
    links.new(sec_sag_product.outputs[0], sec_sag_four.inputs[0])

    sec_sag_amount = math_node(
        nodes, 'MULTIPLY', "Apply Secondary Sag",
    )
    sec_sag_amount.location = (4050, 4000)
    links.new(sec_sag_four.outputs[0], sec_sag_amount.inputs[0])
    links.new(group_in.outputs["Secondary Sag"], sec_sag_amount.inputs[1])

    sec_sag_down = math_node(
        nodes, 'MULTIPLY', "Secondary Sag Down", 0.0, -1.0,
    )
    sec_sag_down.location = (4250, 4000)
    links.new(sec_sag_amount.outputs[0], sec_sag_down.inputs[0])

    sec_offset = nodes.new("ShaderNodeCombineXYZ")
    sec_offset.location = (4450, 4000)
    sec_offset.label = "Secondary Sag Offset"
    links.new(sec_sag_down.outputs[0], sec_offset.inputs["Y"])

    sec_set_position = nodes.new("GeometryNodeSetPosition")
    sec_set_position.location = (4650, 4200)
    sec_set_position.label = "Sagged Secondary Long Shoot"
    links.new(sec_resample.outputs["Curve"], sec_set_position.inputs["Geometry"])
    links.new(sec_offset.outputs["Vector"], sec_set_position.inputs["Offset"])

    sec_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    sec_profile.location = (4650, 4000)
    sec_profile.label = "Secondary Profile"
    sec_profile.inputs["Resolution"].default_value = 3
    links.new(group_in.outputs["Secondary Radius"], sec_profile.inputs["Radius"])

    sec_taper = nodes.new("ShaderNodeMapRange")
    sec_taper.location = (4850, 4000)
    sec_taper.label = "Secondary Taper"
    sec_taper.inputs["From Min"].default_value = 0.0
    sec_taper.inputs["From Max"].default_value = 1.0
    sec_taper.inputs["To Min"].default_value = 1.0
    sec_taper.inputs["To Max"].default_value = 0.12
    links.new(sec_spline_factor.outputs["Factor"], sec_taper.inputs["Value"])

    sec_mesh = nodes.new("GeometryNodeCurveToMesh")
    sec_mesh.location = (5050, 4200)
    sec_mesh.label = "Secondary Mesh"
    links.new(sec_set_position.outputs["Geometry"], sec_mesh.inputs["Curve"])
    links.new(sec_profile.outputs["Curve"], sec_mesh.inputs["Profile Curve"])
    links.new(sec_taper.outputs["Result"], sec_mesh.inputs["Scale"])
    if "Fill Caps" in sec_mesh.inputs:
        sec_mesh.inputs["Fill Caps"].default_value = True

    # --------------------------------------------------------
    # A) WOODY secondaries
    #
    # Only wood receives the individual secondary scale.
    # --------------------------------------------------------

    sec_instances = nodes.new("GeometryNodeInstanceOnPoints")
    sec_instances.location = (6250, 3300)
    sec_instances.label = "Secondary Long Shoots"

    links.new(
        jittered_points.outputs["Geometry"],
        sec_instances.inputs["Points"],
    )
    links.new(
        sec_mesh.outputs["Mesh"],
        sec_instances.inputs["Instance"],
    )
    links.new(
        sec_points.outputs["Rotation"],
        sec_instances.inputs["Rotation"],
    )
    links.new(
        sec_scale_vector.outputs["Vector"],
        sec_instances.inputs["Scale"],
    )

    rotate_secondaries = nodes.new("GeometryNodeRotateInstances")
    rotate_secondaries.location = (6450, 3300)
    rotate_secondaries.label = "Distribute Secondary Shoots Around Primary"

    links.new(
        sec_instances.outputs["Instances"],
        rotate_secondaries.inputs["Instances"],
    )
    links.new(
        sec_rotation.outputs["Rotation"],
        rotate_secondaries.inputs["Rotation"],
    )

    if "Local Space" in rotate_secondaries.inputs:
        rotate_secondaries.inputs["Local Space"].default_value = True

    # --------------------------------------------------------
    # B) MATCHING transformed secondary CURVES
    #
    # These receive exactly the same position, scale and rotation
    # as the woody shoots, but remain curves until realization.
    #
    # Foliage stations are generated only after realization, so
    # rosette SIZE does not inherit secondary-shoot scale.
    # --------------------------------------------------------

    sec_curve_instances = nodes.new("GeometryNodeInstanceOnPoints")
    sec_curve_instances.location = (6250, 4650)
    sec_curve_instances.label = "Secondary Curves for Foliage"

    links.new(
        jittered_points.outputs["Geometry"],
        sec_curve_instances.inputs["Points"],
    )
    links.new(
        sec_set_position.outputs["Geometry"],
        sec_curve_instances.inputs["Instance"],
    )
    links.new(
        sec_points.outputs["Rotation"],
        sec_curve_instances.inputs["Rotation"],
    )
    links.new(
        sec_scale_vector.outputs["Vector"],
        sec_curve_instances.inputs["Scale"],
    )

    rotate_sec_curves = nodes.new("GeometryNodeRotateInstances")
    rotate_sec_curves.location = (6450, 4650)
    rotate_sec_curves.label = "Rotate Secondary Foliage Curves"

    links.new(
        sec_curve_instances.outputs["Instances"],
        rotate_sec_curves.inputs["Instances"],
    )
    links.new(
        sec_rotation.outputs["Rotation"],
        rotate_sec_curves.inputs["Rotation"],
    )

    if "Local Space" in rotate_sec_curves.inputs:
        rotate_sec_curves.inputs["Local Space"].default_value = True

    realize_sec_curves = nodes.new("GeometryNodeRealizeInstances")
    realize_sec_curves.location = (6650, 4650)
    realize_sec_curves.label = "Realize Secondary Foliage Curves"

    links.new(
        rotate_sec_curves.outputs["Instances"],
        realize_sec_curves.inputs["Geometry"],
    )

    # Give the realized curves a stable normal frame.  Exact twist
    # is visually unimportant because the rosette is radially symmetric.
    sec_fol_normal = nodes.new("GeometryNodeSetCurveNormal")
    sec_fol_normal.location = (6850, 4650)
    sec_fol_normal.label = "Secondary Foliage Curve Frame"
    sec_fol_normal.inputs["Mode"].default_value = 'Minimum Twist'

    links.new(
        realize_sec_curves.outputs["Geometry"],
        sec_fol_normal.inputs["Curve"],
    )

    # --------------------------------------------------------
    # Secondary foliage-bearing zone
    # --------------------------------------------------------

    secondary_fol_trim = nodes.new("GeometryNodeTrimCurve")
    secondary_fol_trim.location = (7050, 4650)
    secondary_fol_trim.label = "Secondary Foliage Zone"
    secondary_fol_trim.mode = 'FACTOR'

    links.new(
        sec_fol_normal.outputs["Curve"],
        secondary_fol_trim.inputs["Curve"],
    )
    links.new(
        group_in.outputs["Secondary Foliage Start"],
        secondary_fol_trim.inputs["Start"],
    )
    links.new(
        group_in.outputs["Secondary Foliage End"],
        secondary_fol_trim.inputs["End"],
    )

    secondary_fol_points = nodes.new("GeometryNodeCurveToPoints")
    secondary_fol_points.location = (7250, 4650)
    secondary_fol_points.label = "Secondary Foliage Stations"
    secondary_fol_points.mode = 'COUNT'

    links.new(
        secondary_fol_trim.outputs["Curve"],
        secondary_fol_points.inputs["Curve"],
    )
    links.new(
        group_in.outputs["Secondary Foliage Count"],
        secondary_fol_points.inputs["Count"],
    )

    # --------------------------------------------------------
    # Local station index within every secondary spline:
    #
    #     global point index MOD station count
    #
    # This lets endpoint weighting restart on each secondary.
    # --------------------------------------------------------

    secondary_fol_index = nodes.new("GeometryNodeInputIndex")
    secondary_fol_index.location = (7250, 4400)
    secondary_fol_index.label = "Global Secondary Foliage Index"

    secondary_local_index = math_node(
        nodes,
        'MODULO',
        "Local Secondary Foliage Index",
        0.0,
        9.0,
    )
    secondary_local_index.location = (7450, 4400)

    links.new(
        secondary_fol_index.outputs["Index"],
        secondary_local_index.inputs[0],
    )
    links.new(
        group_in.outputs["Secondary Foliage Count"],
        secondary_local_index.inputs[1],
    )

    secondary_fol_last = math_node(
        nodes,
        'SUBTRACT',
        "Last Secondary Foliage Index",
        0.0,
        1.0,
    )
    secondary_fol_last.location = (7450, 4200)

    links.new(
        group_in.outputs["Secondary Foliage Count"],
        secondary_fol_last.inputs[0],
    )

    secondary_fol_factor = nodes.new("ShaderNodeMapRange")
    secondary_fol_factor.location = (7650, 4400)
    secondary_fol_factor.label = "Secondary Foliage Position 0..1"
    secondary_fol_factor.inputs["From Min"].default_value = 0.0
    secondary_fol_factor.inputs["To Min"].default_value = 0.0
    secondary_fol_factor.inputs["To Max"].default_value = 1.0

    links.new(
        secondary_local_index.outputs[0],
        secondary_fol_factor.inputs["Value"],
    )
    links.new(
        secondary_fol_last.outputs[0],
        secondary_fol_factor.inputs["From Max"],
    )

    # --------------------------------------------------------
    # Deterministic global station jitter
    # --------------------------------------------------------

    secondary_fol_seed = math_node(
        nodes,
        'MULTIPLY',
        "Secondary Foliage Seed Offset",
        0.0,
        503.0,
    )
    secondary_fol_seed.location = (7450, 4000)

    links.new(
        group_in.outputs["Seed"],
        secondary_fol_seed.inputs[0],
    )

    secondary_fol_key_base = math_node(
        nodes,
        'ADD',
        "Secondary Foliage Index + Seed",
    )
    secondary_fol_key_base.location = (7650, 4000)

    links.new(
        secondary_fol_index.outputs["Index"],
        secondary_fol_key_base.inputs[0],
    )
    links.new(
        secondary_fol_seed.outputs[0],
        secondary_fol_key_base.inputs[1],
    )

    secondary_fol_key = math_node(
        nodes,
        'ADD',
        "Secondary Foliage Key",
        0.0,
        83.0,
    )
    secondary_fol_key.location = (7850, 4000)

    links.new(
        secondary_fol_key_base.outputs[0],
        secondary_fol_key.inputs[0],
    )

    secondary_fol_hash = build_hash_01(
        nodes,
        links,
        secondary_fol_key.outputs[0],
        "Secondary Foliage Spacing",
        8050,
        4100,
        frequency=67.193,
        multiplier=17681.953,
        phase=23.71,
    )

    secondary_fol_hash_two = math_node(
        nodes,
        'MULTIPLY',
        "Secondary Foliage Hash x2",
        0.0,
        2.0,
    )
    secondary_fol_hash_two.location = (8850, 4100)

    links.new(
        secondary_fol_hash,
        secondary_fol_hash_two.inputs[0],
    )

    secondary_fol_signed = math_node(
        nodes,
        'SUBTRACT',
        "Signed Secondary Foliage Hash",
        0.0,
        1.0,
    )
    secondary_fol_signed.location = (9050, 4100)

    links.new(
        secondary_fol_hash_two.outputs[0],
        secondary_fol_signed.inputs[0],
    )

    # Nominal maximum spacing.  Actual short secondaries already
    # receive closer stations from Curve to Points COUNT mode.
    secondary_fol_spacing = math_node(
        nodes,
        'DIVIDE',
        "Nominal Secondary Foliage Spacing",
    )
    secondary_fol_spacing.location = (8050, 3900)

    links.new(
        group_in.outputs["Secondary Max Length"],
        secondary_fol_spacing.inputs[0],
    )
    links.new(
        secondary_fol_last.outputs[0],
        secondary_fol_spacing.inputs[1],
    )

    secondary_fol_jitter_limit = math_node(
        nodes,
        'MULTIPLY',
        "Secondary Foliage Jitter Limit",
    )
    secondary_fol_jitter_limit.location = (8250, 3900)

    links.new(
        secondary_fol_spacing.outputs[0],
        secondary_fol_jitter_limit.inputs[0],
    )
    links.new(
        group_in.outputs["Foliage Spacing Variation"],
        secondary_fol_jitter_limit.inputs[1],
    )

    secondary_fol_one_minus = math_node(
        nodes,
        'SUBTRACT',
        "1 - Secondary Foliage Factor",
        1.0,
        0.0,
    )
    secondary_fol_one_minus.location = (8050, 3700)

    links.new(
        secondary_fol_factor.outputs["Result"],
        secondary_fol_one_minus.inputs[1],
    )

    secondary_fol_endpoint_product = math_node(
        nodes,
        'MULTIPLY',
        "Secondary Foliage Endpoint Product",
    )
    secondary_fol_endpoint_product.location = (8250, 3700)

    links.new(
        secondary_fol_factor.outputs["Result"],
        secondary_fol_endpoint_product.inputs[0],
    )
    links.new(
        secondary_fol_one_minus.outputs[0],
        secondary_fol_endpoint_product.inputs[1],
    )

    secondary_fol_endpoint_weight = math_node(
        nodes,
        'MULTIPLY',
        "Secondary Foliage Endpoint Weight x4",
        0.0,
        4.0,
    )
    secondary_fol_endpoint_weight.location = (8450, 3700)

    links.new(
        secondary_fol_endpoint_product.outputs[0],
        secondary_fol_endpoint_weight.inputs[0],
    )

    secondary_fol_jitter_signed = math_node(
        nodes,
        'MULTIPLY',
        "Secondary Foliage Signed Jitter",
    )
    secondary_fol_jitter_signed.location = (9250, 4000)

    links.new(
        secondary_fol_signed.outputs[0],
        secondary_fol_jitter_signed.inputs[0],
    )
    links.new(
        secondary_fol_jitter_limit.outputs[0],
        secondary_fol_jitter_signed.inputs[1],
    )

    secondary_fol_jitter = math_node(
        nodes,
        'MULTIPLY',
        "Secondary Foliage Endpoint-Pinned Jitter",
    )
    secondary_fol_jitter.location = (9450, 4000)

    links.new(
        secondary_fol_jitter_signed.outputs[0],
        secondary_fol_jitter.inputs[0],
    )
    links.new(
        secondary_fol_endpoint_weight.outputs[0],
        secondary_fol_jitter.inputs[1],
    )

    secondary_fol_tangent_offset = nodes.new("ShaderNodeVectorMath")
    secondary_fol_tangent_offset.operation = 'SCALE'
    secondary_fol_tangent_offset.location = (9650, 4000)
    secondary_fol_tangent_offset.label = "Jitter Secondary Foliage Along Tangent"

    links.new(
        secondary_fol_points.outputs["Tangent"],
        secondary_fol_tangent_offset.inputs["Vector"],
    )
    links.new(
        secondary_fol_jitter.outputs[0],
        secondary_fol_tangent_offset.inputs["Scale"],
    )

    secondary_fol_jittered = nodes.new("GeometryNodeSetPosition")
    secondary_fol_jittered.location = (9850, 4650)
    secondary_fol_jittered.label = "Irregular Secondary Foliage Stations"

    links.new(
        secondary_fol_points.outputs["Points"],
        secondary_fol_jittered.inputs["Geometry"],
    )
    links.new(
        secondary_fol_tangent_offset.outputs["Vector"],
        secondary_fol_jittered.inputs["Offset"],
    )

    secondary_rosettes = nodes.new("GeometryNodeInstanceOnPoints")
    secondary_rosettes.location = (10050, 4650)
    secondary_rosettes.label = "Secondary Needle Rosettes"

    links.new(
        secondary_fol_jittered.outputs["Geometry"],
        secondary_rosettes.inputs["Points"],
    )
    links.new(
        foliage_rosette,
        secondary_rosettes.inputs["Instance"],
    )
    links.new(
        secondary_fol_points.outputs["Rotation"],
        secondary_rosettes.inputs["Rotation"],
    )

    # --------------------------------------------------------
    # Join furnished primary + secondaries + foliage
    # --------------------------------------------------------

    furnished_join = nodes.new("GeometryNodeJoinGeometry")
    furnished_join.location = (10250, 3450)
    furnished_join.label = "Furnished Tamarack Branch"

    links.new(
        primary_mesh_socket,
        furnished_join.inputs["Geometry"],
    )
    links.new(
        primary_fol_instances.outputs["Instances"],
        furnished_join.inputs["Geometry"],
    )
    links.new(
        rotate_secondaries.outputs["Instances"],
        furnished_join.inputs["Geometry"],
    )
    links.new(
        secondary_rosettes.outputs["Instances"],
        furnished_join.inputs["Geometry"],
    )

    return furnished_join.outputs["Geometry"]


# ============================================================
# Reusable regular radial tier
# ============================================================


def build_primary_tier(nodes, links, group_in, branch_mesh_socket, tag, base_y):
    tier_points = nodes.new("GeometryNodeMeshLine")
    tier_points.location = (2350, base_y)
    tier_points.label = f"{tag} Tier Points"
    tier_points.mode = 'OFFSET'
    tier_points.count_mode = 'TOTAL'
    tier_points.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
    tier_points.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
    links.new(group_in.outputs["Branches Per Tier"], tier_points.inputs["Count"])

    tier_index = nodes.new("GeometryNodeInputIndex")
    tier_index.location = (2350, base_y - 250)
    tier_index.label = f"{tag} Branch Index"

    angle_step = math_node(
        nodes, 'DIVIDE', f"{tag} Tier Angular Step", math.tau, 3.0,
    )
    angle_step.location = (2550, base_y - 250)
    links.new(group_in.outputs["Branches Per Tier"], angle_step.inputs[1])

    azimuth = math_node(nodes, 'MULTIPLY', f"{tag} Branch Azimuth")
    azimuth.location = (2750, base_y - 250)
    links.new(tier_index.outputs["Index"], azimuth.inputs[0])
    links.new(angle_step.outputs[0], azimuth.inputs[1])

    tier_euler = nodes.new("ShaderNodeCombineXYZ")
    tier_euler.location = (2950, base_y - 250)
    tier_euler.label = f"{tag} Tier Euler"
    links.new(azimuth.outputs[0], tier_euler.inputs["Z"])

    tier_rotation = nodes.new("FunctionNodeEulerToRotation")
    tier_rotation.location = (3150, base_y - 250)
    tier_rotation.label = f"{tag} Tier Rotation"
    links.new(tier_euler.outputs["Vector"], tier_rotation.inputs["Euler"])

    tier_instances = nodes.new("GeometryNodeInstanceOnPoints")
    tier_instances.location = (3350, base_y)
    tier_instances.label = f"{tag} Primary Tier"
    links.new(tier_points.outputs["Mesh"], tier_instances.inputs["Points"])
    links.new(branch_mesh_socket, tier_instances.inputs["Instance"])
    links.new(tier_rotation.outputs["Rotation"], tier_instances.inputs["Rotation"])

    return tier_instances.outputs["Instances"]


# ============================================================
# Crown
# ============================================================


def build_crown(nodes, links, group_in, crown_points_socket,
                crown_rotation_socket, low_tier_socket,
                mid_tier_socket, top_tier_socket):
    crown_index = nodes.new("GeometryNodeInputIndex")
    crown_index.location = (3650, 250)
    crown_index.label = "Crown Tier Index"

    last_index = math_node(nodes, 'SUBTRACT', "Last Crown Tier Index", 0.0, 1.0)
    last_index.location = (3850, 100)
    links.new(group_in.outputs["Tier Count"], last_index.inputs[0])

    crown_factor = nodes.new("ShaderNodeMapRange")
    crown_factor.location = (4050, 100)
    crown_factor.label = "Crown Position 0..1"
    crown_factor.inputs["From Min"].default_value = 0.0
    crown_factor.inputs["To Min"].default_value = 0.0
    crown_factor.inputs["To Max"].default_value = 1.0
    links.new(crown_index.outputs["Index"], crown_factor.inputs["Value"])
    links.new(last_index.outputs[0], crown_factor.inputs["From Max"])

    lower_envelope = nodes.new("ShaderNodeMapRange")
    lower_envelope.location = (4250, 250)
    lower_envelope.label = "Lower Crown Envelope"
    lower_envelope.inputs["From Min"].default_value = 0.0
    lower_envelope.inputs["To Max"].default_value = 1.0
    links.new(crown_factor.outputs["Result"], lower_envelope.inputs["Value"])
    links.new(group_in.outputs["Widest Point"], lower_envelope.inputs["From Max"])
    links.new(group_in.outputs["Crown Base Scale"], lower_envelope.inputs["To Min"])

    upper_envelope = nodes.new("ShaderNodeMapRange")
    upper_envelope.location = (4250, 50)
    upper_envelope.label = "Upper Crown Envelope"
    upper_envelope.inputs["From Max"].default_value = 1.0
    upper_envelope.inputs["To Min"].default_value = 1.0
    links.new(crown_factor.outputs["Result"], upper_envelope.inputs["Value"])
    links.new(group_in.outputs["Widest Point"], upper_envelope.inputs["From Min"])
    links.new(group_in.outputs["Crown Tip Scale"], upper_envelope.inputs["To Max"])

    envelope = math_node(nodes, 'MINIMUM', "Crown Width Envelope")
    envelope.location = (4450, 150)
    links.new(lower_envelope.outputs["Result"], envelope.inputs[0])
    links.new(upper_envelope.outputs["Result"], envelope.inputs[1])

    growth_width = math_node(nodes, 'MULTIPLY', "Growth Form Width")
    growth_width.location = (4650, 150)
    links.new(envelope.outputs[0], growth_width.inputs[0])
    links.new(group_in.outputs["Crown Width Scale"], growth_width.inputs[1])

    tier_scale = nodes.new("ShaderNodeCombineXYZ")
    tier_scale.location = (4850, 150)
    tier_scale.label = "Uniform Growth Form Scale"
    links.new(growth_width.outputs[0], tier_scale.inputs["X"])
    links.new(growth_width.outputs[0], tier_scale.inputs["Y"])
    links.new(growth_width.outputs[0], tier_scale.inputs["Z"])

    above_upper = math_node(nodes, 'GREATER_THAN', "Above Upper Habit Start")
    above_upper.location = (4250, -200)
    links.new(crown_factor.outputs["Result"], above_upper.inputs[0])
    links.new(group_in.outputs["Upper Habit Start"], above_upper.inputs[1])

    above_top = math_node(nodes, 'GREATER_THAN', "Above Top Habit Start")
    above_top.location = (4250, -350)
    links.new(crown_factor.outputs["Result"], above_top.inputs[0])
    links.new(group_in.outputs["Top Habit Start"], above_top.inputs[1])

    habit_index = math_node(nodes, 'ADD', "Branch Habit Index")
    habit_index.location = (4450, -275)
    links.new(above_upper.outputs[0], habit_index.inputs[0])
    links.new(above_top.outputs[0], habit_index.inputs[1])

    tier_library = nodes.new("GeometryNodeGeometryToInstance")
    tier_library.location = (4050, 550)
    tier_library.label = "Branch Habit Library"
    # Intentional reverse insertion order discovered in Blender 5.2:
    # effective indices become LOW / MID / TOP.
    links.new(top_tier_socket, tier_library.inputs["Geometry"])
    links.new(mid_tier_socket, tier_library.inputs["Geometry"])
    links.new(low_tier_socket, tier_library.inputs["Geometry"])

    crown_instances = nodes.new("GeometryNodeInstanceOnPoints")
    crown_instances.location = (5100, 500)
    crown_instances.label = "Habit Tier on Crown"
    crown_instances.inputs["Pick Instance"].default_value = True
    links.new(crown_points_socket, crown_instances.inputs["Points"])
    links.new(tier_library.outputs["Instances"], crown_instances.inputs["Instance"])
    links.new(habit_index.outputs[0], crown_instances.inputs["Instance Index"])
    links.new(crown_rotation_socket, crown_instances.inputs["Rotation"])
    links.new(tier_scale.outputs["Vector"], crown_instances.inputs["Scale"])

    deg_to_rad = math_node(
        nodes, 'MULTIPLY', "Clock Degrees -> Radians", 0.0, math.pi / 180.0,
    )
    deg_to_rad.location = (4850, -150)
    links.new(group_in.outputs["Tier Clock Step"], deg_to_rad.inputs[0])

    clock_angle = math_node(nodes, 'MULTIPLY', "Successive Tier Clock")
    clock_angle.location = (5050, -150)
    links.new(crown_index.outputs["Index"], clock_angle.inputs[0])
    links.new(deg_to_rad.outputs[0], clock_angle.inputs[1])

    clock_euler = nodes.new("ShaderNodeCombineXYZ")
    clock_euler.location = (5250, -150)
    clock_euler.label = "Clock Euler"
    links.new(clock_angle.outputs[0], clock_euler.inputs["Z"])

    clock_rotation = nodes.new("FunctionNodeEulerToRotation")
    clock_rotation.location = (5450, -150)
    clock_rotation.label = "Clock Rotation"
    links.new(clock_euler.outputs["Vector"], clock_rotation.inputs["Euler"])

    rotate_tiers = nodes.new("GeometryNodeRotateInstances")
    rotate_tiers.location = (5650, 500)
    rotate_tiers.label = "Clock Successive Tiers"
    links.new(crown_instances.outputs["Instances"], rotate_tiers.inputs["Instances"])
    links.new(clock_rotation.outputs["Rotation"], rotate_tiers.inputs["Rotation"])
    if "Local Space" in rotate_tiers.inputs:
        rotate_tiers.inputs["Local Space"].default_value = True

    return rotate_tiers.outputs["Instances"]


# ============================================================
# Deterministic hash helper
# ============================================================


def build_hash_01(nodes, links, key_socket, tag, x, y,
                  frequency, multiplier, phase=0.0):
    if phase != 0.0:
        phase_add = math_node(nodes, 'ADD', f"{tag} Phase", 0.0, phase)
        phase_add.location = (x, y)
        links.new(key_socket, phase_add.inputs[0])
        key_socket = phase_add.outputs[0]
        x += 200

    frequency_node = math_node(
        nodes, 'MULTIPLY', f"{tag} Frequency", 0.0, frequency,
    )
    frequency_node.location = (x, y)
    links.new(key_socket, frequency_node.inputs[0])

    sine = nodes.new("ShaderNodeMath")
    sine.operation = 'SINE'
    sine.location = (x + 200, y)
    sine.label = f"{tag} Sine"
    links.new(frequency_node.outputs[0], sine.inputs[0])

    large = math_node(nodes, 'MULTIPLY', f"{tag} Hash", 0.0, multiplier)
    large.location = (x + 400, y)
    links.new(sine.outputs[0], large.inputs[0])

    unit = nodes.new("ShaderNodeMath")
    unit.operation = 'FRACT'
    unit.location = (x + 600, y)
    unit.label = f"{tag} 0..1"
    links.new(large.outputs[0], unit.inputs[0])

    return unit.outputs[0]


# ============================================================
# Global individual-branch variation
# ============================================================


def apply_global_branch_variation(nodes, links, group_in, crown_socket):
    # Expose nested individual branch instances.
    realize_tiers = nodes.new("GeometryNodeRealizeInstances")
    realize_tiers.location = (5900, 500)
    realize_tiers.label = "Expose Individual Branches"
    links.new(crown_socket, realize_tiers.inputs["Geometry"])
    if "Realize All" in realize_tiers.inputs:
        realize_tiers.inputs["Realize All"].default_value = False
    if "Depth" in realize_tiers.inputs:
        realize_tiers.inputs["Depth"].default_value = 1

    branch_index = nodes.new("GeometryNodeInputIndex")
    branch_index.location = (5900, 150)
    branch_index.label = "Global Branch Index"

    seed_offset = math_node(nodes, 'MULTIPLY', "Variation Seed Offset", 0.0, 101.0)
    seed_offset.location = (6100, 50)
    links.new(group_in.outputs["Seed"], seed_offset.inputs[0])

    index_plus_seed = math_node(nodes, 'ADD', "Branch Index + Seed")
    index_plus_seed.location = (6100, 200)
    links.new(branch_index.outputs["Index"], index_plus_seed.inputs[0])
    links.new(seed_offset.outputs[0], index_plus_seed.inputs[1])

    variation_key = math_node(nodes, 'ADD', "Variation Key", 0.0, 1.0)
    variation_key.location = (6300, 200)
    links.new(index_plus_seed.outputs[0], variation_key.inputs[0])

    # --------------------------------------------------------
    # Channel 1: branch length / proportional size
    # --------------------------------------------------------
    length_hash = build_hash_01(
        nodes, links, variation_key.outputs[0],
        "Length Variation", 6500, 250,
        frequency=12.9898,
        multiplier=43758.5453,
    )

    minimum_scale = math_node(nodes, 'SUBTRACT', "Minimum Branch Scale", 1.0, 0.0)
    minimum_scale.location = (6500, -50)
    links.new(group_in.outputs["Branch Length Variation"], minimum_scale.inputs[1])

    variation_span = math_node(nodes, 'MULTIPLY', "Branch Variation Span", 0.0, 2.0)
    variation_span.location = (6700, -50)
    links.new(group_in.outputs["Branch Length Variation"], variation_span.inputs[0])

    random_offset = math_node(nodes, 'MULTIPLY', "Random Branch Scale Offset")
    random_offset.location = (7300, 100)
    links.new(length_hash, random_offset.inputs[0])
    links.new(variation_span.outputs[0], random_offset.inputs[1])

    branch_scale = math_node(nodes, 'ADD', "Individual Branch Scale")
    branch_scale.location = (7500, 100)
    links.new(minimum_scale.outputs[0], branch_scale.inputs[0])
    links.new(random_offset.outputs[0], branch_scale.inputs[1])

    scale_vector = nodes.new("ShaderNodeCombineXYZ")
    scale_vector.location = (7700, 100)
    scale_vector.label = "Individual Branch Scale Vector"
    links.new(branch_scale.outputs[0], scale_vector.inputs["X"])
    links.new(branch_scale.outputs[0], scale_vector.inputs["Y"])
    links.new(branch_scale.outputs[0], scale_vector.inputs["Z"])

    scale_branches = nodes.new("GeometryNodeScaleInstances")
    scale_branches.location = (7900, 500)
    scale_branches.label = "Vary Individual Branch Lengths"
    links.new(realize_tiers.outputs["Geometry"], scale_branches.inputs["Instances"])
    links.new(scale_vector.outputs["Vector"], scale_branches.inputs["Scale"])

    # --------------------------------------------------------
    # Channel 2: branch azimuth variation
    # --------------------------------------------------------
    azimuth_hash = build_hash_01(
        nodes, links, variation_key.outputs[0],
        "Azimuth Variation", 6500, -300,
        frequency=78.233,
        multiplier=12345.6789,
        phase=17.371,
    )

    hash_times_two = math_node(nodes, 'MULTIPLY', "Azimuth Hash x2", 0.0, 2.0)
    hash_times_two.location = (7500, -300)
    links.new(azimuth_hash, hash_times_two.inputs[0])

    signed_hash = math_node(nodes, 'SUBTRACT', "Signed Azimuth Hash", 0.0, 1.0)
    signed_hash.location = (7700, -300)
    links.new(hash_times_two.outputs[0], signed_hash.inputs[0])

    azimuth_degrees = math_node(nodes, 'MULTIPLY', "Branch Azimuth Offset Degrees")
    azimuth_degrees.location = (7900, -300)
    links.new(signed_hash.outputs[0], azimuth_degrees.inputs[0])
    links.new(group_in.outputs["Branch Azimuth Variation"], azimuth_degrees.inputs[1])

    azimuth_radians = math_node(
        nodes, 'MULTIPLY', "Branch Azimuth Offset Radians",
        0.0, math.pi / 180.0,
    )
    azimuth_radians.location = (8100, -300)
    links.new(azimuth_degrees.outputs[0], azimuth_radians.inputs[0])

    azimuth_euler = nodes.new("ShaderNodeCombineXYZ")
    azimuth_euler.location = (8300, -300)
    azimuth_euler.label = "Branch Azimuth Euler"
    links.new(azimuth_radians.outputs[0], azimuth_euler.inputs["Z"])

    azimuth_rotation = nodes.new("FunctionNodeEulerToRotation")
    azimuth_rotation.location = (8500, -300)
    azimuth_rotation.label = "Branch Azimuth Rotation"
    links.new(azimuth_euler.outputs["Vector"], azimuth_rotation.inputs["Euler"])

    rotate_branches = nodes.new("GeometryNodeRotateInstances")
    rotate_branches.location = (8700, 500)
    rotate_branches.label = "Vary Individual Branch Azimuths"
    links.new(scale_branches.outputs["Instances"], rotate_branches.inputs["Instances"])
    links.new(azimuth_rotation.outputs["Rotation"], rotate_branches.inputs["Rotation"])
    if "Local Space" in rotate_branches.inputs:
        rotate_branches.inputs["Local Space"].default_value = True

    return rotate_branches.outputs["Instances"]


# ============================================================
# Interface
# ============================================================


def build_interface(tree):
    tree.interface.new_socket(
        name="Geometry",
        in_out='OUTPUT',
        socket_type="NodeSocketGeometry",
    )

    tree_panel = tree.interface.new_panel(
        "TREE",
        description="Basic northern-tree dimensions",
    )
    add_input(tree, "Height", "NodeSocketFloat", 3.0, 0.25, 12.0,
              tree_panel, "Overall tree height in metres")
    add_input(tree, "Base Diameter", "NodeSocketFloat", 0.08, 0.005, 0.50,
              tree_panel, "Leader diameter at ground level")
    add_input(tree, "Leader Wander", "NodeSocketFloat", 0.025, 0.0, 0.25,
              tree_panel, "Maximum leader displacement")
    add_input(tree, "Leader Points", "NodeSocketInt", 16, 4, 64,
              tree_panel, "Leader control point count")

    crown_panel = tree.interface.new_panel(
        "CROWN",
        description="Crown dimensions and silhouette",
    )
    add_input(tree, "Crown Start", "NodeSocketFloat", 0.22, 0.0, 1.0,
              crown_panel, "Fraction of leader where crown begins")
    add_input(tree, "Crown End", "NodeSocketFloat", 0.94, 0.0, 1.0,
              crown_panel, "Fraction of leader where crown ends")
    add_input(tree, "Tier Count", "NodeSocketInt", 13, 2, 64,
              crown_panel, "Number of branch tiers")
    add_input(tree, "Tier Clock Step", "NodeSocketFloat", 37.0, -180.0, 180.0,
              crown_panel, "Successive tier rotation")
    add_input(tree, "Crown Width Scale", "NodeSocketFloat", 1.0, 0.20, 2.50,
              crown_panel, "Overall fat / skinny growth form")
    add_input(tree, "Crown Base Scale", "NodeSocketFloat", 0.70, 0.0, 2.0,
              crown_panel, "Envelope multiplier at crown bottom")
    add_input(tree, "Widest Point", "NodeSocketFloat", 0.35, 0.05, 0.95,
              crown_panel, "Position of maximum crown width")
    add_input(tree, "Crown Tip Scale", "NodeSocketFloat", 0.20, 0.0, 2.0,
              crown_panel, "Envelope multiplier at crown top")

    branch_panel = tree.interface.new_panel(
        "BRANCHES",
        description="Primary branch morphology",
    )
    add_input(tree, "Primary Length", "NodeSocketFloat", 0.55, 0.05, 2.0,
              branch_panel, "Nominal maximum primary branch length")
    add_input(tree, "Branch Base Radius", "NodeSocketFloat", 0.012, 0.002, 0.10,
              branch_panel, "Primary branch base radius")
    add_input(tree, "Branch Sag", "NodeSocketFloat", 0.05, 0.0, 0.30,
              branch_panel, "Lower-crown branch sag")
    add_input(tree, "Tip Recovery", "NodeSocketFloat", 0.08, 0.0, 0.50,
              branch_panel, "Lower-crown tip recovery")
    add_input(tree, "Branches Per Tier", "NodeSocketInt", 3, 1, 8,
              branch_panel, "Primary branches per tier")

    habit_panel = tree.interface.new_panel(
        "BRANCH HABIT",
        description="Branch attitude through crown height",
    )
    add_input(tree, "Upper Habit Start", "NodeSocketFloat", 0.67, 0.0, 1.0,
              habit_panel, "Start of ascending upper habit")
    add_input(tree, "Top Habit Start", "NodeSocketFloat", 0.85, 0.0, 1.0,
              habit_panel, "Start of topmost habit")
    add_input(tree, "Low Rise", "NodeSocketFloat", 0.0, -30.0, 60.0,
              habit_panel, "Lower-crown departure angle")
    add_input(tree, "Mid Rise", "NodeSocketFloat", 15.0, -30.0, 60.0,
              habit_panel, "Upper-middle departure angle")
    add_input(tree, "Top Rise", "NodeSocketFloat", 35.0, -30.0, 75.0,
              habit_panel, "Top-crown departure angle")
    add_input(tree, "Mid Curvature", "NodeSocketFloat", 0.60, 0.0, 2.0,
              habit_panel, "Upper-middle sag/recovery multiplier")
    add_input(tree, "Top Curvature", "NodeSocketFloat", 0.20, 0.0, 2.0,
              habit_panel, "Top sag/recovery multiplier")

    foliage_panel = tree.interface.new_panel(
        "FOLIAGE SCAFFOLD",
        description="Prototype tamarack secondary long-shoot architecture",
    )
    add_input(tree, "Secondary Start", "NodeSocketFloat", 0.12, 0.0, 0.90,
              foliage_panel, "Primary-branch factor where secondary shoots begin")
    add_input(tree, "Secondary End", "NodeSocketFloat", 0.90, 0.10, 1.0,
              foliage_panel, "Primary-branch factor where secondary shoots end")
    add_input(tree, "Secondary Count", "NodeSocketInt", 8, 3, 24,
              foliage_panel, "Number of secondary long shoots on prototype primary")
    add_input(tree, "Secondary Max Length", "NodeSocketFloat", 0.22, 0.03, 0.50,
              foliage_panel, "Maximum secondary long-shoot length in metres")
    add_input(tree, "Secondary Radius", "NodeSocketFloat", 0.0025, 0.0005, 0.03,
              foliage_panel, "Secondary long-shoot base radius")
    add_input(tree, "Secondary Forward Sweep", "NodeSocketFloat", 0.12, 0.0, 0.60,
              foliage_panel, "Forward component along primary as fraction of shoot length")
    add_input(tree, "Secondary Sag", "NodeSocketFloat", 0.025, 0.0, 0.15,
              foliage_panel, "Intrinsic sag of a maximum-length secondary shoot")
    add_input(tree, "Secondary Length Variation", "NodeSocketFloat", 0.20, 0.0, 0.60,
              foliage_panel, "Maximum proportional secondary-shoot length variation")
    add_input(tree, "Secondary Spacing Variation", "NodeSocketFloat", 0.18, 0.0, 0.45,
              foliage_panel, "Station jitter as fraction of nominal secondary spacing")
    add_input(tree, "Secondary Base Droop", "NodeSocketFloat", 15.0, -30.0, 90.0,
              foliage_panel, "Downward departure bias in degrees")
    add_input(tree, "Secondary Long Shoot Droop", "NodeSocketFloat", 35.0, 0.0, 90.0,
              foliage_panel, "Additional downward bias applied to longer shoots")
    add_input(tree, "Secondary Azimuth Spread", "NodeSocketFloat", 85.0, 0.0, 180.0,
              foliage_panel, "Angular spread around the downward-biased departure direction")

    foliage_station_panel = tree.interface.new_panel(
        "FOLIAGE STATIONS",
        description="Tamarack foliage distribution and rosette controls",
    )

    add_input(
        tree,
        "Primary Foliage Start",
        "NodeSocketFloat",
        0.10,
        0.0,
        0.90,
        foliage_station_panel,
        "Primary-branch factor where foliage stations begin",
    )

    add_input(
        tree,
        "Primary Foliage End",
        "NodeSocketFloat",
        0.97,
        0.10,
        1.0,
        foliage_station_panel,
        "Primary-branch factor where foliage stations end",
    )

    add_input(
        tree,
        "Primary Foliage Count",
        "NodeSocketInt",
        15,
        3,
        40,
        foliage_station_panel,
        "Diagnostic foliage-station count on the primary",
    )

    add_input(
        tree,
        "Secondary Foliage Start",
        "NodeSocketFloat",
        0.05,
        0.0,
        0.90,
        foliage_station_panel,
        "Secondary-shoot factor where foliage stations begin",
    )

    add_input(
        tree,
        "Secondary Foliage End",
        "NodeSocketFloat",
        0.97,
        0.10,
        1.0,
        foliage_station_panel,
        "Secondary-shoot factor where foliage stations end",
    )

    add_input(
        tree,
        "Secondary Foliage Count",
        "NodeSocketInt",
        9,
        3,
        30,
        foliage_station_panel,
        "Diagnostic foliage-station count on every secondary",
    )

    add_input(
        tree,
        "Foliage Spacing Variation",
        "NodeSocketFloat",
        0.12,
        0.0,
        0.40,
        foliage_station_panel,
        "Bounded station jitter as fraction of nominal spacing",
    )

    add_input(
        tree,
        "Rosette Rings",
        "NodeSocketInt",
        4,
        2,
        8,
        foliage_station_panel,
        "Number of tiny needle whorls along one short-shoot spur",
    )

    add_input(
        tree,
        "Needles Per Ring",
        "NodeSocketInt",
        6,
        3,
        12,
        foliage_station_panel,
        "Needles carried by each mini-whorl",
    )

    add_input(
        tree,
        "Needle Length",
        "NodeSocketFloat",
        0.016,
        0.008,
        0.040,
        foliage_station_panel,
        "Needle length in metres",
    )

    add_input(
        tree,
        "Needle Radius",
        "NodeSocketFloat",
        0.00030,
        0.00015,
        0.0015,
        foliage_station_panel,
        "Low-poly diagnostic needle radius",
    )

    add_input(
        tree,
        "Short Shoot Length",
        "NodeSocketFloat",
        0.006,
        0.001,
        0.015,
        foliage_station_panel,
        "Tiny woody spur length carrying the mini-whorls",
    )

    add_input(
        tree,
        "Ring Clock Step",
        "NodeSocketFloat",
        42.0,
        -180.0,
        180.0,
        foliage_station_panel,
        "Rotation in degrees between successive needle whorls",
    )

    add_input(
        tree,
        "Rosette Cone Angle",
        "NodeSocketFloat",
        7.0,
        0.0,
        30.0,
        foliage_station_panel,
        "Alternating needle elevation from each whorl plane",
    )

    add_input(
        tree,
        "Needle Length Variation",
        "NodeSocketFloat",
        0.12,
        0.0,
        0.40,
        foliage_station_panel,
        "Maximum proportional per-needle length variation",
    )

    add_input(
        tree,
        "Needle Azimuth Variation",
        "NodeSocketFloat",
        6.0,
        0.0,
        30.0,
        foliage_station_panel,
        "Maximum per-needle azimuth jitter in degrees",
    )

    variation_panel = tree.interface.new_panel(
        "VARIATION",
        description="Bounded deterministic individuality",
    )
    add_input(tree, "Seed", "NodeSocketInt", 0, 0, 100000,
              variation_panel, "Deterministic variation seed")
    add_input(tree, "Branch Length Variation", "NodeSocketFloat", 0.15, 0.0, 0.50,
              variation_panel, "Maximum proportional branch-size variation")
    add_input(tree, "Branch Azimuth Variation", "NodeSocketFloat", 7.0, 0.0, 30.0,
              variation_panel, "Maximum branch azimuth offset in degrees")
    add_input(tree, "Tier Spacing Variation", "NodeSocketFloat", 0.15, 0.0, 0.40,
              variation_panel, "Maximum tier-height jitter as a fraction of nominal spacing")


# ============================================================
# Main generator: runtime spray proof
# ============================================================


def print_evaluated_stats(obj):
    """Print evaluated mesh statistics after the Geometry Nodes build."""
    try:
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            print("Evaluated runtime mesh:")
            print("  Vertices :", len(mesh.vertices))
            print("  Edges    :", len(mesh.edges))
            print("  Faces    :", len(mesh.polygons))
            print("  Triangles:", len(mesh.loop_triangles))
        finally:
            eval_obj.to_mesh_clear()
    except Exception as exc:
        print("Evaluated mesh statistics unavailable:", exc)


def build_northern_tree_runtime_proof():
    obj = get_or_create_host()

    atlas = ensure_mixed_atlas()
    atlas_material = ensure_atlas_material(atlas)
    spray_sources = {
        tag: ensure_runtime_spray_source(tag, ATLAS_CELLS[tag], atlas_material)
        for tag in ("LOW", "MID", "TOP")
    }

    old_group = bpy.data.node_groups.get(GROUP_NAME)
    if old_group is not None:
        bpy.data.node_groups.remove(old_group, do_unlink=True)

    tree = bpy.data.node_groups.new(GROUP_NAME, "GeometryNodeTree")
    build_interface(tree)

    nodes = tree.nodes
    links = tree.links

    group_in = nodes.new("NodeGroupInput")
    group_in.location = (-1400, 100)
    group_in.label = "Northern Tree Parameters"

    group_out = nodes.new("NodeGroupOutput")
    group_out.location = (9300, 300)

    # Keep the known-good leader and crown-placement machinery.
    leader_mesh, leader_curve = build_leader(nodes, links, group_in)
    crown_points, crown_rotation = build_crown_stations(
        nodes, links, group_in, leader_curve,
    )

    # Runtime LOW/MID/TOP archetypes.  Each is exactly two triangles.
    low_spray = build_runtime_spray(
        nodes, links, group_in, spray_sources["LOW"],
        tag="LOW",
        rise_input_name="Low Rise",
        base_y=1100,
    )
    low_tier = build_primary_tier(
        nodes, links, group_in, low_spray,
        tag="LOW",
        base_y=1100,
    )

    mid_spray = build_runtime_spray(
        nodes, links, group_in, spray_sources["MID"],
        tag="MID",
        rise_input_name="Mid Rise",
        base_y=1800,
    )
    mid_tier = build_primary_tier(
        nodes, links, group_in, mid_spray,
        tag="MID",
        base_y=1800,
    )

    top_spray = build_runtime_spray(
        nodes, links, group_in, spray_sources["TOP"],
        tag="TOP",
        rise_input_name="Top Rise",
        base_y=2500,
    )
    top_tier = build_primary_tier(
        nodes, links, group_in, top_spray,
        tag="TOP",
        base_y=2500,
    )

    crown = build_crown(
        nodes, links, group_in,
        crown_points, crown_rotation,
        low_tier, mid_tier, top_tier,
    )

    varied_crown = apply_global_branch_variation(
        nodes, links, group_in, crown,
    )

    join_geometry = nodes.new("GeometryNodeJoinGeometry")
    join_geometry.location = (9050, 300)
    join_geometry.label = "Northern Tree Runtime Proof"
    links.new(leader_mesh, join_geometry.inputs["Geometry"])
    links.new(varied_crown, join_geometry.inputs["Geometry"])
    realize_final = nodes.new("GeometryNodeRealizeInstances")
    realize_final.location = (9250, 300)
    realize_final.label = "Realize Runtime Tree"
    links.new(join_geometry.outputs["Geometry"], realize_final.inputs["Geometry"])
    links.new(realize_final.outputs["Geometry"], group_out.inputs["Geometry"])

    modifier = obj.modifiers.new(MODIFIER_NAME, 'NODES')
    modifier.node_group = tree

    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    print("")
    print("Northern Trees v0.8c - MID texture atlas proof (root/tip anchored)")
    print("-------------------------------------------")
    print("Representation:")
    print("  leader/trunk          = existing cheap geometry")
    print("  each primary branch   = 4 vertices / 2 triangles")
    print(f"  spray fold angle      = {SPRAY_FOLD_DEGREES:.1f} deg")
    print("")
    print("Preserved from v0.4a:")
    print("  crown stations and tier jitter")
    print("  crown width envelope")
    print("  LOW / MID / TOP habit selection")
    print("  tier clocking")
    print("  deterministic branch length and azimuth variation")
    print("")
    print("Intentionally NOT instantiated in this runtime proof:")
    print("  primary branch tubes")
    print("  secondary long-shoot geometry")
    print("  short-shoot geometry")
    print("  modeled needles / rosettes")
    print("")
    print("At default 13 tiers x 3 branches:")
    print("  foliage sprays = 39")
    print("  spray triangles = 78")
    print("")

    print_evaluated_stats(obj)
    print("")
    print("First visual test:")
    print("  inspect the whole-tree silhouette in solid view")
    print("  then try Low Rise / Mid Rise / Top Rise")
    print("  and Crown Width Scale = 0.75 / 1.00 / 1.30")
    print("")
    print("Mixed runtime atlas applied:")
    print("  LOW = diagnostic warm cell")
    print("  MID = actual transparent botanical branch render, root/tip anchored")
    print("  TOP = diagnostic blue cell")
    print("  LOW/TOP retain fold markers")
    print("")
    print("Switch viewport to Material Preview to inspect atlas mapping.")
    print("")


build_northern_tree_runtime_proof()