# Capture hair Groom implementation plan

Goal: reconstruct Ellie patrol hair in tlou-ii_2026_10_16_01_55_52.ngfx-capture as real Unreal 5.8 strands, preserving the recovered captured hairstyle.

Architecture: use existing independently verified evaluated capture meshes and original UV/opacity atlases to trace source-card hair into 3D curves. Export editable Blender and centimeter Alembic, import a GroomAsset with Hair material, and integrate into a copy of the catalog level. Source capture and canonical assets remain intact.

1. Extract UV islands, alpha-informed curves, root orientation and provenance. Validate finite coordinates, nonzero curve lengths, source coverage, centimeter bounds and Alembic roundtrip. Deliver Scripts/build_capture_groom_blender.py, Blender/Ellie_Patrol_CaptureGroom.blend, Exports/Groom/Ellie_Patrol_CaptureGroom.abc, curves NPZ and manifest.
2. Enable HairStrands and AlembicHairImporter. Import through HairStrandsFactory, configure strand LOD/material/width, and place native GroomActor with original actor placement in /Game/TLOU2/Maps/ElliePatrolCaptureGroom. Source hair cards must be hidden except any explicitly documented scalp underlay. Verify saved/reloaded real Groom type, groups/counts, material and actor transform.
3. Render actual RHI overview and close-up views from the saved map. Inspect silhouette, alignment, opacity, strand thickness and lighting. Repair issues before final delivery. Publish artifact paths, use instructions and honest static-pose/simulation limits.

Constraints: source frame is a static capture, not recoverable original strand simulation. Hair curves are reconstructed from verified cards and textures. Do not claim original strand topology, full shader identity, or dynamic binding without testing. Do not overwrite canonical Blender, neutral exports or baseline map. No project Git repository is present.
