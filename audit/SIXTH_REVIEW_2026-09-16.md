# 第六轮独立审查：F1/F2 验收通过

日期：2026-09-16。结论优先于第五轮历史问题状态。

## 结论与范围

上一轮 F1（任务清单阻断打包）、F2（旧批次答案键覆盖）均通过独立验收。此前 T1 打包收尾可关闭，T2–T6 的已通过状态保持。未发现本轮验收范围内新的打包阻断问题，可转入既定真实 SDK 小样例和研究评价准备阶段。

本轮只新增审查材料并更新交接文档，没有修改生产代码、调用付费 API 或生成正式报告。真实 main() 使用模拟 provider、合成曲线和临时目录；不是对在线模型或临床解释能力的验证。未重算主数据集；相关提取代码未变化。

## 独立验证结果

- 现有全套测试：45 passed in 1.46s，使用 /Users/lixinyu/.venvs/gait-emg/bin/python，在 /private/tmp/gait-review6 源码快照上运行。
- 对比第五轮变动：新增 src/llm/generation_runner.py，修改 blinding.py、两个生成脚本和 test_packet_selection.py。32 个源码/脚本/测试文件在结束时哈希复核一致。
- 实际调用 generate_pilot_reports.main() 和 generate_control_spotcheck.main()，分别接模拟 provider；每个入口首次调用 3 次，重复运行新增调用 0 次。没有用手工报告替代此入口验收。
- 两个入口各自生成的完整目录原样进入打包；任务清单位于 _meta/task_manifest.json，加载清单后传入预期任务、三家 provider 和 v2，均成功打包 3 条，答案键各 3 行，匿名 ID 集合一致。F1 通过。
- 冻结时间为同一秒，连续打包三次，生成三个不同批次目录。第一次批次所有文件哈希保持不变，各批次答案键与各自报告一一对应。
- 每个批次包含 packets/、answer_key_DO_NOT_SHARE.csv、rubric.json、packaging_manifest.json；答案键未进入发给专家的 packets/。F2 通过。
- 注入 packaging_manifest 写入异常：没有产生新的正式批次，旧三批所有文件保持不变，仅留下明确标记 .building 的未完成目录。批次整体发布的关键失败路径已验证。
- 相关负例回归：OpenAI content_filter、错用其他 provider 成功码、与冻结清单不符的输入、预期外受试者均被拒；三种损坏 superseded 归档不影响有效当前集合。

## 使用约定与后续准备

正式打包应加载 _meta/task_manifest.json，并提供 expected_tasks、expected_providers、prompt_version；这三项是显式参数，不能省略后仍声称做了完整任务验收。create_rating_packets 返回本次 batch 路径，后续按该路径分发 packets 与 rubric；答案键和内部 manifest 留在研究管理侧。旧的审查脚本输出路径属于当时 API，不应用旧路径去判断新实现失败。

本次重构有一个非阻断的溯源补充建议：两个生成脚本的 CODE_FILES 仍未包含新 generation_runner.py。正式采集冻结代码前，将该共享生成模块及实际入口纳入源码清单或保存完整代码快照，避免留档声称覆盖全部生成代码却遗漏新模块。这不影响已验证的 F1/F2 行为；无需因此重做整轮打包审查。

下一步沿既有计划推进真实 SDK 小样例兼容性、依赖和配置冻结，以及专家参考材料/试评准备。模拟接口通过不代表在线 SDK 已验证，也不代表临床结论已获专家认可。本轮未替用户启动付费调用。

## 证据

- review6/source_manifest.json、source_end_check.json：源码及结束一致性。
- review6/test_results.txt：45 项项目测试结果。
- review6/entrypoints.py、entrypoint_checks.json：两个真实 main() 的生成、幂等重跑、清单加载、打包与答案键对应。
- review6/packaging_probes.py、packaging_probes.json：正常/错误集合、同秒多批次、旧批次完整性及发布前写入失败。
