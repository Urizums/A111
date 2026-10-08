# 正式 schema 适配（冻结准备不改写）

独立检查器由 preparation 拷入本域；初始来源读取仍由本审查者直接从原 DOCX 提取。CSV 将 `*_cm` 转为内部数值坐标，类别/车辆ID原样；另核原轴orientation、task_id、可用车型、单车数量、canonical逐件ID、由坐标重建的单个完整支撑及support_ids追踪、逐车/总目标对实际metrics。

新增具名 gap_cm / pressure_limit / own_mass 参数用于明确参数场景，默认仍3cm/500kg/m²/不计下层自重。own_mass采用论文4.2所述将parent自身质量加入该接触界面分子；它是明确研究替代假设，不声称原题事实。主场景对易碎托举使用single，与作者声明对应；准备中的union另为解释分支，不强迫作者必须采用放宽模型。

适配没有导入作者checker，也未借其passed作独立真值。作者checker仅作为再运行程序路径的一部分，结果另由本域代码独立复算。场景数据必须逐项比对由本审查者原附件生成的同名人工变换，不能作者config自动当原值。偏支撑、道路动态和原连续优化仍无验证，不改变准备限制。
