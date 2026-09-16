# 第五轮独立审查：打包仍有两处集成缺口

日期：2026-09-16。对应第四轮 T1 四项收尾；此报告优先于前轮历史结论。

## 结论

45 项现有测试通过。成功状态校验、损坏归档隔离、按冻结任务哈希拒绝异输入报告均通过独立复验；重跑后当前 packets 目录也不再遗留旧受试者。然而真实生成入口到打包器的链路被新任务清单阻断，且旧评分包的答案键没有一起归档。当前不能标记 T1 全部完成。

本轮不改生产源码，不调用付费 API、不重生成正式数据。只新增 audit/review5 复现材料和本报告，更新交接文档。对比第四轮，生产/测试仅四个文件变化：blinding.py、两个生成脚本、test_packet_selection.py。31 个 Python 文件已快照到 /private/tmp/gait-review5，结束哈希复核无变化。特征提取和主数据集读取没有变化，本轮不重复整套数据审查；前轮结论在其原有范围内保持。

## 已通过，不再重复修改

- 全套现有测试：45 passed in 1.59s。
- 三家正常成功码的有效集合正确打包 3 条。
- OpenAI content_filter、有文本、未截断被拒；OpenAI 错用 Anthropic end_turn 也被拒。
- 损坏 JSON、数组、null 三种 superseded 归档同时存在，正常当前集合仍完成匿名化和打包。
- Gemini 使用不同输入，与冻结预期任务哈希不符时正确拒绝。预期外受试者也被拒；现有测试另覆盖预期受试者缺失。
- 两个实际生成入口接模拟 provider，首次各生成 3 条、第二次新增调用 0 次，均写出包含 3 项的任务清单。
- 不含清单文件的隔离报告目录重建后，当前评分包与新答案键匹配，旧受试者包不再混入当前 packets。

## F1：生成器写出的任务清单被打包器当作报告（高优先级，阻断正常链路）

位置：scripts/generate_pilot_reports.py:147、scripts/generate_control_spotcheck.py:147；src/eval/blinding.py:111。

两个入口都将 task_manifest.json 写入 OUT_DIR。_select_current_reports 对该目录 glob("*.json")，只排除 superseded；于是把任务清单当作普通报告，因其没有 report_text 报错。

独立复现使用两个真实 main()，只替换数据加载器、provider 与昂贵文件哈希，随后按接口调用 load_task_manifest 和 create_rating_packets，传入 v2、预期三家 provider 和任务清单。两个入口都失败：

    PacketSelectionError: blank/non-string report_text: task_manifest.json

这不是模型请求失败或数据问题，是生成与打包的新文件约定没有对齐。现有测试手工构造 report JSON，未包含真实生成脚本产出的清单，因而漏掉。

建议：清单移到独立元数据位置并统一调用方；或在报告选择器显式排除约定的清单文件，继续对损坏的真正报告严格报错。不要笼统忽略所有无 report_text 的文件，以免吞掉损坏报告。

验收：两个真实生成入口接模拟 provider → 原样保留生成目录所有文件 → 加载清单 → 打包，均成功且每名受试者恰含三条、答案键一致。异输入和缺失任务仍拒绝。

## F2：只归档旧评分文本，没有保留旧答案键（中优先级，历史评审可追溯性）

位置：src/eval/blinding.py:244–263。

独立复现：先为 Sub01 打包，再向同一输出目录为 Sub02 打包。旧 Sub01.json 被移入 packets.previous-<ts>/，但旧 answer_key_DO_NOT_SHARE.csv 被覆盖，输出目录内所有 CSV 均不再包含原答案键。旧包和新包又都会从 R0001 开始编号，不能拿新答案键解释旧评分。

已修复的是“当前目录遗留旧受试者文件”；未修复的是“旧批次完整保留”。本轮没有断言正式评分数据已丢失，也不把测试临时目录的问题描述为现有研究数据事故。

此外，当前 staging 仅含报告包：先切换 packets，再写答案键和 rubric。文档所称“packets、answer key、rubric 完整构建后统一发布”与实现不符。文件写入异常时可能出现新报告配旧/不完整答案键；这是静态代码路径判断，本轮未注入磁盘故障测试。

建议优先使用全新、独立的批次输出目录，并拒绝覆盖既有批次；这已足以满足前轮要求，无需复杂事务。如果保留重用目录功能，则把 packets、答案键、rubric、相应任务清单作为整批构建和归档，答案键始终保密且与该批次绑定。不要把答案键放进交给盲评专家的 packets 子目录。

验收：连续打包两个不同批次，两个批次均保留自己的完整匿名映射；各自评分包 ID 与各自答案键一一对应。或者直接拒绝重用已有批次目录，且旧文件字节不变。

## 证据与下一步

- review5/source_manifest.json、source_end_check.json：源码快照和结束一致性。
- review5/test_results.txt：现有测试结果。
- review5/entrypoints.py、entrypoint_checks.json：两个实际生成入口到打包器的失败复现；模拟模型，无网络调用。
- review5/packaging_probes.py、packaging_probes.json：成功状态、损坏归档、任务哈希、当前包清理及旧答案键丢失验证。

下一轮只验收 F1、F2 及相关正常链路回归；T2–T6 和已通过的 T1 校验保持。无需为验证这两项而调用付费模型或重算主数据集。通过后再进入既定的真实 SDK 小样例、研究方案与专家试评准备；代码通过不等于临床有效性通过。
