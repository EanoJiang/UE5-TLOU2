param([int]$DelaySeconds = 15)
$ErrorActionPreference = 'Stop'
$drawstringRoot = 'D:\TLOU2_UE5_8_Codex'
$drawstringOut = Join-Path $drawstringRoot 'Exports\Drawstring'
$drawstringEngine = 'D:\EpicGame\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$drawstringArgs = @(
    ('"' + (Join-Path $drawstringRoot 'TLOU2Codex.uproject') + '"'),
    '/Game/TLOU2/Maps/ElliePatrolCaptureGroomFront',
    '-game', '-windowed', '-ResX=1600', '-ResY=1200', '-ForceRes',
    '-unattended', '-nosplash', '-nop4', '-nosound',
    '-ExecCmds="py D:/TLOU2_UE5_8_Codex/Scripts/drawstring_runtime_audit_ue.py"',
    ('-CatalogCapture="' + (Join-Path $drawstringOut 'UE_Drawstrings_Closeup.png') + '"'),
    ('-CatalogCaptureDelay=' + $DelaySeconds),
    ('-abslog="' + (Join-Path $drawstringOut 'ue_runtime.log') + '"')
)
$drawstringProcess = Start-Process -FilePath $drawstringEngine -ArgumentList $drawstringArgs -WindowStyle Hidden -PassThru
[pscustomobject]@{ProcessId=$drawstringProcess.Id; Image=(Join-Path $drawstringOut 'UE_Drawstrings_Closeup.png'); Log=(Join-Path $drawstringOut 'ue_runtime.log')} | ConvertTo-Json
