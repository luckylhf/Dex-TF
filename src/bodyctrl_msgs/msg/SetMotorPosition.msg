uint16 name  # MotorName
float32 pos  # rad
float32 spd  # 期望速度（协议标注 rpm；实际单位以固件为准，见 docs/protocol.md §3）
float32 cur  # A