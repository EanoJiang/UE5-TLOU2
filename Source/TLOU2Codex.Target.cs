using UnrealBuildTool;
using System.Collections.Generic;
public class TLOU2CodexTarget : TargetRules
{
    public TLOU2CodexTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("TLOU2Codex");
    }
}
