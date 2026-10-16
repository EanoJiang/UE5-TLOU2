using UnrealBuildTool;
using System.Collections.Generic;
public class TLOU2CodexEditorTarget : TargetRules
{
    public TLOU2CodexEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("TLOU2Codex");
    }
}
