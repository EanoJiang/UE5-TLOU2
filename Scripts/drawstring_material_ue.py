"""Build only an isolated drawstring material; called by the root UE importer.

exec this file with __name__='drawstring_material', then call build_material().
No import-time asset writes. No mesh, skeleton, BP, actor or level edits.
"""
import hashlib
import json
from pathlib import Path

import unreal

ROOT = Path(r"D:/TLOU2_UE5_8_Codex")
OUT = ROOT / "Exports/Drawstring"
MATERIAL_PATH = "/Game/TLOU2/Drawstring/M_Ellie_Patrol_Drawstrings"
TEXTURE_DEST = "/Game/TLOU2/Drawstring/Textures"


def build_material():
    spec = json.loads((OUT / "Material_SourcePrimary.json").read_text())
    assert spec["pass"] and spec["ue_material_path"] == MATERIAL_PATH
    mel = unreal.MaterialEditingLibrary
    assets = unreal.EditorAssetLibrary
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    textures = {}
    reused = []
    for channel, row in spec["maps"].items():
        assert hashlib.sha256(Path(row["path"]).read_bytes()).hexdigest() == row["sha256"]
        if channel == "ao":
            tex = unreal.load_asset(row["preferred_existing_ue_path"])
            if isinstance(tex, unreal.Texture2D) and not tex.get_editor_property("srgb"):
                textures[channel] = tex
                reused.append(tex.get_path_name())
                continue
        task = unreal.AssetImportTask()
        task.filename = row["path"]
        task.destination_path = TEXTURE_DEST
        task.destination_name = row["stem"]
        task.automated = True
        task.replace_existing = True
        task.save = True
        asset_tools.import_asset_tasks([task])
        tex = unreal.load_asset(TEXTURE_DEST + "/" + row["stem"])
        assert isinstance(tex, unreal.Texture2D), channel
        tex.set_editor_property("srgb", channel == "color")
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP if channel == "normal"
                                else unreal.TextureCompressionSettings.TC_DEFAULT if channel == "color"
                                else unreal.TextureCompressionSettings.TC_MASKS)
        if channel == "normal":
            tex.set_editor_property("flip_green_channel", False)
        assert assets.save_loaded_asset(tex)
        textures[channel] = tex
    mat = unreal.load_asset(MATERIAL_PATH)
    if mat is None:
        folder, name = MATERIAL_PATH.rsplit("/", 1)
        assets.make_directory(folder)
        mat = asset_tools.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    assert isinstance(mat, unreal.Material)
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    mat.set_editor_property("two_sided", False)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    mel.set_base_material_usage(mat, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH, True)
    mel.set_base_material_usage(mat, unreal.MaterialUsage.MATUSAGE_MORPH_TARGETS, True)
    props = {"color": unreal.MaterialProperty.MP_BASE_COLOR, "normal": unreal.MaterialProperty.MP_NORMAL,
             "ao": unreal.MaterialProperty.MP_AMBIENT_OCCLUSION, "roughness": unreal.MaterialProperty.MP_ROUGHNESS}
    for index, (channel, prop) in enumerate(props.items()):
        node = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -500, index * 210)
        node.set_editor_property("parameter_name", "ND_Drawstring_" + channel.title())
        node.set_editor_property("texture", textures[channel])
        node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if channel == "color"
                                 else unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if channel == "normal"
                                 else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        assert mel.connect_material_property(node, "" if channel in ("color", "normal") else "R", prop)
    for name, value, prop, ypos in [("UE_Bridge_Metallic", 0., unreal.MaterialProperty.MP_METALLIC, 850),
                                    ("UE_Bridge_Specular", .5, unreal.MaterialProperty.MP_SPECULAR, 1000)]:
        node = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -450, ypos)
        node.set_editor_property("parameter_name", name)
        node.set_editor_property("default_value", value)
        assert mel.connect_material_property(node, "", prop)
    assets.set_metadata_tag(mat, "drawstring_source_manifest", str(OUT / "Material_SourcePrimary.json"))
    assets.set_metadata_tag(mat, "drawstring_source_scope", spec["scope"])
    assets.set_metadata_tag(mat, "drawstring_original_material", spec["source_material"])
    mel.recompile_material(mat)
    assert assets.save_loaded_asset(mat)
    graph = {}
    for channel, prop in props.items():
        node = mel.get_material_property_input_node(mat, prop)
        assert node and node.get_editor_property("texture") == textures[channel]
        graph[channel] = {"texture": textures[channel].get_path_name(),
                          "srgb": bool(textures[channel].get_editor_property("srgb")),
                          "compression": str(textures[channel].get_editor_property("compression_settings"))}
    report = {"pass": True, "material_path": mat.get_path_name(), "active_graph": graph,
              "reused_existing_textures_read_only": reused,
              "skeletal_usage": bool(mat.get_editor_property("used_with_skeletal_mesh")),
              "morph_usage": bool(mat.get_editor_property("used_with_morph_targets")),
              "metallic_bridge_default": 0, "specular_bridge_default": .5,
              "scope": spec["scope"], "limitations": spec["limitations"],
              "canonical_material_mesh_blueprint_level_edits": False,
              "persistence": "save_loaded_asset returnedTrue; connected inputs verified in the running editor. Fresh editor persistence/render verification remains the caller's responsibility."}
    (OUT / "Material_UE_Application.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("DRAWSTRING_MATERIAL_BUILD_PASS " + json.dumps(report))
    return mat


if __name__ == "__main__":
    build_material()
