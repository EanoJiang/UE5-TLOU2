#include "GroomBlueprintEditorLibrary.h"

#if WITH_EDITOR
#include "Components/SceneComponent.h"
#include "Engine/Blueprint.h"
#include "Engine/SCS_Node.h"
#include "Engine/SimpleConstructionScript.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
USCS_Node* FindComponentNode(UBlueprint* Blueprint, USceneComponent* Component)
{
    if (!Blueprint || !Blueprint->SimpleConstructionScript || !Component)
        return nullptr;
    for (USCS_Node* Node : Blueprint->SimpleConstructionScript->GetAllNodes())
        if (Node && Node->ComponentTemplate == Component)
            return Node;
    return nullptr;
}
}
#endif

bool UGroomBlueprintEditorLibrary::SetBlueprintComponentSocket(UBlueprint* Blueprint,
    USceneComponent* ComponentTemplate, FName SocketName)
{
#if WITH_EDITOR
    USCS_Node* Node = FindComponentNode(Blueprint, ComponentTemplate);
    if (!Node)
        return false;
    Blueprint->Modify();
    Node->Modify();
    ComponentTemplate->Modify();
    Node->AttachToName = SocketName;
    ComponentTemplate->SetupAttachment(ComponentTemplate->GetAttachParent(), SocketName);
    Blueprint->MarkPackageDirty();
    return true;
#else
    return false;
#endif
}

FString UGroomBlueprintEditorLibrary::DescribeBlueprintComponentAttachment(UBlueprint* Blueprint,
    USceneComponent* ComponentTemplate)
{
#if WITH_EDITOR
    USCS_Node* Node = FindComponentNode(Blueprint, ComponentTemplate);
    if (!Node)
        return TEXT("{}");
    USCS_Node* Parent = Blueprint->SimpleConstructionScript->FindParentNode(Node);
    TSharedRef<FJsonObject> Json = MakeShared<FJsonObject>();
    Json->SetStringField(TEXT("path"), Node->GetPathName());
    Json->SetStringField(TEXT("attach_to_name"), Node->AttachToName.ToString());
    Json->SetStringField(TEXT("parent_node"), Parent ? Parent->GetPathName() : FString());
    Json->SetStringField(TEXT("parent_component"), Parent && Parent->ComponentTemplate
        ? Parent->ComponentTemplate->GetName() : FString());
    Json->SetBoolField(TEXT("is_scs_default"), true);
    FString Result;
    FJsonSerializer::Serialize(Json, TJsonWriterFactory<>::Create(&Result));
    return Result;
#else
    return TEXT("{}");
#endif
}
