#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "GroomBlueprintEditorLibrary.generated.h"

class UBlueprint;
class USceneComponent;

/** Editor scripting bridge for a component's serialized SCS socket. */
UCLASS()
class TLOU2CODEX_API UGroomBlueprintEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Editor Scripting|Groom")
    static bool SetBlueprintComponentSocket(UBlueprint* Blueprint,
        USceneComponent* ComponentTemplate, FName SocketName);

    UFUNCTION(BlueprintPure, Category="Editor Scripting|Groom")
    static FString DescribeBlueprintComponentAttachment(UBlueprint* Blueprint,
        USceneComponent* ComponentTemplate);
};
