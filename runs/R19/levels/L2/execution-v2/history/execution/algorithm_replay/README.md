# 离线算法附件

完整原件至全场景：

py -3.12 -X utf8 -B code/main.py --raw raw --config config.json --output replay

15件烟雾（本包已解压实跑）：

py -3.12 -X utf8 -B code/main.py --raw raw --items data/smoke_items.csv --vehicles data/vehicles.json --config smoke_config.json --scenario q2_cost --output smoke_replay

只用既有Python3.12/numpy/scipy/python-docx/openpyxl，不联网不安装。尺寸mm，重量kg，费用元每趟；原点右后下。两车型V1/V2、5类同尺寸同单重输入，规则与范围详见研究主README。可行上界不是原问题全局最优，官方测试协议未知。