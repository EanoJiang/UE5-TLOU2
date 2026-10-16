# Git 上传准备说明

此目录由 D:\TLOU2_UE5_8_Codex 生成，目标是提供一个适合加入 Git 的 UE 5.8 工程副本。此次只复制和整理文件，未执行 git init、git add、git commit 或 git push。

## 保留内容

- Content/：UE 资产、材质、地图、Groom、SourcePaks 等核心工程内容。
- Config/、Source/、Scripts/、docs/。
- 根目录 TLOU2Codex.uproject、README、启动命令文件和小型工具脚本。

## 从副本剔除的内容

- Binaries/、Intermediate/、DerivedDataCache/、Saved/：UE 构建输出、索引、着色器/派生缓存、日志和自动保存，可由引擎重新生成。
- Exports/（源目录约 8.5 GiB）：截帧块、导出缓存、历史实验、重复备份和大量诊断文件。
- Blender/（源目录约 1.7 GiB）：DCC 工作文件；其中多个 .blend 大于 GitHub 单文件 100 MB 限制，.blend1 是备份。
- _Archive/、--background/、AnimTest/：归档、分析证据和测试临时资料。
- _external/：嵌套的独立 Git 仓库及下载资料，避免形成嵌套仓库。
- 根目录 tmp_anim_list.txt 和 Python __pycache__。

## 后续上传提示

副本根部的 .gitignore 已覆盖以上目录和常见 UE/IDE 临时文件。若之后需要上传 Blender 或 Exports 中的规范交换资产，建议单独筛选并使用 Git LFS；不要把完整的捕获缓存、历史备份和构建目录复制回来。项目 README 中指向 Exports/、Blender/ 的部分证据链接在这个精简副本中会缺失，原始资料仍保留在源目录。


注意：在后续检查期间，如果 Unreal Editor 或相关工具打开此副本，可能自动生成少量 Intermediate/、Saved/ 或 Binaries/ 内容；这些路径已经由 .gitignore 忽略，不会被 Git 上传。若要让目录保持物理空白，请在关闭 Unreal Editor 后手动删除它们。
