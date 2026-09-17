# 5例数据卡草稿

打开 index.html 浏览并交互审核全部病例（图和审核功能内嵌，可离线使用）。每例 card.html 可单独分享。
最前面的通用审核区只审一次；导出包含common_rules及五例病例区，common_rules不是第六例受试者。
单例页面也附带同一版通用区，便于独立使用。
先填写专家编号并点击“开始／载入审核”，再逐条接受/修改/删除和补充条目。
完成后导出 JSON 交回研究者；CSV可用Excel查看，JSON可跨设备续填。不同专家使用不同编号。
浏览器暂存不是正式交回，也不会修改磁盘上的原始文件；请务必导出。
每例还提供 PNG/PDF 图、model_system_prompt.txt、model_user_prompt.txt、model_messages.json、
summary.json、facts.json、reference_card.md、checklist_DRAFT.md 和专家可编辑 CSV。

这是专家准备材料，没有模型报告、模型身份或答案键。先由专家审定清单，再开展盲评。
不要将候选“必须描述”条目直接作为扣分标准；不得因模型没有提及专家补充图或未提供的
详细分位数而扣分。核查数值时考虑模型输入的显示精度，不能用机器全精度追责。

模型输入快照与当前正式入口使用相同函数；任何后续prompt/数据变动都应重新生成新版本，
并核对实际报告中保存的system_prompt/user_prompt，而不是假定永远一致。
健康Sub49使用排除本人的137人参考，各肌肉有效n另列；经验校准分布与本例参考成员不是同一个概念。
此项目仅评估给定证据下的报告忠实性与解释边界，不验证诊断或治疗。

生成命令示例：
`python scripts/build_expert_trial_package.py --verified-cache --out docs/expert_trial/data_cards_vNEXT`
也可省略 --verified-cache 直接读取发布Excel/MAT。已有目录不覆盖，以保留专家编辑。
manifest.json记录来源、源码和所有交付物哈希；缓存不在Git中，需本地数据或选择直接读取。
