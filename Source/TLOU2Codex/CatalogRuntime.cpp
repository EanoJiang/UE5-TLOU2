#include "CatalogRuntime.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Texture2D.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetSystemLibrary.h"
#include "UObject/ConstructorHelpers.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Animation/SkeletalMeshActor.h"
#include "Animation/MorphTarget.h"
#include "SkeletalRenderPublic.h"
#include "Rendering/SkinWeightVertexBuffer.h"
#include "Rendering/SkeletalMeshRenderData.h"
#include "Rendering/SkeletalMeshLODRenderData.h"
#include "Misc/FileHelper.h"
#include "HAL/FileManager.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Camera/PlayerCameraManager.h"

namespace
{
TArray<TSharedPtr<FJsonValue>> JsonVector(const FVector& V)
{
    return {MakeShared<FJsonValueNumber>(V.X), MakeShared<FJsonValueNumber>(V.Y), MakeShared<FJsonValueNumber>(V.Z)};
}

void ApplyCatalogAffineCorrectives(UWorld* World)
{
    for (TActorIterator<ASkeletalMeshActor> It(World); It; ++It)
    {
        if (!It->ActorHasTag(TEXT("CaptureAffineCorrective"))) continue;
        USkeletalMeshComponent* Component = It->GetSkeletalMeshComponent();
        if (!Component || !Component->GetSkeletalMeshAsset()) continue;
        for (UMorphTarget* Morph : Component->GetSkeletalMeshAsset()->GetMorphTargets())
        {
            if (Morph && Morph->GetName().Contains(TEXT("CaptureAffineCorrective")))
                Component->SetMorphTarget(Morph->GetFName(), 1.0f);
        }
    }
}

void WriteCatalogVertexAudit(UWorld* World)
{
    FString Directory;
    if (!FParse::Value(FCommandLine::Get(), TEXT("CatalogVertexDump="), Directory)) return;
    IFileManager::Get().MakeDirectory(*Directory, true);
    TArray<TSharedPtr<FJsonValue>> Rows;
    int64 CharacterIndexCount = 0;
    int64 CharacterTriangleCount = 0;
    int32 CharacterChunkCount = 0;
    for (TActorIterator<ASkeletalMeshActor> It(World); It; ++It)
    {
        USkeletalMeshComponent* Component = It->GetSkeletalMeshComponent();
        USkeletalMesh* Mesh = Component ? Component->GetSkeletalMeshAsset() : nullptr;
        if (!Mesh) continue;
        TArray<FFinalSkinVertex> Vertices;
        Component->GetCPUSkinnedVertices(Vertices, 0);
        TArray<uint8> Bytes;
        Bytes.SetNumUninitialized(Vertices.Num() * 3 * sizeof(float));
        float* Output = reinterpret_cast<float*>(Bytes.GetData());
        for (const FFinalSkinVertex& Vertex : Vertices)
        {
            *Output++ = Vertex.Position.X;
            *Output++ = Vertex.Position.Y;
            *Output++ = Vertex.Position.Z;
        }
        const FString File = FPaths::Combine(Directory, Mesh->GetName() + TEXT(".positions.f32"));
        FFileHelper::SaveArrayToFile(Bytes, *File);
        TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
        Row->SetStringField(TEXT("actor"), It->GetPathName());
        Row->SetStringField(TEXT("mesh"), Mesh->GetPathName());
        Row->SetStringField(TEXT("positions"), File);
        Row->SetNumberField(TEXT("vertices"), Vertices.Num());
        int32 IndexCount = 0;
        int64 SectionTriangleCount = 0;
        if (const FSkeletalMeshRenderData* RenderData = Mesh->GetResourceForRendering())
        {
            if (RenderData->LODRenderData.IsValidIndex(0))
            {
                const FSkeletalMeshLODRenderData& LOD = RenderData->LODRenderData[0];
                if (LOD.MultiSizeIndexContainer.IsIndexBufferValid())
                    IndexCount = LOD.MultiSizeIndexContainer.GetIndexBuffer()->Num();
                for (const FSkelMeshRenderSection& Section : LOD.RenderSections)
                    SectionTriangleCount += Section.NumTriangles;
            }
        }
        Row->SetNumberField(TEXT("lod"), 0);
        Row->SetNumberField(TEXT("index_count"), IndexCount);
        Row->SetNumberField(TEXT("triangles"), IndexCount / 3);
        Row->SetNumberField(TEXT("render_section_triangles"), SectionTriangleCount);
        if (Mesh->GetPathName().StartsWith(TEXT("/Game/TLOU2/CaptureMatched1152/CapturedMeshes/")))
        {
            CharacterIndexCount += IndexCount;
            CharacterTriangleCount += IndexCount / 3;
            ++CharacterChunkCount;
        }
        Row->SetStringField(TEXT("space"), TEXT("component local, UE centimeters, little-endian float32 XYZ"));
        Row->SetStringField(TEXT("component_world_transform"), Component->GetComponentTransform().ToString());
        Row->SetArrayField(TEXT("component_location_cm"), JsonVector(Component->GetComponentLocation()));
        Row->SetArrayField(TEXT("component_rotation_degrees"), JsonVector(FVector(Component->GetComponentRotation().Pitch, Component->GetComponentRotation().Yaw, Component->GetComponentRotation().Roll)));
        Row->SetArrayField(TEXT("component_scale"), JsonVector(Component->GetComponentScale()));
        if (FSkinWeightVertexBuffer* Weights = Component->GetSkinWeightBuffer(0))
            Row->SetNumberField(TEXT("maximum_bone_influences"), Weights->GetMaxBoneInfluences());
        TSharedPtr<FJsonObject> Morphs = MakeShared<FJsonObject>();
        for (UMorphTarget* Morph : Mesh->GetMorphTargets())
        {
            if (Morph) Morphs->SetNumberField(Morph->GetName(), Component->GetMorphTarget(Morph->GetFName()));
        }
        Row->SetObjectField(TEXT("morphs"), Morphs);
        Rows.Add(MakeShared<FJsonValueObject>(Row));
    }
    TSharedPtr<FJsonObject> Document = MakeShared<FJsonObject>();
    Document->SetArrayField(TEXT("meshes"), Rows);
    Document->SetNumberField(TEXT("character_index_count"), CharacterIndexCount);
    Document->SetNumberField(TEXT("character_triangles"), CharacterTriangleCount);
    Document->SetNumberField(TEXT("character_chunk_count"), CharacterChunkCount);
    Document->SetStringField(TEXT("method"), TEXT("UE GetCPUSkinnedVertices LOD0 including enabled morph targets; render thread flushed."));
    if (APlayerController* PC = World->GetFirstPlayerController())
    {
        FVector Location;
        FRotator Rotation;
        PC->GetPlayerViewPoint(Location, Rotation);
        Document->SetArrayField(TEXT("camera_location_cm"), JsonVector(Location));
        Document->SetArrayField(TEXT("camera_forward"), JsonVector(Rotation.Vector()));
        if (PC->PlayerCameraManager) Document->SetNumberField(TEXT("camera_horizontal_fov_degrees"), PC->PlayerCameraManager->GetFOVAngle());
    }
    FString Json;
    FJsonSerializer::Serialize(Document.ToSharedRef(), TJsonWriterFactory<>::Create(&Json));
    FFileHelper::SaveStringToFile(Json, *FPaths::Combine(Directory, TEXT("ue_runtime_vertex_dump.json")));
    UE_LOG(LogTemp, Display, TEXT("CATALOG_VERTEX_AUDIT %d meshes %s"), Rows.Num(), *Directory);
}
}

ACatalogPawn::ACatalogPawn()
{
    PrimaryActorTick.bCanEverTick = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("CatalogRoot"));
    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("CatalogCamera"));
    Camera->SetupAttachment(RootComponent);
    Camera->FieldOfView = 35;
    AutoPossessPlayer = EAutoReceiveInput::Player0;
    UpdateCamera();
}

void ACatalogPawn::BeginPlay()
{
    Super::BeginPlay();
    FParse::Value(FCommandLine::Get(), TEXT("CatalogCapture="), CaptureOutputPath);
    FParse::Value(FCommandLine::Get(), TEXT("CatalogCaptureDelay="), CaptureDelay);
    ApplyCatalogAffineCorrectives(GetWorld());
    ACameraActor* PlacedCamera = nullptr;
    for (TActorIterator<ACameraActor> It(GetWorld()); It; ++It)
    {
        if (!PlacedCamera || It->ActorHasTag(TEXT("CatalogCamera")))
        {
            PlacedCamera = *It;
            if (It->ActorHasTag(TEXT("CatalogCamera"))) break;
        }
    }
    if (PlacedCamera)
    {
        const FVector Direction = PlacedCamera->GetActorForwardVector();
        Radius = InitialRadius = 340;
        Pivot = InitialPivot = PlacedCamera->GetActorLocation() + Direction * Radius;
        const FRotator Away = (-Direction).Rotation();
        Yaw = InitialYaw = Away.Yaw;
        Pitch = InitialPitch = Away.Pitch;
        Camera->FieldOfView = PlacedCamera->GetCameraComponent()->FieldOfView;
    }
    ResetCatalogView();
    if (APlayerController* PC = Cast<APlayerController>(GetController()))
    {
        FInputModeGameOnly InputMode;
        InputMode.SetConsumeCaptureMouseDown(false);
        PC->SetInputMode(InputMode);
        PC->bShowMouseCursor = false;
        PC->SetViewTarget(this);
    }
}

void ACatalogPawn::UpdateCamera()
{
    const FVector Away = FRotator(Pitch, Yaw, 0).Vector();
    const FVector Location = Pivot + Away * Radius;
    Camera->SetWorldLocationAndRotation(Location, (Pivot - Location).Rotation());
}

void ACatalogPawn::ResetCatalogView()
{
    Pivot = InitialPivot;
    Radius = InitialRadius;
    Yaw = InitialYaw;
    Pitch = InitialPitch;
    UpdateCamera();
}

void ACatalogPawn::OrbitCatalogView(float YawDegrees, float PitchDegrees)
{
    Yaw = FMath::UnwindDegrees(Yaw + YawDegrees);
    Pitch = FMath::Clamp(Pitch + PitchDegrees, -80.0, 80.0);
    UpdateCamera();
}

void ACatalogPawn::PanCatalogView(float RightCentimeters, float UpCentimeters)
{
    Pivot += Camera->GetRightVector() * RightCentimeters + Camera->GetUpVector() * UpCentimeters;
    UpdateCamera();
}

void ACatalogPawn::ZoomCatalogView(float LogDistanceDelta)
{
    // Clamp the exponent as well as the result so extreme input stays finite.
    Radius = FMath::Clamp(Radius * FMath::Exp(FMath::Clamp(double(LogDistanceDelta), -20.0, 20.0)), 70.0, 800.0);
    UpdateCamera();
}

void ACatalogPawn::ToggleCatalogMenu() { bMenuVisible = !bMenuVisible; }
FVector ACatalogPawn::GetCatalogCameraLocation() const { return Camera->GetComponentLocation(); }

void ACatalogPawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!CaptureOutputPath.IsEmpty())
    {
        CaptureElapsed += DeltaSeconds;
        if (!bCaptureRequested && CaptureElapsed >= CaptureDelay)
        {
            WriteCatalogVertexAudit(GetWorld());
            FScreenshotRequest::RequestScreenshot(CaptureOutputPath, true, false);
            bCaptureRequested = true;
            UE_LOG(LogTemp, Display, TEXT("CATALOG_CAPTURE_REQUEST %s"), *CaptureOutputPath);
        }
        if (bCaptureRequested && CaptureElapsed >= CaptureDelay + 3.0)
        {
            const bool bSaved = FPaths::FileExists(CaptureOutputPath);
            UE_LOG(LogTemp, Display, TEXT("CATALOG_CAPTURE_SAVED %d %s"), bSaved, *CaptureOutputPath);
            FPlatformMisc::RequestExit(false);
        }
    }
    APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC) return;
    const auto Pressed = [PC](FKey Key) { return PC->WasInputKeyJustPressed(Key); };
    const auto Down = [PC](FKey Key) { return PC->IsInputKeyDown(Key) ? 1.0f : 0.0f; };
    if (Pressed(EKeys::R)) ResetCatalogView();
    if (Pressed(EKeys::F)) ToggleCatalogMenu();
    if (Pressed(EKeys::Q)) { Radius = 70; UpdateCamera(); }
    if (Pressed(EKeys::E)) { Radius = 800; UpdateCamera(); }
    if (Pressed(EKeys::Escape)) UKismetSystemLibrary::QuitGame(this, PC, EQuitPreference::Quit, false);
    const float PanSpeed = float(Radius) * 0.3f * DeltaSeconds;
    const float Right = Down(EKeys::D) - Down(EKeys::A);
    const float Up = Down(EKeys::W) - Down(EKeys::S);
    if (Right != 0 || Up != 0) PanCatalogView(Right * PanSpeed, Up * PanSpeed);
    const float Zoom = Down(EKeys::X) - Down(EKeys::Z);
    if (Zoom != 0) ZoomCatalogView(Zoom * DeltaSeconds);
    if (Pressed(EKeys::MouseScrollUp)) ZoomCatalogView(-0.1f);
    if (Pressed(EKeys::MouseScrollDown)) ZoomCatalogView(0.1f);
    if (PC->IsInputKeyDown(EKeys::LeftMouseButton))
    {
        float X = 0, Y = 0;
        PC->GetInputMouseDelta(X, Y);
        if (X != 0 || Y != 0) OrbitCatalogView(X * 0.25f, Y * 0.25f);
    }
}

ACatalogHUD::ACatalogHUD()
{
    static ConstructorHelpers::FObjectFinder<UTexture2D> Texture(TEXT("/Game/TLOU2/Reference/T_CatalogInstructionBar.T_CatalogInstructionBar"));
    if (Texture.Succeeded()) Instructions = Texture.Object;
}

void ACatalogHUD::DrawHUD()
{
    Super::DrawHUD();
    const ACatalogPawn* Pawn = PlayerOwner ? Cast<ACatalogPawn>(PlayerOwner->GetPawn()) : nullptr;
    if (!Canvas || !Pawn || !Pawn->IsCatalogMenuVisible()) return;
    const float Width = Canvas->SizeX;
    const float Height = Width * (117.0f / 1920.0f);
    DrawRect(FLinearColor(0.025f,0.025f,0.025f,1), 0, Canvas->SizeY - Height, Width, Height);
    if (Instructions)
    {
        // The original extraction includes15pixels above the instruction bar.
        // Crop them in UV space so the HUD contains only its actual source UI.
        const float SourceHeight = Instructions->GetSizeY();
        const float VisibleHeight = FMath::Min(SourceHeight, 117.0f);
        const float TextureHeight = Width * VisibleHeight / Instructions->GetSizeX();
        DrawTexture(Instructions, 0, Canvas->SizeY - TextureHeight, Width, TextureHeight,
            0, (SourceHeight - VisibleHeight) / SourceHeight, 1, VisibleHeight / SourceHeight);
    }
    else
    {
        DrawText(TEXT("R Reset   WASD Move   Mouse Rotate   Z/X Zoom   Q/E Limits   F Hide   Esc Exit"), FLinearColor::White, Width * 0.12f, Canvas->SizeY - Height * 0.55f);
    }
}

ACatalogGameMode::ACatalogGameMode()
{
    DefaultPawnClass = ACatalogPawn::StaticClass();
    HUDClass = ACatalogHUD::StaticClass();
}
