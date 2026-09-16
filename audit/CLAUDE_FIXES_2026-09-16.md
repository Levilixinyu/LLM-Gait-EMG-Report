# 修复记录:对 2026-09-16 审查交接的逐项响应

执行者:Claude(Fable 5 会话,接替生成 v1 的 Sonnet 5 会话)。
约束遵守情况:v1 已冻结未覆盖;全部为本地修复与验证;未调用任何付费模型 API。

> 已读 handoff v2(2026-09-16 14:35 更新)与《主数据集可用性评估》。
> 第八节补充项的响应见文末新增章节。

## 逐项状态表(handoff v2 头部要求)

| 项 | 状态 |
|---|---|
| 冻结 v1 | 核验通过(113 文件 SHA256 全对) |
| P0-1 多区间/跨界 | **核验通过**:10/10 测试全绿;Sub50 TA 输出跨界区间 (56.6→7.4),Sub05 GAS 后段(含 max\|z\| 相位 80%)进入结构化输出与文本(fix_verification.json) |
| P0-2 阈值口径 | **核验通过**:正式 `analyze_activation()` 复算双口径表,与审查复现数字逐格一致(相对 32/37/9/0/15/7;绝对 12/3/1/0/2/3) |
| P0-3 max\|z\| 校准 | **核验通过**:原始数据重算 plain+LOO 校准与审查一致(GAS p95 3.936,RF 4.527,TA 4.605…;LOO 更高;any-muscle>2 = 109/109);`data/normative_calibration_v2.json` 已产出 |
| P0-4 撤回结论/重定义对照实验 | 核验通过(README 专节 + 本文更正汇总) |
| P1-1 输入信息补全 | **核验通过**:v2 样例已产出(Sub50/Sub05/Sub09/Sub47),含定义块、全区间、方向/相位、诚实缺失表述 |
| P1-2 raw 尺度 | **核验通过**:10 倍幅度下 z 相对差 2.0e-11(修复前为 2.6 倍差异)。注:首轮验收判 False 是我的验收条件错误(量级 233 的值用 1e-9 绝对容差),已改相对容差并重跑 |
| P1-3 步长定义 | 已修复(双定义显式化、docstring 与代码一致、敏感性入档;临床裁定保留争议——该项无自动验收,属文档+接口修复) |
| P1-4 匿名化 | **核验通过**:test_blinding.py 2/2 通过(完整 ID 无残留片段、厂商词兜底有效) |
| P1-5 可复现 | 部分修复:脚本改造完成;`requirements.lock.txt` 已生成(注明未含 API SDK);响应侧元数据(request ID/usage/实际模型版本)留待下次真实调用落地 |
| P1-6 README 事实 | 核验通过(逐条订正) |
| §8.1 研究范围声明 | 已修复(README 头部新增 scope 段) |
| §8.2 速度支持范围 | 已修复(METRIC_DEFINITIONS 新增 0.80 m/s 下限与 41/50 事实) |
| §8.3 有效样本量口径 | 已修复(EMG n=106-109 订正;逐周期数/质量掩码要求记入待办) |
| §8.4 临床记录不一致/辅助行走 | 已修复(README pilot 节注明 Sub46=TVC54 辅助行走、FAC/TIS 不一致保留不改) |
| §8.5 动力学禁入 | 无需改代码(当前管线本就未用动力学;README scope 已明示) |
| §8.6 专家参考标准 | 记入待办(评分三层框架、清单式参考、≥2 专家先独立后裁决——依赖 v2 报告) |
| §8.7 下阶段顺序 | 记入待办(3-5 例试评包、18 人披露为开发用途) |

## 交接复核结论:核心判断全部成立,未发现需要反例反驳的项

按交接要求,修复前对关键主张做了独立复核(不直接采信审查自己的汇总数字):

| 审查主张 | 我的独立复核方式 | 结果 |
|---|---|---|
| Sub50-P TA 有被丢弃的第二段(~57-100%) | 用正式数据自写区间扫描 | 证实:(0.0,7.0)+(56.8,100.0) |
| Sub05-P GAS 有被丢弃的第二段,max\|z\|=13.33 在 80.3%,SD=0.023 非近零 | 同上 + 审查 z_scores.csv 逐行核对 | 证实;我此前的"低方差伪影"解释撤回 |
| 健康对照 max\|z\| 的 p95 为 3.65-4.61,不是 2 | 用审查逐行 CSV 自行聚合分位数 | 证实(ERS 3.65 … TA 4.61);我起草 v2 说明时误写成 3.3-3.9(实为 p90),已改正——说明数字必须逐个验算 |
| 匿名化先删厂商词导致完整 ID 漏配 | 用现行代码直接构造测试输入 | 证实:`gemini-3.1-pro-preview`→`[model]-3.1-pro-preview` |
| raw 路径尺度不匹配(10 倍幅度 → z 370.58→967.72) | 用合成信号重跑 | 证实,数值完全一致 |
| Claude Sub50 报告"6.86 低于四项 GVS 中的三项"是算术错误 | 读取报告原文 | 证实,句子自相矛盾且只有 2 项高于 6.86 |
| 磁盘 94% 未证实为卡顿根因;存在 dataless 云占位 | `ls -lO` 检查 venv | 证实并**确定了机制**:.venv 内 18346 个文件带 `dataless` 标记(iCloud 桌面同步 + 优化存储驱逐),冷访问需从 iCloud 回载,这才是分钟级导入的直接原因;磁盘压力是驱逐诱因而非直接根因 |

## 已完成的修复(按交接优先级)

### 冻结 v1(交接 §五-1)
- `v1_freeze/`:113 个文件(src/scripts/tests/README/requirements、pilot_subset、
  66 份报告、评分包)+ `MANIFEST.sha256`,全部校验通过。
- v1 报告与评分包在 `data/` 原位保留未动;README 明确标注 v1 仅作探索性记录,
  不得用于模型比较或专家评分。

### P0-1 多区间与周期边界(emg_signal.py)
- 新增 `analyze_activation()` + `ActivationProfile`:环形扫描返回**全部**满足
  阈值+最短时长的区间;跨 0/100% 的连续激活合并为单一 wrapped 区间
  (onset>offset 表示跨界)并置 `crosses_cycle_boundary`;单独报告
  `above_threshold_pct`(区间之外的信息量);阈值定义、峰值、峰值相位随结果携带。
- 旧 `onset_offset_pct_from_cycle()` 保留但明确标注 DEPRECATED、仅供与 v1 对照,
  docstring 改为如实描述其"只取第一段、绝对阈值"的 v1 行为。
- `MuscleFinding` 扩展:`activation_intervals`、`above_threshold_pct`、
  `crosses_cycle_boundary`、`deviation_z_signed`、`deviation_phase_pct`;
  旧 onset/offset 字段保留为"第一区间"并注明仅限 v1 对照用途。
- `to_prompt_text()` 序列化全部区间、跨界标注、超阈值占比;"no interval met
  detection criteria" 取代 "not detected",并在指标定义中声明其不等于无肌肉活动。
- 新测试 `tests/test_emg_signal.py`:双 burst、跨界合并、全周期、短于最短时长、
  全 NaN、部分 NaN、尺度不变(阈值随峰值缩放)七个失败模式。
- 验收(Sub50/Sub05 后段进入结构化输出与文本):由
  `scripts/audit_fix_verification.py` 输出 `fix_verification.json` 佐证。

### P0-2 阈值口径统一(冻结主定义)
- **主定义(冻结)**:阈值 = 该曲线自身峰值的 20%,最短区间 3% 周期。
  理由:与原 docstring 意图及 raw 路径实际语义一致(统一两条路径);Excel 数据为
  逐周期归一化后平均、均值曲线峰值≠1,绝对 0.2 在受试者间含义不一致;符合
  EMG 文献 %peak 惯例。绝对 0.2 保留为敏感性口径。
- 定义敏感性巨大且已如实入档(README 新表,双口径并列;来源:审查复算,
  由验证脚本用正式函数重算确认)。**注意我的独立复核还发现:对低峰值肌肉
  (如 Sub05 GAS,峰值 0.39)两种口径给出的区间几乎完全不同
  (绝对口径两段窄 burst vs 相对口径近全周期)——定义选择实质影响生理叙事,
  这是必须冻结并声明的原因。**
- README 原表格及"健康 ERS 35% 全周期激活"解释已重写:标明计算口径、
  两口径数字并列、区分"≥95% 采样点超阈值"与"检测器返回单一 0-100% 区间"。

### P0-3 max|z| 校准
- 提取新增最大偏差的**符号与相位**;`METRIC_DEFINITIONS`(随每份 v2 输入下发)
  明确:这是 1001 点最大绝对 z 的极值统计量、不适用 2 SD 惯例、健康对照
  109/109 至少一块肌肉 >2、各肌肉健康 p95 = 3.65(ERS)-4.61(TA)、留一法更高、
  健康分布为内部经验参考而非已验证临床界值。
- `scripts/audit_fix_verification.py` 从原始数据重算 plain + 留一法校准,写入
  `data/normative_calibration_v2.json`,并交叉核对定义文本中的数字。
- 109/109 的含义已在 README 与定义文本中限定为统计量行为,非疾病率、
  非 LLM 假阳性率。

### P0-4 撤回无依据结论、重定义对照实验
- README 新增 "Healthy-control spot-check (v1): what it was and was not":
  - 定性为**已知标签的解释任务**,4 人 × 3 模型 ≠ 12 独立病例,不可得假阳性率;
  - **撤回**"假阳性检查通过""Claude 质疑 Sub10 标签体现更强推理"
    "Claude 明显更强",降级为待检验假设;
  - 记录反例:Sub10(81 岁)GPS-like 位于对照第 ~81 百分位(p95=10.71),
    质疑其标签并非天然高明;Claude Sub50 算术错误曾被会话中的我当作亮点表扬;
    Claude/Gemini 均把健康范围内的 CCI 0.63 称为 high/elevated(健康中位 0.68);
    GPT 的谨慎部分源于输入确实缺定义,不是无价值套话;
  - 声明正式比较须来自盲评 + 预定义错误类别 + 受试者内重复测量分析,
    不得由被比较模型本人事后挑例。

### P1-1 输入信息补全
- `METRIC_DEFINITIONS` 常量随每份 v2 输入下发:矢状面声明、EMG 归一化语义
  (禁止跨肌肉比强弱)、区间/跨界/0% 语义、max|z| 定义与健康参考、CCI 公式与
  健康分位数(并解释与不重叠 burst 并存的原因)、GPS-like 构成与健康分位数、
  对称指数公式与符号方向、参考队列非年龄/速度匹配、
  "数据集存在但本次未提供"字段清单(年龄/性别/TPS/临床评分/对侧数据/toe-off)。

### P1-2 raw 路径尺度修复
- `extract_patient_summary` 改为在峰值归一化后再对比归一化参考(共用
  `_muscle_finding`);验证脚本含 10 倍幅度不变性断言。影响范围:仅 raw 路径,
  Excel 路径的 54 份 v1 报告不经过该代码(README 已如此陈述)。
- `detect_onset_offset()`(Hodges-Bui 时域实现)仍未接入 raw 路径——如实保留
  "存在但未使用"状态,未虚称已接入。

### P1-3 步长定义
- docstring 与代码不一致已修复:默认 `successive_footfall`(= v1 行为,数字可
  复现)如实描述为"对侧足着地点位置 − 本侧步首着地位置";新增 `instantaneous`
  (同时刻双脚距离)为显式可选项;审查的敏感性结果(Sub45 +5.80%→−0.27%)
  记入 docstring 与 README;明确内部一致性 ≠ ground truth,速度的外部核对
  (补充表 5,四位小数)独立于该争议。未裁定哪种定义为临床真值。

### P1-4 匿名化
- 完整模型 ID(按长度降序)先于厂商词根替换;文件枚举 `sorted()` 固定顺序;
  新测试 `tests/test_blinding.py` 守护替换顺序与残留片段。
- 未声称 v1 已实际泄漏(66 份文本无模型自称,与审查一致)。
- v1 评分包与 v1 报告一同降级为探索性;v2 评分包应在 v2 报告生成后重建。

### P1-5 可复现性
- `generate_pilot_reports.py`:输出改 `data/reports_v2/`、PROMPT_VERSION=v2、
  每条记录内嵌完整 system/user prompt 与 config hash(prompt 版本 + system prompt
  + 模型名 + 特征提取源码文件内容的 SHA256 前 16 位)、跳过前校验既有文件
  (可解析、同 config hash、非截断),损坏/过期配置文件不再被静默跳过。
- 待办(见"未解决"):响应侧元数据(request ID、usage、实际响应模型版本)
  需要在下次真实调用时从 SDK 响应对象补充采集;依赖锁定文件在 venv
  实体化完成后生成。

### P1-6 README 事实订正
- "chronic stroke cohort"→ 亚急性(TPS 14-139 天,入组 <5 个月);
- "没有任何预计算时空参数"→ 订正:补充表 5 有步速,且我方计算与其
  100 条数值对齐至四位小数(这才是速度的独立验证);
- MAT 为处理后周期归一化数据、非原始连续 EMG;
- 全通道缺失不再断言为电极故障,注明"原研究存在未采集模拟信号者,
  具体原因未公开";
- "两个路径均已验证"等措辞降级为"可运行 + 明确列出已修复缺陷";
  "验证"一词仅保留在有独立外部对照的项(速度)。

## 会话内此前口头结论的更正汇总(供用户对照)

1. 撤回:"Sub05 GAS 13.3 SD 可能是低方差伪影"——实测 SD=0.023 非近零,
   且该值位于被 v1 丢弃的真实第二段内。
2. 撤回:"健康对照假阳性检查通过、三模型底线合格"——该实验设计不支持
   此结论(标签已知、样本 4 人、无预定义错误标准)。
3. 撤回:"Claude 批判性整合能力明显更强"——依据为未盲化少量案例,
   且其中被我表扬的 Sub50 复合分数讨论包含算术错误。
4. 更正:"磁盘 94% 满导致一切变慢"——直接机制是 iCloud 驱逐产生的
   dataless 回载;磁盘压力是诱因。
5. 更正:v1 的 54 份报告"verified clean"仅指结构/终止状态,其输入
   携带 P0-1/P0-2 缺陷,内容不作数。

## 仍未解决 / 需用户决定

- **v2 报告未生成**(需付费 API,等待用户明确授权;生成前建议先过目
  `audit/outputs/v2_input_samples.txt` 的输入样例)。
- 专家评分材料(事实核验输入、评分填写表、裁决参考答案)未建——属交接
  §五-7,依赖 v2 报告存在。
- 请求/响应完整留档需在下次真实 API 调用时落地(providers 返回对象需
  透传 request ID / usage / 响应模型版本)。
- 步长定义的临床裁定(须核对原研究协议或联系作者)。
- 外部数据集 EMG 通道映射(不变:公开资料不含,勿凭波形猜测当真值)。
- 依赖锁定与全量测试通过确认:等待 venv iCloud 实体化完成后执行
  (`pip freeze > requirements.lock.txt` + 全量 pytest)。
- 建议(需用户决定):项目移出 iCloud 同步的 Desktop,或将 .venv 排除出
  同步范围,否则 dataless 驱逐会反复发生。

## 对 handoff v2 第八节的响应(2026-09-16 增补)

- **§8.1 范围**:README 头部新增冻结的研究范围声明(描述忠实性/不确定性表达/可评审报告;
  排除诊断、机制确认、治疗选择、部署验证),并链接可用性评估的决策表。
- **§8.2 速度支持**:METRIC_DEFINITIONS 新增"SPEED SUPPORT LIMIT"条目:健康自选速度
  0.80-1.79 m/s,低于 0.80 的受试者(41/50)在本数据集内无速度匹配参考,偏差混杂
  慢速效应与卒中特异性改变且不可分离——该条随每份 v2 输入下发,直接约束模型解释,
  也应约束专家评分与论文结论。
- **§8.3 样本量口径**:EMG 参考 n 订正为各肌肉 106-109(README 头部+定义文本);
  README pilot 节注明 18 人为开发病例、43 名双侧完整者为主分析候选。
  逐周期有效数(2-17,中位 8)与 Sub43 非正时长周期的质量掩码要求记入待办
  (当前 Excel 平均曲线路径不受影响;逐周期分析启动前必须先建统一质量规则)。
- **§8.4 临床记录**:FAC/TIS 不一致按发布值保留并注明;Sub46(TVC54)辅助行走已注记,
  Sub41/Sub43(TVC48/51)不在 pilot 中;未改数据、未编造原因;联系作者留待用户授权。
- **§8.5 动力学**:当前管线未使用 GRF/力矩/功率,维持不使用;README scope 明示
  加入前需独立质量核查。
- **§8.6/8.7 评价流程**:接受"专家参考标准而非绝对真值"的三层框架、清单式参考材料、
  ≥2 专家先独立盲评后裁决、3-5 例试评包(覆盖完整/缺失/健康)的顺序;
  这些依赖 v2 报告与专家资源,标记为下阶段待办,未冒称已实施。

## 对 handoff v3 第九节(第二轮审查 R1-R8)的响应(2026-09-16 第二批增补)

先致谢:第二轮抓到的 R7(我的验收脚本"任意 wrapped 区间即通过"的漏判)、R3
(Sub46"辅助器械"误写)、R6(Sub47=TVC55 有文档记载的无模拟采集)都属实,
均已修复;本文所有"通过"仅指本地检查,不扩大为整套研究已验收。

| 项 | 改动 | 证据/测试 |
|---|---|---|
| R1 统一入口 | `generate_control_spotcheck.py` 迁移至 `reports_control_spotcheck_v2/` + v2 标签 + **留一法参考**(被测者不再进入自身基线);`report_generator.py` 标注 DEPRECATED、加 DeprecationWarning、拒绝覆盖已有文件;两个正式脚本共用 `generation_cache` | 代码评审 + `test_generation_cache.py` 机制级验证 |
| R2 任务身份/缓存 | 新建 `src/llm/generation_cache.py`:TaskSpec 覆盖 subject/side、完整 system+user prompt、provider/model/参数、reference_id、数据文件 SHA256、源码清单(补齐 providers/kinematic/spatiotemporal/data_types);有效性检查 = 可解析 + task_hash 一致 + subject/side 与 spec 及文件名一致 + 非空白文本 + 按 provider 白名单的成功终止 + 非截断;`place_record` 遇同名先改名 `*.superseded-<ts>.json` 保留 | `tests/test_generation_cache.py` 13 项:输入/参考/参数/代码/数据变化各自改变哈希;空白文本、缺终止、非成功终止、受试者冒名、损坏 JSON 全部拒绝;supersede 保留旧档 |
| R3 评分/文档 | README Next steps 整节重写(不再指示分发 v1 评分包;新流程=评价基础冻结→3-5 例试评→冻结方案→授权生成 v2→独立评分+裁决);rubric 的 normal/abnormal 检查改为"按输入携带的指标特定参考评判、无参考时 INDETERMINATE 才是正确行为";**Sub46 更正为物理治疗师扶手协助** | README diff;rubric.py diff |
| R4 响应元数据 | `GenerationResult` 增 `response_model`/`request_id`/`usage`;三家 provider 各自的提取函数为模块级、无 SDK 依赖、缺字段安全降级为 None;记录随 `record_from_result` 入档 | `tests/test_provider_metadata.py` 5 项 mock 测试(含全缺字段不抛异常) |
| R5 参考说明随源生成 | 定义文本拆分:`_DEFS_COMMON` + `_DEFS_MAIN_COHORT`(仅 `reference_source=="main_cohort_excel"` 时)+ `_DEFS_GENERIC_REFERENCE`(明示无校准分布、任何分位数不适用);raw 路径标记 `unspecified_raw`,不再被冠以 138 人/1001 点/主队列分位数 | 代码评审;v2 样例复生成 |
| R6 输入诚实性 | `missing_emg_channels` 显式列出(Sub46 将列出 6 个缺失通道);Sub47(TVC55)使用文档记载的"无模拟采集"原因,其余缺失者保持"未记录";步长定义作为元数据从 `mat_spatiotemporal` 记录→lookup→summary→文本一路携带,`instantaneous` 选项不再会配错说明 | v2 样例复生成(见 fix_verification 重跑) |
| R7 验收可失败 | `interval_covers()` 实现真环形相交(审计反例 wrapped(95,5) vs (75,86) 现判 False);增加结构↔文本一致性检查;失败聚合入 `failures` 列表,写入 JSON 并以非零退出码结束 | 正负例内联验证 5/5;脚本重跑 |
| R8 通用路径边界 | 部分 NaN:掩码策略明示于 docstring,`nan_pct` 进入 ActivationProfile/MuscleFinding 并在文本中输出 DATA QUALITY 标记;CCI 要求全有限曲线否则跳过(主数据无部分 NaN,不影响已核验结果);最短时长的"采样点数 vs 端点跨度"约定写入 docstring | `test_partial_nan_treated_as_inactive` 既有 + 代码评审 |
| §9.6 方法变更留档 | README 阈值节已注明:v1→v2 的差异包含(a)漏段修复、(b)阈值定义变更(绝对 0.2→峰值 20%,对低峰值肌肉区间实质不同,如 Sub05 GAS 两段窄 burst→~97% 全周期)、(c)输入信息增加,三者在任何 v1/v2 比较中必须分开归因,不得统称模型能力变化 | README diff |

测试总量:10 → **28 项全部通过**(新增 cache 13 项 + metadata 5 项)。

## 对 handoff v4 第十节(第三轮审查 T1-T6)的响应(2026-09-16 第三批增补)

| 项 | 改动 | 验收测试 |
|---|---|---|
| **T1 归档混入盲评包** | `blinding.py` 新增 `_select_current_reports()`:`*.superseded-*` 永不入选;候选须为 JSON 对象+非空白文本+非截断+有终止状态+(给定时)匹配 prompt_version;每 (subject, provider) 恰一条,重复即抛 `PacketSelectionError`;给定 expected_providers 时逐受试者核对模型集合,缺/多即抛。打包失败必须响亮,不再静默装错 | `test_packet_selection.py` 覆盖审计实测泄漏场景(1新+1旧截断→现在恰好3条/受试者且旧文本不出现)、截断、重复、缺模型、异版本、空白文本各自抛错 |
| **T2 参考计算与说明不一致** | 两个 `build_normative_reference*` 均返回 `meta` 块(source/method/excluded/n_subjects/n_points/calibration_family);`reference_source` 与 `reference_meta` 从 meta 派生,**不再凭"传了 normative"推断主队列**;文本新增"Deviation reference actually used"行(LOO 显示真实 137 人+排除名单);主队列定义块中 138/106-109 改标为 COHORT BACKGROUND,与实际参考行区分 | `test_reference_metadata.py`:LOO 渲染 5 人+excluding C03;3 人/101 点自定义参考得 generic 定义(无 138、无校准分位数);仅 source="main_cohort_excel" 时校准文本才附着 |
| **T3 同秒归档碰撞** | `place_record` 归档名唯一化(同秒加 `-2/-3` 计数器),timestamp 可注入测试 | `test_same_second_supersede_keeps_all_versions`:冻结时间戳连续三写,三个版本全保留 |
| **T4 非对象 JSON 崩溃** | `existing_record_valid` 先查 `isinstance(record, dict)`,`report_text` 须为 str;任何畸形内容返回 (False, reason) 而非异常 | `test_non_object_json_rejected_not_crash`:`[]`/`null`/`5`/字符串/数字 report_text 全部安全拒绝 |
| **T5 缺失原因映射补齐** | `DOCUMENTED_NO_ANALOG` 按 (group, subject) 键控:stroke 的 Sub08=TVC11、Sub47=TVC55、Sub48=TVC57 均用文档记载的"无模拟采集"原因;**Sub43 保持原因未知**;healthy/通用同名病例不会误继承 | 键控设计本身排除误用;渲染路径复用 R6 已测逻辑 |
| **T6 请求/响应标识分离** | `GenerationResult` 增 `response_id` 与 `request_id` 并列;anthropic/openai 的 request_id 只取 `_request_id`(openai 不再拿 completion id 冒充),response_id 取 API 对象 id;gemini request_id 留空不借用;`_usage_dict` 经 `_json_safe` 递归保留嵌套明细 | `test_provider_metadata.py` 重写为新语义 5 项(含"不得借用 ID"与嵌套 usage 保留) |

测试总量:28 → **40 项全部通过**。端到端链路(fake provider 生成→cache 留档→supersede→打包→答案表)有专门测试
(`test_end_to_end_generation_to_packets`),不只验证单函数。

**边界声明(按 10.3 要求)**:本批全部为本地验证;真实模型接口兼容性(SDK 实际响应对象的字段)与临床能力均未验证;
个体 toe-off 仍未纳入输入,属已声明的简化(定义块中列为"本次不提供"),阶段解释受此限制。

## 对 handoff v5 第十一节(第四轮审查,T1 收尾)的响应(2026-09-16 第四批增补)

T2-T6 与核心生成流程按 11.1 维持通过,未重复修改。T1 的四项残留逐一闭环:

| 残留 | 改动 | 验收测试 |
|---|---|---|
| 1. 非成功终止仍入包 | `_select_current_reports` 复用 `SUCCESS_STOP_REASONS` 按 provider 校验;未知 provider 直接拒绝(无法核实完成状态时宁可响亮失败);**测试夹具改为各 provider 各自真实成功码**(anthropic=end_turn / openai=stop / gemini=STOP),不再全部 end_turn | `test_content_filter_finish_rejected`(OpenAI content_filter+有文本+未截断 → 拒);`test_unknown_provider_rejected` |
| 2. 损坏归档令匿名化崩溃 | 匿名化模式改由**已选 records** 构建(`_build_strip_patterns_from_records`),不再二次 glob 全目录解析归档;遗留的目录扫描变体仅供单元测试且跳过归档/畸形文件 | `test_corrupt_archives_do_not_break_anonymization`:`{corrupt`/`[]`/`null` 归档共存时有效集合正常打包 |
| 3. 同版本异实验输入混包 | 新增 `expected_tasks`(冻结任务清单:(subject,provider)→各自的 task_hash,不要求跨模型相等);逐记录核对 + 受试者集合与清单比对;两个生成脚本运行时输出 `task_manifest.json`,`load_task_manifest()` 供打包侧加载 | `test_same_version_different_experiment_input_caught`:三份 v2 中一份 user_prompt 不同 → task_hash mismatch 抛错;清单多余受试者 → subject set mismatch 抛错 |
| 4. 旧输出包遗留 | 分级发布:先在 `packets.building-<ts>/` 完整构建,再把既有 `packets/` 整体存档为 `packets.previous-<ts>/`(不删除历史),最后原子改名上线;文件集合/匿名 ID/答案键同批产生 | `test_stale_packets_from_previous_run_do_not_linger`:换受试者集合重跑,当前目录只含新集合,旧集合完整保留在 previous 目录,答案键无旧受试者 |

测试总量:40 → **45 项全部通过**。

**边界(按 11.3)**:本批仍全部为模拟接口本地验证;真实 SDK 在线兼容性未验证,待 T1 收尾确认后按计划做真实小样例;专家参考标准/统计方案/临床解释有效性属后续研究工作。

## 对 handoff v6 第十二节(第五轮审查 F1/F2)的响应(2026-09-16 第五批增补)

| 项 | 改动 | 验收 |
|---|---|---|
| **F1 任务清单阻断打包** | 统一文件约定并落实到共享入口:新建 `src/llm/generation_runner.py` 的 `generate_batch()`,两个真实脚本的生成循环全部迁移其上(顺带消除了两份近似重复的循环代码);清单固定写入 `<reports_dir>/_meta/task_manifest.json`,报告目录根只含报告工件与其 superseded 归档——精确隔离,选择器无需任何宽泛豁免,坏报告照旧被拦 | `test_real_entry_generation_then_packaging`:**用真实共享入口接假 provider** 生成完整目录(6 份报告+_meta 清单),幂等重跑 0 新调用,配置变更触发 supersede,然后用 runner 自产清单直接打包成功;答案键中无 manifest、无归档 |
| **F2 旧答案键被覆盖** | 打包改为**自包含批次目录** `out/batch-<ts>[-N]/`:packets/、答案键、rubric、packaging_manifest(记录 expected_tasks/providers/种子/来源)四件套在 staging 完整构建后原子改名统一发布;历史批次(含其匿名 ID→模型映射)永不触碰;答案键位于批次根、绝不进发给专家的 packets/ 子目录;函数返回批次路径 | `test_batches_are_self_contained_and_history_is_preserved`:两次打包得两个批次,新批次只含新受试者,旧批次答案键逐字节未变、仍可追溯;答案键不在 packets/ 内 |

测试:45 项全部通过(F1 验收按 12.2 要求走真实入口+模拟 provider 的完整目录,非手写报告 JSON)。
12.1 已通过项(成功码校验、损坏归档、异输入拦截、当前包无遗留受试者、T2-T6)未重复修改。

**边界(按 12.3)**:仍为模拟接口本地验证;真实 SDK 在线兼容性、专家/统计方案照旧待后续阶段。

## 第六轮关闭后的过渡工作(2026-09-16 第六批增补)

- **留档补充(§13.2 非阻断项)**:两个入口脚本的 CODE_FILES 补入
  `generation_runner.py` 及**入口脚本自身**(`Path(__file__)`);
  `requirements.lock.txt` 重新冻结,现已包含三家 API SDK(工作环境
  `~/.venvs/gait-emg`,覆盖本地验证与真实生成两用途)。
- **真实 SDK 小样例(用户放行,共 4 次极小调用)**:`scripts/sdk_smoke_check.py`
  逐家 1 次真实调用,校验响应字段与提取语义并写
  `audit/outputs/sdk_smoke_check.json`,失败非零退出。结果:
  - 三家均通过:response_model 回显请求模型;anthropic/openai 的
    request_id(req_…)与 response_id(msg_…/chatcmpl-…)真实分离;gemini
    request_id=None、response_id 存在,符合 T6 设计;嵌套 usage(含 gemini 的
    prompt_tokens_details 列表结构)经 _json_safe 保留且严格 JSON 可序列化。
  - **live 发现(mock 测不出)**:claude-opus-5 的思考 token 计入 max_tokens
    ——32 上限下思考耗 31、正文 1 字符即截断(usage 实证)。冒烟脚本已给
    anthropic/gemini 512 余量并记录;生产参数不改(v1 批 8000 上限 54 调用
    0 截断,且 runner 对截断响亮标记)。
- **专家试评材料草案**:`docs/expert_trial/TRIAL_RATING_PLAN_DRAFT.md`
  (5 例试评病例建议、每例数据卡构成、三层评分结构+INDETERMINATE、
  ≥2 人独立盲评流程)+ `rating_form_template.csv`。明确标注 DRAFT,
  须与用户及专家冻结后执行;5 例均为开发病例,试评仅用于打磨材料。

## 证据文件

- `audit/outputs/fix_verification.json`:P0-1 验收、P0-2 双口径表、
  P0-3 校准复算、P1-2 尺度不变性(由 `scripts/audit_fix_verification.py` 生成)。
- `audit/outputs/v2_input_samples.txt`:Sub50/Sub05(P0-1 靶例)、Sub09
  (完整普通例)、Sub47(全缺失例)的 v2 输入全文。
- `data/normative_calibration_v2.json`:健康校准(plain + 留一法)。
- `tests/test_emg_signal.py`、`tests/test_blinding.py`:新增回归测试。
- `v1_freeze/MANIFEST.sha256`:v1 冻结清单。
