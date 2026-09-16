# 第四轮独立审查：核心修复通过，盲评打包待收尾

日期：2026-09-16。对应上一轮 T1–T6；本轮状态优先于第三轮历史结论。

## 结论与范围

T2–T6 在本轮核查范围内通过；T1 已解决正常 superseded 归档直接混入评分条目的问题，但打包流程尚未完整闭环。剩余工作归为一个任务：确保交付专家的报告包来自本轮同一实验输入、全部成功的预期任务，且输出目录与答案键一致。不是要求推倒已修复的特征提取或生成流程。

本轮只新增审查记录和复现脚本，未修改生产源码、未调用真实模型 API、未重生成正式报告。代码在 /private/tmp/gait-review4 隔离快照执行；审查结束重新核对 31 个源码/脚本/测试文件，哈希均未变化。主数据集使用前轮已核验的 curves.npz 重算摘要；本轮没有重新读取整套 MAT，也没有进行专家临床有效性验证。

## 已验收项

- 项目测试：40 passed（1.56 秒）。它证明已有测试通过，不代表下述额外边界已覆盖。
- T2：参考来源、人数、点数、方法及排除对象随元数据进入输入。Sub10 实际文本为“137 healthy subjects (leave-one-out, excluding Sub10), 1001 phase points, source: main_cohort_excel”。138 人背景明确标为 COHORT BACKGROUND，不再误称为本例实际参考。自定义 3 人、101 点参考不再冒用主队列描述。
- T3：冻结同秒连续写入三次，FIRST/SECOND/THIRD 三版均保留。
- T4：非对象 JSON 返回无效记录，不再调用 .get 崩溃。
- T5：已记录无 analog 的卒中 Sub08/Sub47/Sub48 使用对应说明；未明确的缺失保留原因未知，分组避免同名健康对照被误判。
- T6：request_id 与 response_id 分开保存，嵌套 usage 信息已有回归覆盖；模拟 OpenAI 响应正确保留 req-REQUEST 与 chatcmpl-RESPONSE。
- 两个真实生成入口接入模拟 provider：各首次 3 次调用、第二次新增 0 次；患者使用全对照参考，对照使用排除自身的留一参考，全部记录 v2。
- 238 份真实曲线摘要通过严格 JSON 序列化；此前多段激活、跨周期区间、缺失值说明等修复保持有效。

## 唯一剩余工作项：T1 盲评打包闭环

### 1. 成功状态校验不完整（高优先级）

位置：src/eval/blinding.py:95–104。当前只要求 stop_reason 非空。独立复现：OpenAI stop_reason=content_filter、truncated=False、有文本，仍和另两家一起打出 3 条评分记录。

建议复用 generation_cache 中按 provider 定义的成功终止原因校验。拒绝失败、未知以及其他 provider 的成功码。tests/test_packet_selection.py 的模拟结果默认所有 provider 都用 end_turn，也需改成各家真实对应的成功码，避免测试固化错误条件。

验收：正常三模型集合成功；任一非成功码必须明确报错，且不能发布一套看似完整的新评分包。

### 2. 被跳过的损坏归档仍导致匿名化崩溃（中优先级）

位置：src/eval/blinding.py:29–46、148。选择器跳过 superseded 后，_build_strip_patterns 又扫描整个目录、解析所有 JSON。独立复现：把损坏当前 JSON 经 place_record 正常归档并写入有效新报告，选择器跳过该归档，但匿名化仍抛 JSONDecodeError。

建议从已经选中的 records 构建模型匿名化规则，不再二次遍历未入选文件。

验收：有效当前报告旁有损坏 JSON、数组或 null 形式的 superseded 归档，仍只打包当前有效记录且完成匿名化；损坏的当前候选仍应报错。

### 3. 未核对本轮任务与共同实验输入（高优先级）

位置：src/eval/blinding.py:102–124。prompt_version=v2 加预期 provider 集合不能证明报告来自相同输入。独立复现：三家均为 v2、各一份、成功终止，其中 Gemini 使用 DIFFERENT INPUT，仍打包 3 条。

建议由冻结任务清单指定预期受试者、侧别、provider/model 及对应 task hash，再核对共同实验输入与参考。各 provider 的完整 task hash 本来就不同，不能直接要求三家的 task hash 相等；应分别匹配各自预期任务，并确保应当一致的输入/参考一致。保留设计允许的模型专属参数差异。

验收：同名 v2 但不同输入/参考、过期任务或遗漏整名受试者均被阻止；正常预期任务集合通过。

### 4. 重用输出目录会遗留旧评分包（中优先级）

位置：src/eval/blinding.py:139–140、172–179。输出允许目录已存在，只写当前受试者文件，重新写答案键但不处理旧受试者文件。独立复现在成功输出后放入模拟旧受试者包，重新打包后旧包仍存在。当前答案键因而不能代表目录全部评分文件；本轮未断言正式输出已经受到污染。

建议优先要求全新或空输出目录，或者采用完整临时构建后统一发布的方案。不要直接删除可能已带评分的旧目录。发布前验证预期文件集合、匿名 ID 与答案键一一对应。

验收：重用含旧包的目录时明确拒绝，或生成完整一致的新目录；不得留下未在本轮答案键内的旧包。

## 证据与复现边界

- review4/source_manifest.json、source_end_check.json：测试源码及结束一致性核查。
- review4/packaging_probes.json、probe.py：上述四项独立复现；只操作临时目录。
- review4/entrypoint_checks.json、entrypoints.py：真实生成入口接模拟 provider。
- review4/probes.json、regression_probes.py：归档、缓存、参考和 238 份真实摘要回归。
- review4/Sub10_LOO_input.txt：实际完整模型输入，见第 16 行。

注意：沿用旧探针的 claims_138=true 仅表示背景文本中包含 138；mentions_LOO_method_as_actual_reference=false 使用旧固定短语匹配。二者不是本轮失败判断；实际第 16 行已正确区分参考。以完整输入及本报告结论为准。

T1 修复并补充以上有意义的集成测试后，可进入预先规划的 SDK/真实小样例兼容性核验与正式 v2 生成。统计方案冻结、专家参考标准和评分设计仍是研究阶段工作；本轮代码验收不替代这些工作，也不支持提前比较模型临床能力。
