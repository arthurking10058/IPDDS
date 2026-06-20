# IPDDS 瓶盖缺陷检测与数据看板

IPDDS 是一个围绕瓶盖质检场景整理出的本地演示项目，主线聚焦于三件事：摄像头采集画面、调用 YOLO 模型识别瓶盖缺陷、把检测记录写入 CSV 并在 Streamlit 页面中做统计展示。

## 项目主线

- 实时视频采集：通过 `streamlit-webrtc` 接入摄像头画面
- 缺陷识别：调用 `weights/best.pt` 对单帧图像做检测
- 数据落盘：将检测时间、类型、置信度、坐标写入 `defect_data.csv`
- 数据看板：在同一页面中展示缺陷总览、类型占比、时间统计和筛选导出

公开入口保持为：

```bash
streamlit run IPDDS.py
```

## 目录结构

```text
IPDDS/
├─ IPDDS.py                    # 兼容入口，负责启动 ipdds.app
├─ ipdds/                      # 主线代码包
│  ├─ app.py                   # 页面入口与动作编排
│  ├─ constants.py             # 路径、字段、时间范围等常量
│  ├─ data_store.py            # CSV 记录读写与统计查询
│  ├─ inference.py             # 模型加载、推理与结果整理
│  ├─ ui_sections.py           # 页面组件拆分
│  ├─ smoke_check.py           # 轻量自检脚本
│  ├─ summary_report.py        # 摘要导出脚本
│  └─ stats_report.py          # 统计导出脚本
├─ weights/
│  └─ best.pt                  # 当前使用的检测权重
├─ defect_data.csv             # 检测记录数据
├─ archive/
│  └─ notebooks/               # 实验与分析 notebook 归档
├─ record/
│  └─ 项目改造升级计划.md
├─ defect_data_manager.py      # 兼容旧调用的数据管理封装
└─ yolo_model.py               # 兼容旧调用的推理封装
```

## 运行方式

推荐先在项目根目录重建与当前验证环境一致的虚拟环境：

```bash
python -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
```

然后使用该环境启动应用：

```bash
.\.venv312\Scripts\python.exe -m streamlit run IPDDS.py
```

如果当前仓库里的 `.venv312` 已经存在，也可以直接复用：

```bash
.\.venv312\Scripts\python.exe -m streamlit run IPDDS.py
```

启动后可以完成：

- 实时视频预览
- 拍摄当前帧
- 保存原图或检测结果图
- 调用模型做缺陷识别
- 在“检测页”和“统计页”两个主视图之间切换
- 生成缺陷统计图和筛选结果
- 查看检测记录摘要，包括时间范围、高峰时段、主要缺陷和最近记录概览

## 本轮升级补充

- 导出区改为直接使用下载按钮，减少先点按钮再二次下载的操作跳转
- 导出的 CSV 使用 `utf-8-sig` 编码，兼容 Excel 直接打开中文列名
- 导出文件名统一追加时间戳，区分不同批次结果
- 数据层兼容部分旧字段命名，减少历史 CSV 的迁移成本
- 增加 `ipdds.smoke_check` 轻量自检脚本，可先验证 CSV 读写链路
- 增加 `ipdds.summary_report` 摘要脚本，可独立输出检测记录摘要
- 增加 `ipdds.stats_report` 统计脚本，可独立输出摘要与时间序列统计
- 将原有单页主界面拆成“检测页 / 统计页”双视图，降低单页复杂度

可执行的轻量检查命令：

```bash
python -m ipdds.smoke_check
```

如果当前环境已经安装 `ultralytics`，还可以继续检查模型加载：

```bash
python -m ipdds.smoke_check --check-model
```

在当前仓库内，也可以直接使用已验证环境执行：

```bash
.\.venv312\Scripts\python.exe -m ipdds.smoke_check --check-model
```

检测记录摘要也可以独立导出为 JSON：

```bash
.\.venv312\Scripts\python.exe -m ipdds.summary_report
```

如需离线导出统计时间序列与摘要，可运行：

```bash
.\.venv312\Scripts\python.exe -m ipdds.stats_report --time-range 30分钟 --interval 5分钟
```

## 数据记录字段

`defect_data.csv` 当前使用以下字段：

- `时间`：检测记录写入时间
- `类型`：检测类别，当前主线中可见 `cap`、`dirty`、`scratch`
- `置信度`：模型输出置信度
- `x1`、`y1`、`x2`、`y2`：检测框坐标

## 归档材料说明

- `archive/notebooks/`：保留实验与分析 notebook，用于回看探索过程
- `record/`：保留升级计划与阶段性整理记录

这些内容都不参与主线运行，只作为项目过程留档。

## 当前限制

- 当前主线虽然已拆成“检测页 / 统计页”双视图，但仍保留在同一个 Streamlit 入口中
- 识别记录使用 CSV 本地存储，适合演示和轻量分析，不适合高并发场景
- 模型推理仍然依赖本地权重文件和当前 Python 环境
- 当前摘要仍基于 CSV 记录聚合，尚未细化到批次维度或班次维度
- 旧 `.venv` 不再作为推荐运行环境，当前建议使用 `.venv312`

## 后续可继续升级

- 将当前摘要继续细化到批次维度或班次维度
- 视需要逐步退出 `defect_data_manager.py`、`yolo_model.py` 兼容层
- 收敛 `requirements.txt`，使其与当前推荐环境 `.venv312` 的依赖组合完全一致
