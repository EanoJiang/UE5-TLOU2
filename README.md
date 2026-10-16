# 艾莉巡逻服装规范交付

新增截帧发型 Groom：52,954 根真实 Strands，按厚发束、细发、碎发、湿发分成四组。毛发已作为 `BP_ElliePatrolCharacter` 的 `Groom_Hair` 默认组件，挂接 `SKC_HeadFace/headb`，新建角色实例会自带毛发。使用 [打开 Groom 近景](Open_Groom_UE58.cmd) / [运行 Groom 近景](Play_Groom_UE58.cmd)，或加载 `/Game/TLOU2/Maps/ElliePatrolCaptureGroom`。详情及验证见 [Groom 交付说明](Exports/Groom/README.md)。

**角色规范版本：29 网格 / 84,954 分配顶点 / 117,459 三角形 / 1,152 骨骼。** UE运行时：通过（最新运行时数值报告）；原始FG展台：通过（33个原始FG网格、截帧矩阵与UE持久化）。
原始shader权重参考最大位置误差 0.067583 mm；阈值 0.1 mm。

用 [TLOU2Codex.uproject](TLOU2Codex.uproject) 在 `D:/EpicGame/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe` 打开工程，加载 `/Game/TLOU2/Maps/ElliePatrolCaptureGroom` 后运行。场景使用真实3D角色、展台与HUD；原始截帧仅作参考证据。

快捷启动：[打开编辑器](Open_Catalog_UE58.cmd) / [直接运行图鉴](Play_Catalog_UE58.cmd)。工程已包含匹配UE5.8的运行时模块。

| 用途 | Blender | FBX | glTF / GLB |
|---|---|---|---|
| 绑定参考姿态 / 中性模型 | [源文件](Blender/Ellie_Patrol_Catalog_CaptureMatched.blend) | [FBX](Exports/Ellie_Patrol_Catalog_CaptureMatched.fbx) | [GLB](Exports/Ellie_Patrol_Catalog_CaptureMatched.glb) / [glTF JSON + BIN](Exports/Ellie_Patrol_Catalog_CaptureMatched.gltf) |
| 截帧静态姿态 | [源文件](Blender/Ellie_Patrol_CapturedSkinPose.blend) | [FBX](Exports/Ellie_Patrol_CapturedSkinPose.fbx) | [GLB](Exports/Ellie_Patrol_CapturedSkinPose.glb) / [glTF JSON + BIN](Exports/Ellie_Patrol_CapturedSkinPose.gltf) |
| 原始图鉴姿态 | [源文件](Blender/Ellie16_Patrol_OriginalViewerPose.blend) | [FBX](Exports/Ellie16_Patrol_OriginalViewerPose.fbx) | [GLB](Exports/Ellie16_Patrol_OriginalViewerPose.glb) / [glTF JSON + BIN](Exports/Ellie16_Patrol_OriginalViewerPose.gltf) |
| 原始0FW动画 | [源文件](Blender/Ellie_Patrol_Original_0FW.blend) | [FBX](Exports/Ellie_Patrol_Original_0FW.fbx) | [GLB](Exports/Ellie_Patrol_Original_0FW.glb) / [glTF JSON + BIN](Exports/Ellie_Patrol_Original_0FW.gltf) |

绑定与动画说明：中性文件用于原始A形参考绑定编辑；截帧文件用于静态图鉴复刻；原始图鉴与0FW动画保持各自数值来源。1,074人类节点+78帽衫节点组成规范骨架，UE另含1个导出对象根节点。Blender源文件为5.2格式，请使用Blender5.2或更新版本。

84,954为原始顶点缓冲分配数，其中592个头部位置没有被三角索引引用；可绘制参考为84,362。截帧GLB有85088个顶点，含UV/属性边界的拆分或合并，不要求与原始缓冲分配数相同。

117,459个原始三角形的29份有序索引缓冲已在444次实际DrawIndexed中逐位匹配。FG地台另含33网格、101,538分配顶点、27材质与206条原始解码贴图；已使用其独立16节点蒙皮与实际图形实例矩阵，世界坐标烘焙后以单位变换导入。

地台独立交换文件：[Blender](Blender/Catalog_CapturedFGStage.blend) / [FBX](Exports/Catalog_CapturedFGStage.fbx) / [GLB](Exports/Catalog_CapturedFGStage.glb)。FBX与GLB往返均保留124,086三角形及其绕序/重复次数。JSON glTF与同名BIN须一同保留。

## 轨迹、贴图与预览

- [Ellie_Patrol_CapturedSkinPose_RootTrajectory.csv](Exports/Ellie_Patrol_CapturedSkinPose_RootTrajectory.csv)：1样本，最大根位移 0 m。
- [Ellie16_Patrol_OriginalViewerPose_RootTrajectory.csv](Exports/Ellie16_Patrol_OriginalViewerPose_RootTrajectory.csv)：1样本，最大根位移 0 m。
- [Ellie_Patrol_Original_0FW_RootTrajectory.csv](Exports/Ellie_Patrol_Original_0FW_RootTrajectory.csv)：80样本，最大根位移 0 m。
- [Ellie_Patrol_CapturedSkinPose_RootMotion_GameSpace.csv](Exports/Ellie_Patrol_CapturedSkinPose_RootMotion_GameSpace.csv)：游戏坐标Y-up完整T/Q/S与相对首帧增量，1样本，根位移和旋转均为零。
- [Ellie16_Patrol_OriginalViewerPose_RootMotion_GameSpace.csv](Exports/Ellie16_Patrol_OriginalViewerPose_RootMotion_GameSpace.csv)：游戏坐标Y-up完整T/Q/S与相对首帧增量，1样本，根位移和旋转均为零。
- [Ellie_Patrol_Original_0FW_RootMotion_GameSpace.csv](Exports/Ellie_Patrol_Original_0FW_RootMotion_GameSpace.csv)：游戏坐标Y-up完整T/Q/S与相对首帧增量，80样本，根位移和旋转均为零。
- 旧 `RootTrajectory.csv` 使用Blender坐标；新增 `RootMotion_GameSpace.csv` 使用原始游戏X右/Y上/Z前坐标。原始命名root靠近骨盆，其参考高度不代表移动；UE导出对象根也保持静止。
- [340条原始解码贴图清单](Exports/TexturesDecoded/texture_decode_manifest.json)；PNG位于 `Exports/TexturesDecoded`，派生眼球/法线图片另行标注。
- [中性模型预览 PNG](Exports/Ellie_Patrol_NeutralModel_Preview.png)：Blender参考绑定姿态。
- [截帧姿态模型预览 PNG](Exports/Ellie_Patrol_CapturedSkinPose_Preview.png)：Blender原始相机预览，外观仍含材质近似。
- [UE实际RHI截图 PNG](Exports/Ellie_Patrol_UE_Runtime.png)：通过（最新运行时数值报告）；文件存在不等于外观或数值验证通过。
- [0FW动画预览 PNG](Exports/Ellie_Patrol_Original0FW_Preview.png)：原始稀疏动画层。
- [原始0FW动画预览 GIF](Exports/Ellie_Patrol_Original0FW_AnimationPreview.gif)：全部80源帧；GIF以30/40ms帧延时分布近似30Hz，配套报告记录逐帧时间。

操作：鼠标左键拖动旋转；W/A/S/D平移；Z/X或滚轮缩放；Q/E最近/最远；R复位；F显隐UI；Esc退出。

## 验证与来源

- [验证报告](Content/TLOU2/Reports/VALIDATION_REPORT.md)、[材质映射](Content/TLOU2/Reports/MATERIAL_MAPPING_FINAL.md)。
- [原始PAK与GPU记录逐网格匹配](Content/TLOU2/Reports/CAPTURE_MESH_SOURCE_BINDING_VALIDATION.md)。原始角色PAK保存在 `Content/TLOU2/SourcePaks`；原始动画数值与负载保存在 `Exports/AnimationSources/DecodedOriginal`。
- [截帧shader与蒙皮分析](Content/TLOU2/Reports/CAPTURE_SHADER_SKINNING.md)；331个shader与57个根签名容器/反汇编位于 `Exports/CaptureBuffers/Shaders`。
- [原始相机证据](Content/TLOU2/Reports/CAPTURE_ORIGINAL_CAMERA_CONSTANTS.md)：game Y-up位置(0,1.15,3)m，水平FOV79.9908974°；UE位置(0,300,115)cm，俯角10.431785°。
- [原始FG地台与遮罩证据](Content/TLOU2/Reports/CAPTURE_FG_STAGE_VALIDATION.md)；蕨叶与苔藓使用源深度预通道独立R遮罩，UE保留原始距离阈值公式。地面多层材质仍为PBR近似。
- [规范文件SHA-256清单](Content/TLOU2/Reports/FINAL_DELIVERY_MANIFEST.json)；仅涵盖规范资产，不包含多GB截帧页缓存/历史试验。

## 范围与限制

- 未知参考绑定：人类1074节点中520条原始SQT已恢复，554条helper参考仍明确标注为未解析；帽衫另有75条原始SQT与3条helper回退。截帧蒙皮矩阵是独立证据，不将其冒称为原始helper绑定姿态。
- 截帧是单个静态状态；CaptureAffineCorrective只补偿该状态中骨骼TRS无法表达的仿射剪切。原始0FW/图鉴姿态不使用这项截帧专用修正。
- 帽衫20个sim节点保留，但只有本截帧的静态布料矩阵；没有宣称恢复动态布料模拟或为稀疏0FW补造模拟动画。
- 眼球UV缩放3.2为推定参数；头发使用可移植PBR/遮罩，泪膜使用透明度.08/粗糙度.12；原始纤维光学、角膜折射、皮肤SSS与分层湿润shader没有完整移植。
- 原始NPZ没有提供独立的顶点法线/切线；Blender拆分法线与导出的body切线属于重建的DCC着色基底，保留它们不代表已逐位恢复原始GPU法线/切线或法线图绿色通道方向。位置、权重与拓扑验证不涵盖该基底。
- 0FW是26骨骼右臂/手指稀疏动画层，不是整段角色移动；图鉴源为1帧，UE两帧保持仅为兼容零时长导入。两者及截帧姿态的RootMotion位移为零。
- 实际UE运行时数值验证与外观比对独立于文件存在性；未通过的最新报告保持待完成状态，截图文件本身不构成通过证据。

旧 Exact、1074/1390 骨架、RawRootCandidate、Probe、Proxy、synthetic/root-motion测试与旧组合展台均为历史调试记录，已被本索引取代，不属于规范交付入口。
