param([ValidateSet('Baseline','HeadHidden','HeadHiddenFinal','StringsHidden','Fixed')][string]$Mode='Baseline', [ValidateSet('Front','Left','Right')][string]$View='Front')
$ErrorActionPreference = 'Stop'
$hoodSeamOut = 'D:\TLOU2_UE5_8_Codex\Exports\HoodSeam'
$hoodSeamLabel = $Mode
if ($View -ne 'Front') { $hoodSeamLabel += '_'+$View }
New-Item -ItemType Directory -Path $hoodSeamOut -Force | Out-Null
$hoodSeamArgs = @('D:\TLOU2_UE5_8_Codex\TLOU2Codex.uproject', '/Game/TLOU2/Maps/ElliePatrolCaptureGroomFront',
    '-game','-windowed','-ResX=1600','-ResY=1200','-ForceRes','-unattended','-nosplash','-nop4','-nosound',
    '-ExecCmds="py D:/TLOU2_UE5_8_Codex/Scripts/hood_seam_runtime_probe_ue.py"',
    ('-HoodSeamMode='+$Mode), ('-HoodSeamView='+$View), ('-CatalogCapture="'+(Join-Path $hoodSeamOut ($hoodSeamLabel+'.png'))+'"'),
    '-CatalogCaptureDelay=7', ('-abslog="'+(Join-Path $hoodSeamOut ($hoodSeamLabel+'.log'))+'"'))
$hoodSeamProcess = Start-Process -FilePath 'D:\EpicGame\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe' -ArgumentList $hoodSeamArgs -WindowStyle Hidden -PassThru
[pscustomobject]@{ProcessId=$hoodSeamProcess.Id;Mode=$Mode} | ConvertTo-Json
