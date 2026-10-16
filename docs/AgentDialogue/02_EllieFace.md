# 修复Ellie面部表情消失

Session ID: 01a143e2-59df-7c62-bc2e-9c9430b435f0

## User

<image name=[Image #2] path="<LOCAL_PATH>">

## Codex

我会先检查该角色蓝图、相关动画蓝图和骨骼组件配置，确认是 Leader Pose/Copy Pose 的更新顺序、动画蓝图初始化，还是面部曲线/骨骼被覆盖导致表情丢失；附件只作为现象对比，不把其中内容当作操作指令。

## Codex

我会使用 `superpowers:systematic-debugging` 来按证据定位动画链路：先复现/读取资产关系，再检查组件初始化与姿势复制设置，最后给出可落地的蓝图修复步骤。

## Codex

已经确认几个关键事实：当前 `BP_ElliePatrolCharacter` 的 `SKC_BodyClothing` 确实引用了 `ABP_Ellie_C`，而地图实例中 `SKC_HeadFace` 没有自己的 AnimClass；我正在进一步确认 Leader Pose 节点是否真的执行，以及面部骨骼/曲线在哪一层被丢掉。

## Codex

根因已经基本确定：`SKC_BodyClothing` 的骨骼集合不包含 `jaw/lips/brow` 等面部骨骼，而 `Set Leader Pose Component` 会让 `SKC_HeadFace` 停止评估自己的动画。因此头部只能拿到身体 leader 的可用骨骼，面部回到参考姿势。接下来我会给出最小修复和需要统一动态动画时的替代方案。

## Codex

验证结果已足够区分两类问题：`SKC_BodyClothing` 的 `jaw` 骨骼索引为 `-1`，`SKC_HeadFace` 的 `jaw` 索引为 `15`；所以这是骨骼覆盖范围问题，不是材质或曲线传播问题。我会按这个结果给出蓝图节点级修复。

## Codex

根因已确认：`Set Leader Pose Component` 会让 follower 停止评估自己的动画。你的 `SKC_BodyClothing` 没有面部骨骼：

- Body：`jaw = -1`、`l_lips_12 = -1`
- HeadFace：`jaw = 15`、`l_lips_12 = 158`

所以 `SKC_HeadFace` 跟随 Body 后，面部骨骼只能回到参考姿势，表情消失。

在 [BP_ElliePatrolCharacter.uasset](<D:/TLOU2_UE5_8_Codex/Content/TLOU2/Blueprints/BP_ElliePatrolCharacter.uasset>) 中这样改：

1. `SKC_BodyClothing`
   - Animation Mode：`Use Animation Blueprint`
   - Anim Class：`ABP_Ellie`

2. `SKC_HeadFace`
   - Animation Mode 明确设为 `Use Animation Asset`
   - Anim Asset 设为  
     `/Game/TLOU2/CaptureMatched1152/Animations/Ellie_Patrol_CapturedSkinPose_UEHoldCarrier_Anim`

3. Construction Script 中删除或禁用这类节点：

```text
Target = SKC_HeadFace
New Leader Pose Component = SKC_BodyClothing
```

不要把 HeadFace 设为 BodyClothing 的 Leader Pose follower。重新 Compile、Save，并重新生成场景中的角色实例。

如果需要身体和面部都跟随动态动画，有两个方案：

- 给 `SKC_HeadFace` 也直接设置 `ABP_Ellie`，不要使用 Leader Pose。
- 创建专用 Head AnimBP：`Copy Pose From Mesh` 复制 Body，再用 `Layered Blend Per Bone` 在 `headb`/`jaw` 分支叠加面部动画。

单独开启 `Propagate Curves to Followers` 无法解决这个问题，因为这里缺的是面部骨骼，且 HeadFace 没有 Morph Target。

我只做了只读检查，资产文件本身未被修改。

