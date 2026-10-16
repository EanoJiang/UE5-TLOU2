# Git 上传准备说明

此目录由 `D:\TLOU2_UE5_8_Codex` 的当前清理版本同步生成。同步只覆盖工作文件，保留 `.git`，未执行 `git add`、`git commit`、`git push` 或任何历史重写。

保留内容：

- `Content/`：当前 UE 5.8 资产、Groom、Drawstring、HoodSeam、地图和 SourcePaks。
- `Config/`、`Source/`、`Scripts/`、`docs/`、根目录项目/启动文件。
- `Scripts/` 只保留当前资产管线和验证入口；根目录一次性探针、`_tmp*`/`tmp_*.js` 以及旧 Exact/1074/1390/RawRoot 导入族已移出。
- `.gitignore`、`.gitattributes` 和本说明。

排除内容：

- `Binaries/`、`Intermediate/`、`DerivedDataCache/`、`Saved/`：UE 构建输出、索引、缓存、日志和自动保存。
- `Exports/`、`Blender/`、`_Archive/`、`--background/`、`AnimTest/`、`_external/`：大型交换文件、历史证据、实验缓存和嵌套资料。
- `__pycache__/`、`*.py[cod]`、临时文件。

`Config/DefaultEngine.ini` 中的 Android File Server `SecurityToken` 已替换为 `REPLACE_WITH_LOCAL_TOKEN`；本地使用时请通过未提交的本机配置设置新 token。

源项目中的完整导出、Blender 文件、历史归档、Reports 和验证缓存仍保留在 `D:\TLOU2_UE5_8_Codex`，临时脚本留档在 `D:\TLOU2_UE5_8_Codex\_Archive\TLOU2_cleanup_2026-10-17\GitPrunedScratch`，未复制到本 Git 工作树。当前目标工作树约 542.3 MiB、1,169 个文件；最大单文件约 16.2 MiB，没有 GitHub 100 MiB 单文件限制。大体积 Blender/交换资产若需上传，应另用 Git LFS 或外部存储。
