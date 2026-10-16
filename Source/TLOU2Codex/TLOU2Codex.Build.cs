using UnrealBuildTool;
public class TLOU2Codex : ModuleRules
{
    public TLOU2Codex(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "Json" });
    }
}
