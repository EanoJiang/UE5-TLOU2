$py='D:\Unpack_3A\blender_portable\blender-4.5.10-windows-x64\4.5\python\bin\python.exe'
$script='D:\TLOU2_UE5_8_Codex\Scripts\decode_nd_anim_stream.py'
$out='D:\TLOU2_UE5_8_Codex\Exports\AnimationSources_redecode_all_20261016'
Remove-Item $out -Recurse -Force -ErrorAction SilentlyContinue
$inputs=@(
'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak',
'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-pat-hoodie.pak',
'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-movement.pak',
'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-mm-explore.pak',
'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-mm-tense.pak',
'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-gestures.pak',
'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm'
)
& $py $script @inputs --out $out
Write-Output "exit=$LASTEXITCODE"

