#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/HUD.h"
#include "GameFramework/GameModeBase.h"
#include "CatalogRuntime.generated.h"

class UCameraComponent;
class UTexture2D;

UCLASS()
class TLOU2CODEX_API ACatalogPawn : public APawn
{
    GENERATED_BODY()
public:
    ACatalogPawn();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable) void ResetCatalogView();
    UFUNCTION(BlueprintCallable) void OrbitCatalogView(float YawDegrees, float PitchDegrees);
    UFUNCTION(BlueprintCallable) void PanCatalogView(float RightCentimeters, float UpCentimeters);
    UFUNCTION(BlueprintCallable) void ZoomCatalogView(float LogDistanceDelta);
    UFUNCTION(BlueprintCallable) void ToggleCatalogMenu();
    UFUNCTION(BlueprintPure) bool IsCatalogMenuVisible() const { return bMenuVisible; }
    UFUNCTION(BlueprintPure) double GetCatalogRadius() const { return Radius; }
    UFUNCTION(BlueprintPure) FVector GetCatalogPivot() const { return Pivot; }
    UFUNCTION(BlueprintPure) FVector GetCatalogCameraLocation() const;

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<UCameraComponent> Camera;
    FVector Pivot = FVector(0, 0, 90);
    FVector InitialPivot = FVector(0, 0, 90);
    double Radius = 340;
    double InitialRadius = 340;
    double Yaw = -65;
    double InitialYaw = -65;
    double Pitch = 10;
    double InitialPitch = 10;
    bool bMenuVisible = true;
    FString CaptureOutputPath;
    double CaptureDelay = 15.0;
    double CaptureElapsed = 0.0;
    bool bCaptureRequested = false;
    void UpdateCamera();
};

UCLASS()
class TLOU2CODEX_API ACatalogHUD : public AHUD
{
    GENERATED_BODY()
public:
    ACatalogHUD();
    virtual void DrawHUD() override;
private:
    UPROPERTY() TObjectPtr<UTexture2D> Instructions;
};

UCLASS()
class TLOU2CODEX_API ACatalogGameMode : public AGameModeBase
{
    GENERATED_BODY()
public:
    ACatalogGameMode();
};
