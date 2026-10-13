# 水下实例分割实验

更新日期：2026-10-13。本文统一记录当前状态、实验协议、结果、历史步骤和后续入口。历史记录不作为当前启动指令。

## 1. 当前状态与下一步

**Mask2Former-R50 在 UIIS 上的正式基线训练及评估已完成：36 轮、70884 次迭代，691 张测试图，mask AP 32.6 / AP50 47.6 / AP75 35.3。尚未加入 DSGAT、MFRM、BLL，未复现 WaterMask，也未开展第二研究点。**

- 已完成：环境/GPU 算子检查、数据下载与审计、短训练及恢复测试、正式入口验证、36 轮训练、最终全量评估、前 6 张图片复核、WaterMask 公布结果和部分配置核对。
- 未完成：更清晰的实例可视化、全数据集误差归因、边界专用指标、模块适配/消融、多随机种子验证、WaterMask 同环境复现、第二研究点和论文正文。
- 下一步优先在本地利用已保存预测，改进诊断展示，分析漏检、错分类、实例拆分与轮廓问题，再确定第一个模块；这项工作尚未执行。
- 最后检查时，训练与评估均正常结束。用户随后询问关机，已告知可以普通关机；**是否已实际关机未核验**。本轮只整理文档，未连接或启动服务器。
- 最终权重最后确认保存在服务器，**尚未完成本地权重备份**。本地已有日志、指标、原始预测和对照图。

优先阅读：[正式评估报告](reports/uiis-baseline-36e-evaluation/report.md)、[完整指标](reports/uiis-baseline-36e-evaluation/metrics.json)、[训练完成核验](reports/training-completion-review.json)。这些产物被 Git 忽略，只克隆 GitHub 仓库不会获得它们。

## 2. 研究目标与讨论范围

任务是水下实例分割：识别类别，并分别分割每一个物体。用户希望控制实验时间、为秋招留出时间，论文希望包含两个研究点、约 100 页；这是规划要求，不是已完成工作量或毕业保证。

| 研究线 | 已讨论内容 | 实际状态 |
| --- | --- | --- |
| 第一研究点 | UIIS + Mask2Former，逐步适配 WaterMask 的 DSGAT、MFRM、BLL，验证细节及轮廓等改善 | 基线完成；模块插入位置、适配实现及收益未确定 |
| 第二研究点 | DINOv2 / DiveSeg 或 TIDE 辅助分析等候选 | 未最终确定、未运行；误差分析工具本身不自动构成独立研究贡献 |
| 早期备选 | 水下图像与密集标注生成论文启发的数据生成方向 | 仅讨论，未实施，不是当前主线 |

不预设 Mask2Former 一定边界差，也不预设移植模块一定有效。已有模块必须注明来源；直接拼接、页数或实验数量不能单独证明创新。当前模型已有预训练及完整架构，“还没加入自己的模块”不等于模型没有经过优化。

## 3. 数据集与固定使用规则

来源：[WaterMask 官方仓库](https://github.com/LiamLian0727/WaterMask)提供的[原版 UIIS](https://huggingface.co/datasets/LiamLian0727/UIIS)，不是 UIIS10K。固定版本 `44ca5db46599f14faf8e57643014664435823738`；清单 `data/UIIS/download-manifest.json`。

| 项目 | 数量及规则 |
| --- | --- |
| 训练集 | 3937 张、24626 个实例；annotations/train.json |
| 测试集 | 691 张、3784 个实例；annotations/val.json，文件名 val 但官方用途是测试 |
| 文件核验 | 本地及服务器 4631 个清单文件哈希通过；不是 4631 张图片 |
| 结构审计 | 全部图片读取、尺寸和掩码解码通过，结构错误 0、空掩码 0 |
| 已知重复 | train/XL_266.jpg 与 val/XL_679.jpg 字节完全相同；未排查近重复 |
| 用户确认规则 | 保留官方划分和这对图片，不删除、不排除；所有对照使用同样规则 |
| 内部验证集 | 未另划；早期去重及约 10% 内部验证方案仅被记录，未执行，已取消 |
| 本次模型选择 | 固定最后第 36 轮权重，训练期间不评估测试集、不根据测试 AP 选 best |

重复图片 SHA256：`ce7d3d5b5c759496d903626329a7ce9ea3cde946853596a3c9fa200c28802af8`。保留是遵循已确认的数据协议，不代表已消除泄漏风险或证明精度提升；论文需披露。

| ID | 类别 | 训练实例 | 测试实例 | 本次分割 AP |
| --- | --- | ---: | ---: | ---: |
| 1 | fish | 14709 | 2040 | 48.2 |
| 2 | reefs | 7251 | 1241 | 33.9 |
| 3 | aquatic plants | 1052 | 203 | 12.9 |
| 4 | wrecks/ruins | 211 | 37 | 21.4 |
| 5 | human divers | 499 | 97 | 64.6 |
| 6 | robots | 73 | 17 | 26.6 |
| 7 | sea-floor | 831 | 149 | 20.8 |

类别明显不均衡，需保留分类别指标。下载曾遇大 JSON 不完整、镜像限流；补传后与官方哈希匹配，服务器从本地补传 1629 个缺失文件后完成全量复核。脚本支持 `--audit-only`，默认并发 8，429 等待重试。证据：[uiis-audit.json](reports/uiis-audit.json)。`reports/uiis-ground-truth-train.jpg` 和 `reports/uiis-ground-truth-val.jpg` 是人工标注示例，不是预测。

## 4. 正式模型、预训练与训练参数

完整结构为 MMDetection Mask2Former，ResNet-50 是骨干。未加入自定义模块，但已修改类别和训练设置，不能说所有参数都没变。

| 参数 | 实际配置 |
| --- | --- |
| 基础配置 | mask2former_r50_8xb2-lsj-50e_coco.py；名称指原官方配置，不表示本次用 8 卡或训练 50 轮 |
| 初始化 | COCO 实例分割整模型预训练；80 类分类层改为 7 类并重新初始化，兼容参数加载 |
| 输出类别 | 7 个 thing 类，0 个 stuff 类 |
| 硬件/精度 | 单卡 V100 32GB，FP32 |
| 数据加载 | batch 2、workers 2；每轮 1969 步，最后一批 1 张，不丢弃 |
| 训练处理 | 官方 LSJ 随机缩放比例 0.1–2.0、1024×1024 裁剪等流程 |
| 测试处理 | 保持比例，尺度 (1333, 800) |
| 优化器 | AdamW，基础学习率 0.0001，骨干倍率 0.1，关闭自动学习率缩放 |
| 预算/调度 | 36 轮、70884 步；第 27/33 轮学习率各乘 0.1 |
| 随机种子 | 20261012；目前只做一个种子，未做多次重复 |
| 权重保存 | 每轮保存，根目录保留最近 3 份；另在 milestones 保存 12/24/36 轮 |
| 测试与选模 | 不在训练期间测试，不选 best；最后固定 epoch_36 评估 |

配置入口：[prepare-uiis-baseline.py](scripts/prepare-uiis-baseline.py)。完整解析配置：[evaluation-config.py](reports/uiis-baseline-36e-evaluation/evaluation-config.py)。服务器正式目录另有 `config-first.py`、`config-resume.py`、`run-protocol.json`。

初始权重：`mask2former_r50_8xb2-lsj-50e_coco_20220506_191028-41b088b6.pth`；SHA256 `41b088b62838c986004f94bab2870395b669ec6bd11b6590369b838b0de06879`。正式训练从该权重开始，没有接续 100 步排错模型或 20 步性能检查权重。

## 5. 分阶段实验与验收证据

| 阶段 | 执行和结果 | 证据 |
| --- | --- | --- |
| 环境 | 导入、CUDA 可变形注意力前向/反向、NMS、pip check 通过 | [环境检查](reports/environment-check.txt)、[依赖快照](reports/environment-freeze.txt) |
| 单图演示 | COCO 普通场景；显示阈值 0.5 时 20 个实例；约 2.78 秒、峰值已分配约 1197 MiB，仅验证推理 | [summary](reports/demo-mask2former/summary.json)、同目录 input.jpg / prediction.jpg |
| 短训练 | 512 尺度、batch 1、FP32、AdamW 0.0001、无调度；50 步保存后新进程恢复到 100 步，全部 691 张评估 | [50 步](reports/uiis-smoke-50.json)、[100 步](reports/uiis-smoke-100.json)、[权重检查](reports/uiis-smoke-checkpoints.json) |
| 短训练指标 | mask AP 4.7 / AP50 8.5；bbox AP 4.6；仅测试流程，不是正式基线 | [短训练日志](reports/uiis-smoke-console.log) |
| 容量检查 | 20 步、1024 LSJ、batch 2；损失有限，无 OOM；峰值已分配 10558.5 MiB，预留 11230 MiB；预热后纯计算 0.694 秒/步 | [性能报告](reports/uiis-baseline-profile.json) |
| 正式入口隔离验证 | 4 张图、5 小轮；首轮停止/恢复、优化器/调度状态、衰减、最近 3 份及阶段备份、防重复/覆盖均通过 | [入口验证](reports/training-entry-verification.json) |
| 正式前检查 | 4631 文件、预训练哈希、15 源文件同步、GPU 算子、加载器/类别映射、配置、锁/进程/磁盘通过 | [preflight](reports/formal-training-preflight.json)、[源码清单](reports/preflight-code-manifest.json) |
| 首轮 | 1969 步，exit=0，权重可读，模型/优化器有限、调度存在；约 24 分钟 | [首轮核验](reports/first-epoch-review.json) |
| 36 轮完成 | 70884 步，exit=0；恢复状态一致，最终模型有限、优化器/调度存在，12/24/36 备份存在 | [续训结果](reports/result-resume.json)、[完成核验](reports/training-completion-review.json) |
| 全量评估 | 完整覆盖 691 个图像 ID，退出 0，权重哈希与完成检查一致 | [指标](reports/uiis-baseline-36e-evaluation/metrics.json)、[退出码](reports/uiis-baseline-36e-evaluation/exit-code.txt) |

短测试不证明已收敛，也不代表全数据显存上限。首轮第 50 步日志 loss 43.4699、第 1950 步 25.92，不能代替测试精度。完成检查文件中的 `accuracy_evaluated=false` 是当时尚未评估的历史状态，后来评估以独立 metrics.json 为准。

正式时间（北京时间）：2026-10-12 23:30:33 启动，23:54:30 首轮结束；23:57:55 用户确认后恢复，2026-10-13 13:41:41 正常结束。含人工暂停总历时约 14 小时 11 分钟。评估于 14:17 完成，记录测试耗时约 179.38 秒，不含全部启动和结果整理开销。

正式服务器目录：`/root/autodl-tmp/underwater-segmentation/work_dirs/uiis_baseline_r50_36e`。最终 `epoch_36.pth` 为 575721052 字节，SHA256 `53f9382f8db706be2d91da38b765b6bd5b8f26c33a2434f9a26e795fbbb8376f`。

历史首轮哈希：`2662f3b7584c642e8fc1809254d099ad559c33797733ffb1fdcc91f81b82b733`。滚动保存会清理早期权重，不能根据历史核验报告声称 epoch_1 目前仍存在。

## 6. 正式结果与实际问题

| 任务（0–100 分） | AP | AP50 | AP75 | 小目标 AP | 中目标 AP | 大目标 AP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 实例分割 segm（主要指标） | 32.6 | 47.6 | 35.3 | 8.2 | 25.1 | 47.8 |
| 检测框 bbox | 34.3 | 47.6 | 35.3 | 9.3 | 29.8 | 47.4 |

[结果目录](reports/uiis-baseline-36e-evaluation/)包含 report.md、metrics.json、predictions.bbox.json / predictions.segm.json、evaluation-config.py、console.log、exit-code.txt、examples/0.jpg 至 5.jpg。

这是一组单次可追溯基线成绩，不意味着视觉效果令人满意、预算最优或全部类别都表现好。训练充分性、多种子稳定性、边界专用指标和跨数据集泛化尚未验证。

### 六张示例复核

预测计数限显示阈值 score >= 0.5，不改 AP 评价。

| 图片 | 人工实例 | 显示预测实例 | 观察 |
| --- | --- | --- | --- |
| L_1000.jpg | fish 2、reefs 4、sea-floor 2 | fish 2、reefs 3 | 鱼主体较接近，海底未显示，礁石范围和划分有偏差 |
| L_1001.jpg | reefs 1 | reefs 1 | 上方细长部分明显缺失 |
| L_1025.jpg | reefs 1、fish 4 | reefs 1、aquatic plants 1 | 四条鱼均未达显示阈值，最高鱼分数 0.410；不是完全没有鱼候选 |
| L_1029.jpg | reefs 1 | fish 1、reefs 1 | 同一目标附近出现不同类别，需进一步掩码匹配；不擅自改标注 |
| L_1032.jpg | fish 1 | fish 1 | 主体轮廓较接近，相对较好 |
| L_1046.jpg | reefs 5 | reefs 15、aquatic plants 1 | 数量明显失配，需量化多报、拆分、重叠，不能只归因于边缘 |

绘图按类别着色，没有实例编号、类别文字或分数；重叠透明掩码会改变颜色，不易分辨同类实例。展示问题存在，但不能掩盖真实预测错误。改版可视化和全测试集错误占比统计尚未执行。

## 7. 术语与论文比较规则

**COCO** 有两个用途：模型先在 COCO 上学习通用分割；本次 UIIS 测试使用 COCO 评分规则。`coco/segm_mAP` 指评价器，不表示用普通场景替代水下图片考试。

- **IoU**：预测区域与人工区域的交集面积 / 并集面积。
- **AP50 / AP75**：用 IoU >= 0.50 / 0.75 匹配类别正确的实例，再综合预测排序、误报和漏检计算精度。
- **主 AP**：在 0.50、0.55……0.95 十个阈值及类别上平均，不是像素正确率或单张图的重合率。
- JSON 的 0.326 写成 32.6 AP；差值 6.2 是 AP 点数，不是相对提升 6.2%。
- 图上置信度阈值 0.5 与 AP50 的 IoU 0.5 不同；AP75 更严格，但不等于边界专用指标。

定义来源：[COCO 评估实现](https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/cocoeval.py)。

### WaterMask 初步比较

| 方法 | mask AP | AP50 | AP75 | 来源 |
| --- | ---: | ---: | ---: | --- |
| WaterMask R50-FPN，3× | 26.4 | 43.6 | 28.8 | 官方公布，未自行复现 |
| WaterMask R101-FPN，3× | 27.2 | 43.7 | 29.3 | 官方公布，未自行复现 |
| 本次 Mask2Former R50，36 轮 | 32.6 | 47.6 | 35.3 | 实测 |
| 本次减 WaterMask R50 | +6.2 | +4.0 | +6.5 | AP 点数差值 |
| 本次减 WaterMask R101 | +5.4 | +3.9 | +6.0 | AP 点数差值 |

来源：[官方结果表](https://github.com/LiamLian0727/WaterMask#main-results)。2026-10-13 已核对原 mmdet2 分支 [R50 3× 配置](https://raw.githubusercontent.com/LiamLian0727/WaterMask/mmdet2/configs/_our_/water_r50_fpn_ms3x.py)：36 轮、27/33 衰减、SGD lr=0.0025、短边 480–800 多尺度缩放；[1× 基础配置](https://raw.githubusercontent.com/LiamLian0727/WaterMask/mmdet2/configs/_our_/water_r50_fpn_1x.py)继承 Mask R-CNN 并换为 WaterRoIHead / WaterMaskHead。当时 README 当前分支的 3× 配置链接失效，因此读取原分支。

本次使用 AdamW、1024 LSJ 和 COCO 整模型预训练。对方实际预训练加载及运行覆盖参数仍未完整核对，不能默认相同，也不能声称对方没有 COCO 预训练。同骨干、同轮数不等于全部条件相同；+6.2 AP 不能归因于尚未实现的自有模块。

### 论文中可以怎样比较

可以引用官方结果作外部参考，但注明来源、是否复现、训练差异。不同完整方法可使用各自训练策略；数据划分、任务和评分规则应统一，额外预训练数据需披露。当前不是完全控制训练条件的对照实验。

| 比较 | 回答的问题 | 条件要求 |
| --- | --- | --- |
| 最终方法 vs WaterMask 等 | 与已有方法相比性能如何 | 标明官方/复现结果和训练差异，条件允许时同环境复现 |
| 原版 Mask2Former vs 改进版 | 自己的设计是否有效 | 尽量固定数据、预训练、预算、优化器、增强、评价器和种子，仅改变模块 |
| 逐模块消融 | 每一部分有何贡献 | 分别和组合测试，保留失败/无增益记录，不只报最好组合 |

当前 32.6 属于原版基线，不是自己的创新成果。WaterMask 内部模块有效不代表移植必然有效。未来调参和选模规则仍需明确；不能反复依据测试集选配置后声称测试完全独立。

## 8. 工作目录、硬件与完整源码

- 本地：`C:/Users/Lenovo/Documents/Codex/2026-10-09/new-chat-2/underwater-segmentation`，VS Code 与 Codex 共用唯一代码主目录。
- 服务器：`/root/autodl-tmp/underwater-segmentation`。
- GitHub：[XilunWang/Master-thesis](https://github.com/XilunWang/Master-thesis)，master 分支。
- 已用硬件：AutoDL 047 机，V100-PCIE-32GB 单卡、CPU 6 核、内存 25GB、系统盘 30GB、数据盘 50GB。截图 1.88 元/小时为历史价格，不保证后续不变。
- 环境：Python 3.10、PyTorch 2.1.2+cu121、torchvision 0.16.2+cu121、NumPy 1.26.4、MMCV 2.1.0、MMEngine 0.10.7、MMDetection 3.3.0。
- 驱动 535.54.03；nvidia-smi 的 CUDA 12.2 与 PyTorch 的 CUDA 12.1 含义不同。
- `.venv` 用 `--system-site-packages` 复用基础环境，非完全隔离；更换镜像后需重新验证。[requirements.txt](requirements.txt)固定新增依赖，环境快照在 reports。

本仓库不是 Mask2Former 全部源码。完整实现来自服务器 `.venv/lib/python3.10/site-packages/` 中 mmdet/mmengine 和 PyTorch/MMCV。已核对 `mmdet/models/detectors/mask2former.py`、`mmdet/models/dense_heads/mask2former_head.py`、`mmdet/models/layers/msdeformattn_pixel_decoder.py`、`mmengine/runner/runner.py` 等；入口文件很短不代表网络很小。证据：[源码核查](reports/baseline-readiness-audit.json)。自定义模块应放本地项目并注册，不直接改服务器 site-packages。

### 脚本索引

| 文件 | 用途及限制 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 协作、权限、同步和启动规则 |
| [connect.ps1](connect.ps1)、[ssh.config](ssh.config) | SSH 登录及别名 |
| [setup-ssh.ps1](setup-ssh.ps1) | 首次安装公钥，已成功，不需每次重做 |
| [check-server.ps1](check-server.ps1) | 只读检查 SSH/GPU/项目路径/磁盘，不替代算子和全量数据验证 |
| [sync-code.ps1](sync-code.ps1) | 按 Git 忽略规则上传代码，非实时同步、不传忽略目录 |
| [run-demo.ps1](run-demo.ps1) | 同步、单图推理、回传演示结果 |
| [install-env.sh](scripts/install-env.sh)、[verify-env.py](scripts/verify-env.py) | 安装依赖及 GPU 算子检查 |
| [demo-mask2former.py](scripts/demo-mask2former.py) | COCO 单图推理 |
| [download-uiis.py](scripts/download-uiis.py)、[validate-uiis.py](scripts/validate-uiis.py) | 数据下载校验及结构审计 |
| [train-uiis-smoke.py](scripts/train-uiis-smoke.py)、[run-uiis-smoke.sh](scripts/run-uiis-smoke.sh) | 50→100 步排错，重跑会覆盖同名 reports 报告 |
| [prepare-uiis-baseline.py](scripts/prepare-uiis-baseline.py) | 生成配置；--profile 执行 20 步，不是正式入口 |
| [train-uiis.py](scripts/train-uiis.py) | first/resume、状态检查、锁和阶段备份 |
| [run-training.sh](scripts/run-training.sh)、[training-worker.sh](scripts/training-worker.sh) | screen 后台及状态/退出码 |
| [test-training-entry.py](scripts/test-training-entry.py) | 4 图/5 小轮管理逻辑验证 |
| [continue-overnight.py](scripts/continue-overnight.py)、[run-overnight.sh](scripts/run-overnight.sh) | 历史自动接续，已取消，不重启 |
| [evaluate-uiis.py](scripts/evaluate-uiis.py)、[evaluation-worker.sh](scripts/evaluation-worker.sh) | 固定最终权重全量评估；metrics 已存在则拒绝覆盖 |
| [report-uiis-evaluation.py](scripts/report-uiis-evaluation.py) | 从指标和预测绘图、生成报告，服务器环境实测通过 |

## 9. 保存位置、Git 与关机

| 内容 | 本地 | 服务器 | GitHub |
| --- | --- | --- | --- |
| 代码 | 主工作副本 | 评估阶段代码已上传 | 提交/推送管理 |
| README / AGENTS | 本轮全面整理 | 本轮未连接，待重连同步最新文档 | 本轮提交及推送结果另记 |
| UIIS 图片/标注 | 已下载核验 | 已上传核验 | 忽略，不上传 |
| 指标/日志/原始预测/示例图 | 已下载 reports | 已保存 | 忽略，不随 push 备份 |
| 正式权重/阶段备份 | 尚未下载备份 | 完成核验时存在 | 忽略，不上传 |

普通关机与释放/重置不同。平台先前截图提示关机 15 天后释放，长期停用前需核实保留期限并备份权重；不能把 GitHub 代码同步当成模型和报告备份。脚本不自动关机，本轮未代操作开关机或确认电源状态。

本轮开始时 `master` 与本地已知 `origin/master` 同为 `a957686`，但未在线 fetch，不能把远程跟踪引用当成实时服务端状态。此前 Codex 自动 push 多次因凭据管理器 `NtCreateDirectoryObject 0xC0000022` 失败，不能据此断言用户没有通过其他方式同步。项目代理 `http://127.0.0.1:7890` 曾解决 GitHub 连接超时；凭据调用失败是另一问题。本轮新文档已本地提交；实际 git push origin master 再次因凭据管理器 0xC0000022 失败，未完成自动推送。不强推覆盖远程。

## 10. 重连与执行入口

用户说“服务器开启了”后，先确认网络和项目私钥读取授权；必要时定向申请，不要求完全访问、不改 DENY ACL、不复制私钥绕过权限、不重复安装公钥。然后在本地项目目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File ./check-server.ps1
powershell -ExecutionPolicy Bypass -File ./connect.ps1
```

服务器别名 underwater-gpu，地址 region-46.seetacloud.com、端口 27686；若平台改变以最新登录信息为准。密钥和 known_hosts 在忽略目录 `.local/`，主机指纹变化需核实。此前重连约 0.99 秒、关机再开机约 1.57 秒成功，不保证跨应用重启权限永久生效；本机私钥访问失败不能归因为服务器关机。

代码同步：

```powershell
powershell -ExecutionPolicy Bypass -File ./sync-code.ps1
```

覆盖远程同名文件，不删除旧文件；源码改名/删除需核对远端。数据传输与结果下载是独立步骤。不要在两端各自修改同一份代码。

服务器状态检查：

```bash
cd /root/autodl-tmp/underwater-segmentation
bash scripts/run-training.sh status
cat reports/uiis-baseline-36e-evaluation/exit-code.txt
```

必要时用 `.venv/bin/python scripts/verify-env.py` 与 `.venv/bin/python -m pip check` 复验环境，不必每次重装。

正式历史入口 `bash scripts/run-training.sh first` / `resume` **已完成，不再执行**。first 拒绝覆盖已有目录；resume 拒绝满预算或协议不同。恢复核对优化器/调度和进度，不保证随机增强与不中断训练逐位一致。新实验需要独立配置和目录。

评估入口 `.venv/bin/python scripts/evaluate-uiis.py` 因现存 metrics.json 会拒绝覆盖，不删除结果绕过。报告入口 `.venv/bin/python scripts/report-uiis-evaluation.py` 会重写报告及图，后续修改展示时先保留旧结果。

旧 uiis-overnight 监控已取消，不重启。screen 后台任务不依赖本机/SSH 在线；GPU 工作运行时需服务器开机，任务结束可普通关机。工作流程：本地修改 → 必要检查 → 同步服务器 → 执行核验 → 取回结果 → 更新 README → 提交/推送。GitHub 与服务器同步互相独立。

## 11. 完整工作记录

时间为北京时间；无准确时分的记录只写日期，不补造时间。历史未完成状态已被后续结果取代。

| 时间 | 步骤/决策 | 当时结果与证据 |
| --- | --- | --- |
| 前期讨论，确切日期未记录 | 水下实例分割、WaterMask/Mask2Former、生成数据和第二研究线讨论 | 选择 UIIS + Mask2Former 主线；第二点仍待定 |
| 2026-10-12 | 本地项目、Git init、SSH 与同步脚本 | 55c6c0a；首次公钥脚本引号处理失败，修正后 PUBLIC_KEY_INSTALLED / SSH_KEY_OK |
| 2026-10-12 | 确定每步更新 README、提交和同步要求 | 18c76e7；GitHub 与训练服务器分别同步 |
| 2026-10-12 | 固定依赖安装/GPU 算子检查 | 050a6d7；导入、前后向、NMS、pip check 通过 |
| 2026-10-12 | 权重与 COCO 单图演示 | 97bdcfc；服务器 GitHub 超时，经本地下载上传后完成 |
| 2026-10-12 | Git 网络排查、交接文档整理 | bf5b98f、a41d12e；代理解决连接超时，自动凭据调用仍失败 |
| 2026-10-12 | UIIS 下载、补传及全量审计 | 59d3bc4；哈希/结构通过，发现一对跨划分重复 |
| 2026-10-12 | 50→100 步保存/恢复/全量测试 | 5737383；UIIS_SMOKE_ALL_OK，mask AP 4.7，仅排错 |
| 2026-10-12 | 曾提出去重和内部验证方案 | 4f07b3b；只记录，未执行 |
| 2026-10-12 | 用户明确保留原始划分和重复图片 | a6ee016；取代旧方案，所有对照共用规则 |
| 2026-10-12 | 候选配置与 20 步容量检查 | 28a0750；1024 LSJ / batch 2 / FP32 通过，当时还未正式训练 |
| 2026-10-12 晚间 | SSH 本机私钥权限失败排查 | 8859256、8b7e8ea、b834e45；定向授权后恢复，未改 DENY，未证实与服务器关机有因果关系 |
| 2026-10-12 | 固化重连流程 | f54d0fc；新增 check-server.ps1 及 AGENTS 约定 |
| 2026-10-12 23:15 | 用户关机再开机验证 | 878ac33；约 1.57 秒 SERVER_READY，未测试跨应用重启授权持久性 |
| 2026-10-12 晚间 | 正式训练就绪及源码核查 | 93ad008；发现当时缺少正式入口，已有脚本仅生成配置/运行 20 步，后续补齐 |
| 2026-10-12 23:22–23:24 | 正式入口及独立恢复测试 | 63d2bd4；4 图/5 小轮，保存、恢复、保留、防重复/覆盖通过 |
| 2026-10-12 23:29 | 正式前全面复核 | 5e165b5；数据、权重、15 文件、环境、配置和空闲锁/进程/磁盘通过；平台余额/定时关机未核验 |
| 2026-10-12 23:30:33 | 正式首轮启动 | b24fec7；screen 后台，另次 SSH 确认推进，首轮保存后停止 |
| 2026-10-12 23:35 | 当时要求自动验收后续训 | 37ab8f0；门控自测通过，监控 waiting_for_first_epoch，当时尚未实际续训 |
| 2026-10-12 23:40 | 用户改为首轮后暂停共同检查 | d260e15；停止 uiis-overnight、释放监督锁，保留训练进程；自动方案取消 |
| 2026-10-12 23:54:30 | 首轮完成及人工验收 | 8fc9c8c；1969 步、exit=0、权重/数值通过；未算首轮 AP |
| 2026-10-12 23:57:55–23:58:10 | 用户同意后继续剩余 35 轮 | de6e3cc；epoch_1 恢复，RESUME_STATE_VERIFIED；不是旧监控自动接续 |
| 2026-10-13 08:07 | 训练健康巡检 | 913421b；第 22 轮 1500/1969 步，约 60.4%，无发现阻塞；当时 ETA 仅估计 |
| 2026-10-13 13:41:41 | 36 轮全部结束 | 控制台 END exit=0，70884 步 |
| 2026-10-13 14:09 | 完成结果与权重核验 | f688863；最终模型可加载、有限值、优化器/调度及阶段备份存在；报告取回 |
| 2026-10-13 14:17 | 用户授权后全量评估和报告 | 9a68157；691 张，mask AP 32.6；指标、预测、日志、前 6 张图取回 |
| 2026-10-13 评估后 | 用户询问关机 | 已说明可普通关机，未代操作；是否关机未核验，权重待备份 |
| 2026-10-13 | 复核前 6 张效果 | 8316630；记录真实错误及展示局限，不改模型或指标 |
| 2026-10-13 | WaterMask 公布值比较 | 42a4b97；R50 AP 数值差 +6.2，仅外部参考，未复现 |
| 2026-10-13 | AP 定义及 3× 比较口径核实 | a957686；3×=36 轮，训练策略不同，预训练未完全对齐 |
| 2026-10-13 | COCO 解释、工作总结、论文对比规则 | 明确预训练与评分用途、外部参考 vs 自身严格消融；此前未完整记录到 README |
| 2026-10-13 本轮 | 全面核对和整理文档 | 对照 Git、脚本、配置、报告、日志和历史讨论，补齐记录与下一步；首次写入因 PowerShell/Python 编码失败未修改文件，随后用 UTF-8 写入修正 |

## 12. 后续待办和文档检查

| 顺序 | 待办 | 状态/验收条件 |
| --- | --- | --- |
| 1 | 改进诊断图 | 未做；原图/标注/预测、实例区分、类别/分数，固定示例，不只挑好图 |
| 2 | 完整预测误差分析 | 未做；量化漏检、错分类、实例拆分/重复及轮廓问题，确定首个目标 |
| 3 | 模块适配与消融 | 未做；固定基线条件，逐个验证收益和开销 |
| 4 | 完善 WaterMask 比较 | 已核对公开数字和部分配置；实际预训练和统一评价待核对，是否复现另定 |
| 5 | 确定第二研究点 | DINOv2/DiveSeg/TIDE 为候选，不同时全面铺开 |
| 下次服务器在线 | 下载权重与运行协议，校验哈希；同步新文档 | 未完成，不声称权重已经本地备份 |
| 独立维护 | 修复 Codex 自动 GitHub 凭据调用 | 未解决；推送故障不代表训练失败 |

本轮仅修改 README.md、AGENTS.md；不修改数据、训练脚本或成绩，不启动服务器任务。旧版可在 Git 历史查看。文档核验已通过：49 个本地链接有效、17 个脚本均有索引、核心指标和权重哈希与 JSON 一致、时间线提交均存在、代码围栏闭合且无替换乱码，git diff --check 通过；记录在忽略目录 reports/readme-review.json。服务器文件和电源本轮未重新核验。
