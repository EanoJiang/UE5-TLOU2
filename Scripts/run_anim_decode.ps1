$py='D:\Unpack_3A\blender_portable\blender-4.5.10-windows-x64\4.5\python\bin\python.exe'
$script='D:\TLOU2_UE5_8_Codex\Scripts\decode_nd_anim_stream.py'
$out='D:\TLOU2_UE5_8_Codex\Exports\AnimationSources'
Remove-Item $out -Recurse -Force -ErrorAction SilentlyContinue
& $py $script 'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-ellie-player-bindpose.pak' 'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97\anim-pat-hoodie.pak' 'D:\Unpack_3A\TLOU2\Assets\extracted_sp_common\animstream97\anim-dina-performances.dina-idle-performance-touch-belly.stm' --out $out
Write-Output "exit=$LASTEXITCODE"
Get-ChildItem $out -Recurse -File | Select-Object FullName,Length | Select-Object -First 30
Get-Content "$out\ANIMATION_DECODE_REPORT.md" -TotalCount 50
