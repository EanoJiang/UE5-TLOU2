# Exact ND package conversion (run after fixing/enabling the Noesis Python bridge)
$noesis = 'D:\Unpack_3A\TLOU2\Tools\Noesis_x64test\Noesis64.exe'
$src = 'D:\Unpack_3A\TLOU2\Assets\tlou2_assets\actor97'
$out = 'D:\TLOU2_UE5_8_Codex\Exports\Exact'
New-Item -ItemType Directory -Force $out | Out-Null
$packages = @('ellie-skel','ellie16-patrol-body','ellie-patrol-jacket','ellie-patrol-hoodie-cloth','ellie-patrol-pants','ellie-patrol-boots','ellie-patrol-hair','ellie-patrol-hair-hood-up','ellie-patrol-l-glove','ellie-patrol-r-glove','ellie-patrol-l-bicep-bandage','ellie-patrol-r-forearm-bandage','backpack-ellie','ellie-head','ellie-arms')
foreach($name in $packages) {
  & $noesis '?cmode' "$src\$name.pak" "$out\$name.fbx" '-nodialog' '-lods'
}
