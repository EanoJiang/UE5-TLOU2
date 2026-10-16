# 艾莉巡逻服装 UE5.8 工程

这是可直接放入 Git 的运行时工程副本。当前入口是 \`BP_ElliePatrolCharacter\` 和
\`/Game/TLOU2/Maps/ElliePatrolCaptureGroom\`，默认角色包含 Groom、帽绳和当前验证过的服装材质。

## 运行

使用 [TLOU2Codex.uproject](TLOU2Codex.uproject) 在 UE 5.8 中打开工程。也可以使用：

- [打开编辑器](Open_Catalog_UE58.cmd)
- [打开 Groom 近景](Open_Groom_UE58.cmd)
- [直接运行图鉴](Play_Catalog_UE58.cmd)
- [运行 Groom 近景](Play_Groom_UE58.cmd)

默认地图为 \`/Game/TLOU2/Maps/ElliePatrolCaptureGroom\`；另外保留了 Back、Front、ThreeQuarter、
FrontRef 和 TrueFront 验证地图。运行时模块位于 \`Source/TLOU2Codex\`，项目配置位于 \`Config/\`。

## 当前资产

- \`Content/TLOU2/CaptureMatched1152\`：29 个角色网格、服装、展台和贴图。
- \`Content/TLOU2/Groom\`：截帧 Groom、HeroCorrected Groom 和 HairThinOverlay 资产。
- \`Content/TLOU2/Drawstring\`：独立 22 节点帽绳骨骼网格及材质。
- \`Content/TLOU2/HoodSeam\`：帽衫接缝诊断资产。
- \`Content/TLOU2/SourcePaks\`：当前复现所需的角色、服装、头发和动画 PAK。
- \`Content/TLOU2/TexturesDecoded\`：已导入 UE 的运行时贴图。

角色规范版本为 29 网格、84,954 个顶点缓冲分配、117,459 个三角形和 1,152 根骨骼。Groom 使用
52,954 根真实 Strands；帽绳保留独立蒙皮，不修改原有服装网格。

## 操作

鼠标左键拖动旋转；W/A/S/D 平移；Z/X 或滚轮缩放；Q/E 跳到最近或最远距离；R 复位；F 显示或隐藏
说明；Esc 退出。

## Git 副本范围

本目录已移除 UE 构建输出、缓存、交换文件和历史临时目录：\`Binaries/\`、\`Intermediate/\`、\`Saved/\`、
\`DerivedDataCache/\`、\`Exports/\`、\`Blender/\`、\`_Archive/\`、\`--background/\`、\`AnimTest/\` 和
\`_external/\`。根目录一次性探针、脚本中的 \`_tmp*\`/\`tmp_*.js\` 以及旧 Exact/1074/1390/RawRoot
导入族以及 HairThin/HeroFringe/HeroLock/cloth 实验和 HoodSeam 拟合探针也已从此 Git 副本移出；当前只保留
资产构建、导入和验证所需的最小入口。它们的留档在源工程的
\`D:\\TLOU2_UE5_8_Codex\\_Archive\\TLOU2_cleanup_2026-10-17\\GitPrunedScratch\`。

Reports、Blender 源文件、大型 FBX/glTF、截帧预览和未选入当前运行时的 SourcePaks 仍保留在源工程归档，
用于审计或重建，不复制进 Git 工作树。\`.gitignore\` 会继续忽略这些目录以及 Python 缓存和临时文件。

\`Config/DefaultEngine.ini\` 中的 Android File Server token 使用
\`REPLACE_WITH_LOCAL_TOKEN\` 占位符；本机调试时请使用未提交的本地配置设置 token。

## 范围限制

截帧 Groom 和服装是当前静态验证状态；没有把未解析的 helper 绑定或动态布料模拟宣称为已恢复。眼球、
皮肤、头发和泪膜材质是可移植重建，原始纤维光学、角膜折射和完整 SSS 没有全部移植。原始 0FW 只包含
稀疏的右臂和手指动画层，根位移为零。

更完整的报告、交换文件和历史实验记录见源工程归档，不属于这个可上传 Git 的运行时基线。
