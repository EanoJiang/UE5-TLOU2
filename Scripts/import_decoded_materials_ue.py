"""Import decoded ND textures and wire the exact static catalog materials.

The FBX importer preserves each original game material as a static-material
slot named ``M_ND_<material>``.  This commandlet imports the decoded PNGs,
creates one UE material per slot, connects color/normal/AO maps, and assigns
the material to every matching static mesh in the catalog map.
"""
import unreal, os, json

ROOT = r"D:/TLOU2_UE5_8_Codex"
SRC = ROOT + "/Exports/TexturesDecoded"
TEX_DEST = "/Game/TLOU2/TexturesDecoded"
MAT_DEST = "/Game/TLOU2/Materials/Exact"
MESH_DEST = "/Game/TLOU2/ExactStatic"
REPORT = ROOT + "/Content/TLOU2/Reports/UE_TEXTURE_MATERIAL_REPORT.json"

at = unreal.AssetToolsHelpers.get_asset_tools()

def import_textures():
    paths = []
    for name in sorted(os.listdir(SRC)):
        if not name.lower().endswith(".png"):
            continue
        full = os.path.join(SRC, name).replace("\\", "/")
        task = unreal.AssetImportTask()
        task.filename = full
        task.destination_path = TEX_DEST
        task.destination_name = os.path.splitext(name)[0]
        task.automated = True
        task.replace_existing = True
        task.save = True
        paths.append(task)
    # Import as one batch so the asset registry is updated before materials.
    at.import_asset_tasks(paths)
    out = {}
    for task in paths:
        for p in task.imported_object_paths:
            tex = unreal.load_asset(p)
            if tex:
                # Object paths are `/Game/.../name.name`; material tables use
                # the source PNG stem without the duplicated object suffix.
                obj_name = os.path.basename(p).split('.')[0].lower()
                out[obj_name] = tex
    unreal.log("UE_TEXTURES_IMPORTED %d" % len(out))
    return out

COLOR = {
  "patrol-tshirt":"ellie16-patrol-shirt-color", "skein":"ellie-shirt-skein-color", "pants":"ellie-patrol-pants-color", "theater-pants":"ellie-festival-pants-color",
  "shoes":"ellie-shoes-color", "boots":"ellie-festival-boots-color", "jacket":"ellie-patrol-jacket-color", "hoodie-up-nowrinkles":"ellie-patrol-hoodie-up-color",
  "backpack":"ellie-backpack-color", "backpack-acces":"ellie-backpack-acces-color", "backpack-skein":"ellie-backpack-color", "backpack-velcro":"ellie-backpack-velcro-color",
  "hair-base":"ellie-hair-thick-color-new", "hair-thick":"ellie-hair-thick-color", "hair-thick-alpha":"ellie-hair-thick-color", "hair-thin":"ellie-hair-thin-color", "hair-thin-alpha":"ellie-hair-thin-color", "hair-thin-wet":"ellie-hair-thin-color", "hair-flying-alpha":"ellie-hair-flying-color",
  "head":"ellie-head-color", "arms":"ellie16-arms-color-tattoo", "torso-ao":"ellie-torso-color", "gloves":"ellie-patrol-gloves-color", "teeth":"ellie-teeth-color", "eyebrows":"ellie-brows-color", "eyes":"ellie-eyes-iris-color"
}
NORMAL = {
  "patrol-tshirt":"ellie16-patrol-shirt-normal", "skein":"ellie-shirt-skein-normal", "pants":"ellie-patrol-pants-normal", "theater-pants":"ellie-festival-pants-normal",
  "shoes":"ellie-shoes-normal", "boots":"ellie-festival-boots-normal", "jacket":"ellie-patrol-jacket-normal", "hoodie-up-nowrinkles":"ellie-patrol-hoodie-up-normal",
  "backpack":"ellie-backpack-normal", "backpack-acces":"ellie-backpack-acces-normal", "backpack-skein":"ellie-backpack-normal", "backpack-velcro":"ellie-backpack-velcro-normal",
  "hair-base":"ellie-hair-thick-normal", "hair-thick":"ellie-hair-thick-normal", "hair-thick-alpha":"ellie-hair-thick-normal", "hair-thin":"ellie-hair-thin-normal", "hair-thin-alpha":"ellie-hair-thin-normal", "hair-thin-wet":"ellie-hair-thin-wet-normal", "hair-flying-alpha":"ellie-hair-flying-normal",
  "head":"ellie-head-normal-xyz", "arms":"ellie16-arms-normal", "torso-ao":"ellie-torso-normal", "gloves":"ellie-patrol-gloves-normal", "teeth":"ellie-teeth-normal", "eyebrows":"ellie-brows-normal", "eyes":"iris-normal", "eyelashes":"ellie-eyelashes-normal"
}

OPACITY = {
 "hair-base":"ellie-hair-thick-trans", "hair-thick":"ellie-hair-thick-trans", "hair-thick-alpha":"ellie-hair-thick-trans",
 "hair-thin":"ellie-hair-thin-trans", "hair-thin-alpha":"ellie-hair-thin-trans", "hair-thin-wet":"ellie-hair-thin-wet-trans",
 "hair-flying-alpha":"ellie-hair-flying-trans", "eyebrows":"ellie-brows-trans", "eyelashes":"ellie-eyelashes-trans",
}
AO = {
  "patrol-tshirt":"ellie16-patrol-shirt-no-backpack-ao", "skein":"ellie-shirt-skein-ao", "pants":"ellie-patrol-pants-wetness-mask", "theater-pants":"ellie-festival-pants-ao",
  "shoes":"ellie-shoes-ao", "boots":"ellie-festival-boots-ao", "jacket":"ellie-patrol-jacket-ao", "hoodie-up-nowrinkles":"ellie-patrol-hoodie-up-ao",
  "backpack":"ellie-backpack-ao", "backpack-acces":"ellie-backpack-contact-ao", "backpack-skein":"ellie-backpack-ao", "backpack-velcro":"ellie-backpack-contact-ao",
  "hair-thick":"ellie-hair-thick-ao", "hair-thick-alpha":"ellie-hair-thick-ao", "hair-thin":"ellie-hair-thick-ao", "hair-thin-alpha":"ellie-hair-thick-ao", "hair-thin-wet":"ellie-hair-thin-wet-ao", "hair-flying-alpha":"ellie-hair-flying-ao",
  "head":"ellie-head-ao", "arms":"ellie-arms-ao", "torso-ao":"ellie-torso-ao", "gloves":"ellie-patrol-gloves-ao", "teeth":"ellie-teeth-ao", "eyebrows":"ellie-brows-ao", "eyes":"iris-height"
}

def tex(by_name, stem):
    return by_name.get((stem or "").lower())

def make_material(key, textures):
    name = "M_ND_" + key
    path = MAT_DEST + "/" + name
    mat = unreal.load_asset(path)
    if not mat:
        mat = at.create_asset(name, MAT_DEST, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        return None
    if MAT_DEST == '/Game/TLOU2/Materials/Exact':
        unreal.MaterialEditingLibrary.set_base_material_usage(mat,unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH,True)
        unreal.MaterialEditingLibrary.set_base_material_usage(mat,unreal.MaterialUsage.MATUSAGE_MORPH_TARGETS,True)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    x = -900
    color = tex(textures, COLOR.get(key))
    normal = tex(textures, NORMAL.get(key))
    ao = tex(textures, AO.get(key))
    opacity = tex(textures, OPACITY.get(key))
    if color:
        color.set_editor_property('srgb', True)
        color.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_DEFAULT)
        unreal.EditorAssetLibrary.save_loaded_asset(color)
    if normal:
        normal.set_editor_property('srgb', False)
        normal.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_NORMALMAP)
        unreal.EditorAssetLibrary.save_loaded_asset(normal)
    for scalar in [ao, opacity]:
        if scalar:
            scalar.set_editor_property('srgb', False)
            scalar.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_MASKS)
            unreal.EditorAssetLibrary.save_loaded_asset(scalar)
    if opacity:
        mat.set_editor_property('blend_mode', unreal.BlendMode.BLEND_MASKED)
        mat.set_editor_property('two_sided', True)
        mat.set_editor_property('opacity_mask_clip_value', 0.25)
        n = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, 540)
        n.set_editor_property('parameter_name', 'ND_Opacity')
        n.set_editor_property('texture', opacity)
        n.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        unreal.MaterialEditingLibrary.connect_material_property(n, 'R', unreal.MaterialProperty.MP_OPACITY_MASK)
    if color:
        n = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, 0)
        n.set_editor_property("parameter_name", "ND_Color")
        n.set_editor_property("texture", color)
        unreal.MaterialEditingLibrary.connect_material_property(n, "", unreal.MaterialProperty.MP_BASE_COLOR)
        n.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    if normal:
        n = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, 180)
        n.set_editor_property("parameter_name", "ND_Normal")
        n.set_editor_property("texture", normal)
        try: n.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        except Exception: pass
        unreal.MaterialEditingLibrary.connect_material_property(n, "", unreal.MaterialProperty.MP_NORMAL)
    if ao:
        n = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, 360)
        n.set_editor_property("parameter_name", "ND_AO")
        n.set_editor_property("texture", ao)
        try: unreal.MaterialEditingLibrary.connect_material_property(n, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
        except Exception: pass
        n.set_editor_property('sampler_type', unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 650)
    rough.set_editor_property('r', .9 if 'hair' in key else (.64 if key in ('head','arms') else .8))
    unreal.MaterialEditingLibrary.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat

def assign_materials(materials):
    meshes = 0; slots = 0
    for p in unreal.EditorAssetLibrary.list_assets(MESH_DEST, recursive=True):
        sm = unreal.load_asset(p)
        if not isinstance(sm, unreal.StaticMesh):
            continue
        arr = sm.get_editor_property("static_materials")
        changed = False
        for slot_index, slot in enumerate(arr):
            slot_name = str(slot.get_editor_property("material_slot_name"))
            key = slot_name[5:] if slot_name.startswith("M_ND_") else ""
            mat = materials.get(key)
            if mat:
                # StaticMaterial is a value struct in the Python API.  Calling
                # StaticMesh.set_material writes the array back to the asset;
                # mutating the temporary struct alone is silently discarded.
                sm.set_material(slot_index, mat)
                changed = True; slots += 1
        if changed:
            unreal.EditorAssetLibrary.save_loaded_asset(sm)
            meshes += 1
    unreal.log("UE_MATERIALS_ASSIGNED meshes=%d slots=%d" % (meshes, slots))
    return meshes, slots

textures = import_textures()
materials = {}
for key in sorted(set(list(COLOR) + list(NORMAL) + list(AO))):
    m = make_material(key, textures)
    if m: materials[key] = m
meshes, slots = assign_materials(materials)
report = {"textures_imported": len(textures), "materials_created": len(materials), "meshes_assigned": meshes, "slots_assigned": slots, "texture_root": TEX_DEST, "material_root": MAT_DEST}
os.makedirs(os.path.dirname(REPORT), exist_ok=True)
json.dump(report, open(REPORT, "w", encoding="utf-8"), indent=2)
unreal.log("UE_EXACT_MATERIALS_DONE " + str(report))
