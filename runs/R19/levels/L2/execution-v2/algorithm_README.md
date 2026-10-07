# 可运行算法附件（L2 v2）
离线Windows Python3.12，已有numpy/scipy/python-docx/openpyxl；不安装、不联网。
尺寸整数mm，质量kg，费用元/趟；CSV每件ID/同质类型/类别/原尺寸/单重，JSON车厢内尺寸/载重/费用/30mm间隙。
从本目录运行：
py -3.12 -X utf8 -B code/main.py --raw raw --config configs/main.json --output results/full
py -3.12 -X utf8 -B code/check_cases.py
py -3.12 -X utf8 -B code/validate.py --placements results/full/selected/q2_cost/placements.csv --items data/items.csv --vehicles data/vehicles.json --output results/full/external_validation.json
--scenario all默认完成四个全运和两车型单车集；--scenario q2_cost只运行单个费用主问题，少了其它场景提供的候选，可能得到更差合法上界。--items/--vehicles/--config/--output可指定接口。
主种子19、22随机启动+3固定权重，45秒每场景MILP；外层总耗时更长。有限库、限时及容差不证明全局最优或次级库内最优。库存严格等式，全部输出独立构造代码的checker重算后导出。单车点为搜索非支配集。
新保护块与累计传载假设在论文，全部底面充分支撑/均匀密度/接触面积分担为保守工程模型，未验证动态材料安全。易碎地板/固定方向可config声明；定向仅012。未知官方I/O、AI规则/投稿授权，附件2缺完整订单字段，仅资格审计。
本ZIP包含真实源码、原三官方文件、输入与配置，没有预装答案。完整论文、对照9条、当前36参数、原36历史/首审、失败与资源账在外部execution-v2研究交付包，不要求此小算法ZIP单独包含全部研究历史。
