# 复刻截帧角色头发 Groom

Session ID: 01a1441b-c479-71c0-9f9c-d7d9bea0ba2b

## User

用groom做角色毛发复刻"D:\Unpack_3A\TLOU2\Captures\NsightCapturesRetry2\tlou-ii_2026_10_16_01_55_52.ngfx-capture"截帧文件中的角色头发

## Codex

我会先检查截帧里能提取的头发数据，以及 UE 工程现有的角色和 Groom 资源，确定复刻对象和可直接复用的内容。

## Codex

我会用 brainstorming 技能先梳理现有资源与复刻路线，并并行检查截帧导出和 UE 导入流程。目标是把这帧中的发型做成可在工程里查看、调整的 Groom 资产，并用实际渲染核对轮廓。

## Codex

已确认复刻对象是巡逻服艾莉，工程里已有与这帧匹配的头部、头发网格和原始贴图。现有头发是发片；我会沿发片的 UV 和透明度纹理重建发丝曲线，保留刘海、束发和碎发的空间走向，再导入 UE Groom。单帧无法恢复原版完整毛发模拟，这次先完成截帧姿态下的发型与材质。

## Codex

重建曲线和 UE 导入正在并行进行。导入时会重点检查 Alembic 的坐标轴与厘米单位，避免头发旋转或缩放错误；结果会放进独立 Groom 场景，方便与现有发片版本比较。

## Codex

曲线会按厚发束、细发、碎发和湿发分组，保留原始发型的层次。接下来会检查 UE 保存并重新加载后是否仍使用真实 Strands、是否落在正确头部位置，再看正面、侧后方的实际渲染。

## Codex

已生成 52,954 根发丝、约 127 万个曲线点，坐标范围与原角色头部一致，发丝直径约 0.043–0.08 毫米。现在正在处理 UE 的毛发分组元数据并导入；下一步的渲染检查会确认这些曲线是否呈现出预期的发型和密度。

## Codex

导入前检查发现 Alembic 中有重复曲线，分组信息也需要转成 UE 可识别的格式。我正在清理已确认重复的数据并核对总数，避免影响毛发密度。原始几何和可编辑 Blender 文件都已保留。

## Codex

UE 已识别出四组 Groom，共 52,954 根发丝。引擎构建时会为每根曲线增加一个末端控制点，这是正常行为，已与源数据点数分开记录。接下来会完成场景替换并检查实际渲染，确认刘海、发际线和后部束发的效果。

## Codex

正面实际渲染已出图，Groom 与头部对齐，刘海和鬓角轮廓能正确呈现。头顶高光目前偏亮、偏宽，我会调整毛发粗糙度和高光强度，再核对侧后视角。

## Codex

Groom 资产和独立场景已保存，并通过重新加载检查。我正在重拍调整高光后的预览，同时核验游戏运行时原发片确实隐藏，画面使用的是 Groom。当前已打开的编辑器出现毛发资源未刷新的现象，新启动的渲染进程能正常显示，我也在处理这个刷新问题。

## Codex

调整高光后，正面和侧面的白亮条带已减弱，后脑束发与碎发也已出图。运行时检查确认原发片保持隐藏、Groom Strands 正常显示；当前编辑器的毛发刷新问题也已解决。最后在核对完整展台预览和交付文件。

## Codex

已完成艾莉该截帧的 **UE 5.8 Groom 重建**：52,954 根发丝、4 个分组，已通过保存重载、运行时及三视角渲染检查。

- [运行查看](D:/TLOU2_UE5_8_Codex/Play_Groom_UE58.cmd)
- [Groom Alembic](D:/TLOU2_UE5_8_Codex/Exports/Groom/Ellie_Patrol_CaptureGroom_Grouped.abc)
- [可编辑 Blender 源文件](D:/TLOU2_UE5_8_Codex/Blender/Ellie_Patrol_CaptureGroom.blend)
- [说明与验证](D:/TLOU2_UE5_8_Codex/Exports/Groom/README.md)

当前为截帧静态版本，动态绑定和模拟尚未配置。

![UE 实际渲染](D:/TLOU2_UE5_8_Codex/Exports/Groom/Ellie_Groom_UE_Front.png)

## User

Groom毛发绑定到角色的蓝图中，而不是在场景中单独一个实例

## Codex

我会把 Groom 组件直接加入角色蓝图，移除场景中的独立 Groom 实例，并验证运行时头发跟随角色。

## Codex

这是对现有角色蓝图的组件调整，我会按 brainstorming 技能先核对组件层级和坐标。Groom 将成为蓝图的默认组件，新拖入的角色也会自带毛发；同时检查头部挂接，避免移动或转头时脱离。

## Codex

已确认角色头骨是 `headb`。它的缩放约为 100，需要补偿坐标和缩放，才能保持当前发型的位置与大小。也已验证旧蓝图新建实例时没有 Groom 组件，接下来会修正蓝图默认组件，并清理五个相关场景中的独立毛发实例。

## Codex

检查时发现旧的 `ElliePatrolCaptureMatched` 场景文件已不存在，工程目前保留四个 Groom 场景。我会清理这四个场景，并将仍指向旧场景的启动入口改到有效场景。

## Codex

`Groom_Hair` 已保存为角色蓝图的默认组件，挂接到 `SKC_HeadFace/headb`；四个场景中的独立 Groom 实例已删除。原有网格和动画设置已核对保留。现在正在用新进程验证新建蓝图实例、移动旋转跟随，以及实际渲染对齐。

## Codex

蓝图新建实例和移动测试已通过，但实际渲染发现 Groom 直接挂在骨骼组件下时，引擎重复应用了导入骨架的缩放，导致毛发放大。我会增加一个头部锚点组件，让它负责跟随头骨，再把 Groom 放在锚点下，并重新检查渲染。

## Codex

锚点方案已通过实际渲染检查，毛发的位置和大小恢复正常。新建蓝图实例、角色移动旋转、头部挂接及四个场景的独立实例清理检查均已通过。最后正在保存验证记录，并打开角色蓝图供你查看组件层级。

## Codex

## 当前进度

- 已将 Groom 从场景独立实例改为角色蓝图默认组件。
- 蓝图：`/Game/TLOU2/Blueprints/BP_ElliePatrolCharacter`
- 组件层级：

  `SKC_HeadFace/headb → SC_GroomHeadAnchor → Groom_Hair`

- `SC_GroomHeadAnchor` 使用 `headb` 的逆变换补偿骨架缩放；`Groom_Hair` 使用单位变换。
- Groom 使用真实 Strands，4 组共 **52,954 根曲线**。
- `BindingAsset=None`、无动态模拟、`use_cards=false`，属于静态刚性头部挂接。
- 原 `SKC_Hair` 和 `SKC_Accessories` 已在蓝图默认状态隐藏。
- 四个 Groom 场景中的独立 `GroomActor` 已移除并保存。
- 原角色网格、AnimClass、动画设置均通过前后对比验证保持不变。
- 默认启动地图已改为有效的 `/Game/TLOU2/Maps/ElliePatrolCaptureGroom`，因为旧的 `ElliePatrolCaptureMatched.umap` 文件已不存在。

## 验证结果

- 新建蓝图实例自动拥有 Groom。
- 角色平移、旋转、头部组件移动均能带动 Groom。
- 四个地图均无独立 GroomActor。
- 实际 RHI 正面、三分之四、背面和全身预览均已生成；锚点修复后毛发尺寸和位置正常。
- 关键报告：

  - `D:/TLOU2_UE5_8_Codex/Exports/Groom/BlueprintIntegration/saved_blueprint_validation.json`
  - `D:/TLOU2_UE5_8_Codex/Exports/Groom/BlueprintIntegration/integration_result.json`
  - `D:/TLOU2_UE5_8_Codex/Exports/Groom/runtime_audit_ElliePatrolCaptureGroomFront.json`
  - `D:/TLOU2_UE5_8_Codex/Exports/Groom/saved_asset_validation.json`
  - `D:/TLOU2_UE5_8_Codex/Exports/Groom/DELIVERY_MANIFEST.json`

## 重要资产

- Groom：`/Game/TLOU2/Groom/Ellie_Patrol_CaptureGroom`
- 可编辑 Blender 源文件：[Ellie_Patrol_CaptureGroom.blend](/D:/TLOU2_UE5_8_Codex/Blender/Ellie_Patrol_CaptureGroom.blend)
- Groom Alembic：[Ellie_Patrol_CaptureGroom_Grouped.abc](/D:/TLOU2_UE5_8_Codex/Exports/Groom/Ellie_Patrol_CaptureGroom_Grouped.abc)
- 蓝图编辑器已通过 MCP 打开，确认资产路径为 `BP_ElliePatrolCharacter`。
- 最新正面渲染：[Ellie_Groom_UE_Front.png](/D:/TLOU2_UE5_8_Codex/Exports/Groom/Ellie_Groom_UE_Front.png)

## 约束

- Groom 是由截帧中的原始发片、UV 和透明度重建的静态曲线，不是原始作者 Groom 曲线的恢复。
- 未启用表面 Skinning Binding 或动态毛发模拟。
- 原始截帧主要提供正面视角，背面只做发型结构合理性检查。

## Codex

我已按“角色蓝图组件”方式完成绑定；现在做最后一次文件与运行时审计，确认场景里没有遗留独立 GroomActor。

