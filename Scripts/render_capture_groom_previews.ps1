param(
    [ValidateSet('Overview','Front','ThreeQuarter','Back')]
    [string]$View = 'Front',
    [int]$DelaySeconds = 30
)
$ErrorActionPreference = 'Stop'
$projectRoot = 'D:\TLOU2_UE5_8_Codex'
$outputDir = Join-Path $projectRoot 'Exports\Groom'
$enginePath = 'D:\EpicGame\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$mapPath = '/Game/TLOU2/Maps/ElliePatrolCaptureGroom'
if ($View -ne 'Overview') { $mapPath += $View }
$imagePath = Join-Path $outputDir ('Ellie_Groom_UE_' + $View + '.png')
$logPath = Join-Path $outputDir ('render_' + $View + '.log')
$launchArgs = @(
    ('"' + (Join-Path $projectRoot 'TLOU2Codex.uproject') + '"'),
    $mapPath,
    '-game', '-windowed', '-ResX=1920', '-ResY=1080',
    '-ForceRes', '-unattended', '-nosplash', '-nop4', '-nosound',
    '-EnablePlugins=HairStrands,AlembicHairImporter',
    '-DisablePlugins=ModelContextProtocol',
    '-ExecCmds="py D:/TLOU2_UE5_8_Codex/Scripts/audit_capture_groom_runtime_ue.py"',
    ('-CatalogCapture="' + $imagePath + '"'),
    ('-CatalogCaptureDelay=' + $DelaySeconds),
    ('-abslog="' + $logPath + '"')
)
$captureProcess = Start-Process -FilePath $enginePath -ArgumentList $launchArgs -WindowStyle Hidden -PassThru
[pscustomobject]@{ProcessId=$captureProcess.Id; View=$View; Map=$mapPath; Image=$imagePath; Log=$logPath} | ConvertTo-Json
