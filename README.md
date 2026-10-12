# 水下实例分割实验

## 当前进度（2026-10-12）

**当前阶段：UIIS 已下载并审计；按用户确认的方案，已使用官方原始划分完成 100 次迭代训练、断点恢复和全部 691 张图片的评估。已按用户要求固定保留官方 3937/691 原始划分及重复图片；最终评价方式待定；正式基线候选配置及 20 步性能检查已完成，完整训练尚未开始。**

| 步骤 | 状态与验证 |
| --- | --- |
| 本地项目、Git、VS Code 共用目录 | 已完成 |
| SSH 密钥登录、代码同步 | 已实际验证成功 |
| 实验依赖安装 | 已完成：PyTorch 2.1.2+cu121、MMCV 2.1.0、MMEngine 0.10.7、MMDetection 3.3.0 |
| 依赖与 GPU 算子验证 | 导入、可变形注意力前向/反向、NMS 均通过；pip check 无冲突 |
| 官方 COCO 权重下载 | 已完成，SHA256 前缀 41b088b6 校验通过 |
| Mask2Former ResNet-50 单图推理 | 已完成，输出 MASK2FORMER_DEMO_OK；阈值 0.5 下有 20 个实例 |
| UIIS 数据集 | 本地与服务器 4631 个文件均通过官方哈希校验；图片与全部掩码审计通过，发现 1 对跨划分重复图片 |
| UIIS 七类短训练配置 | 已通过：训练 50 → 保存 → 恢复到 100 → 全量 bbox/segm 评估 |
| WaterMask 模块适配 | 未开始 |

此前单图演示使用 COCO 预训练模型与普通场景示例图，仅验证推理链路；水下短训练结果见下文，不代表正式精度。示例图片因服务器访问 GitHub 超时，经本机下载后上传服务器。

结果在本地和服务器项目目录下的 `reports/demo-mask2former/`：`input.jpg` 为原图，`prediction.jpg` 为分割可视化，`summary.json` 为运行记录。首轮推理约 2.78 秒、峰值已分配 GPU 显存约 1197 MiB，不作为吞吐量或训练显存结论。

### 当前阻碍与同步状态

- 2026-10-12 晚间最新重试已恢复：再次通过定向网络及私钥读取授权后，实际返回 SSH_KEY_OK、PROJECT_DIR_OK；V100 32768 MiB，显存占用 0 MiB。未启用完全访问权限、未修改密钥 ACL；此前文件访问失败已不再复现，但权限恢复的底层原因未确认。未启动完整训练。本次仅核对登录、GPU 和项目目录，不代表重新全量校验了数据。

- 服务器 SSH 已恢复；UIIS 短训练已完成，代码、README 与报告同步到本地及服务器，权重保留在服务器。
- GitHub 连接超时已通过项目级代理 `http://127.0.0.1:7890` 修复，fetch 已验证成功。该配置仅保存在本机仓库配置中，依赖本机代理运行。
- Codex 执行环境读取 Windows GitHub 凭据时仍被拒绝访问，自动推送问题未解决。最近一次推送失败，不能把本地提交视为已经上传 GitHub。
- 本次核对开始时，本地分支与已知 origin/master 一致（此前提交已同步）；但本次 Codex 自动推送仍报凭据调用 NtCreateDirectoryObject 0xC0000022，新文档提交不能记为已推送。最新同步状态以 `git status -sb` 和实际推送结果为准。
- 数据审计发现 train/XL_266.jpg 与 val/XL_679.jpg 内容完全相同。原始划分未修改；按用户最新要求保留两张图片及原始标注，不删除、不从清单中排除。

### 下一步从这里开始

1. 查看下文候选配置及性能报告，下一小步确定训练预算、保存和模型选择规则；不重新划分数据。
2. 预算与规则确定后增加正式训练启动/恢复入口；当前脚本只生成配置或执行 20 步性能检查。
3. 再正式训练原版基线，保存指标与分割效果，之后逐个验证 WaterMask 模块适配。

不需要重复安装依赖或下载已有权重、数据。短训练与评估已通过；候选配置已验证能进行短训练；下一次确定正式预算和保存规则，最终评价与模型选择规则仍待定，不自动启动长训练。

需要重跑单图验证时，在本机项目目录执行 `powershell -ExecutionPolicy Bypass -File .\run-demo.ps1`。权重与图片存在时会复用；GitHub 图片下载超时时需处理网络或提供同一示例图，不能把下载失败误判为模型失败。

每完成或尝试一个工作步骤，都更新本节的结果、阻碍和下一步，相关文档与代码一同提交。

## 项目位置与文件用途

- 本地目录：`C:\Users\Lenovo\Documents\Codex\2026-10-09\new-chat-2\underwater-segmentation`。
- 服务器目录：`/root/autodl-tmp/underwater-segmentation`。
- GitHub 仓库：<https://github.com/XilunWang/Master-thesis>，当前分支 `master`。
- 本地是代码主目录，VS Code 和 Codex 使用同一份文件；运行前再同步到服务器。

| 文件或目录 | 用途 |
| --- | --- |
| `AGENTS.md` | 协作、步骤记录、提交与推送约定 |
| `requirements.txt` | 主要依赖的固定版本 |
| `scripts/install-env.sh` | 创建项目环境并安装、验证依赖 |
| `scripts/verify-env.py` | 验证依赖与关键 GPU 算子 |
| `scripts/demo-mask2former.py` | 加载官方权重并完成单图推理 |
| `scripts/download-uiis.py` | 固定数据版本下载，支持跳过已校验文件，验证官方文件哈希 |
| `scripts/validate-uiis.py` | 检查图片、标注引用、类别、掩码解码及跨划分完全重复图片 |
| `scripts/train-uiis-smoke.py` | 构建七类、单卡、512 像素的排错配置并运行短训练/评估 |
| `scripts/run-uiis-smoke.sh` | 先训练 50 次，再恢复到 100 次；每次创建新的输出目录 |
| `run-demo.ps1` | 本地一键同步、远程推理、下载结果 |
| `connect.ps1` / `ssh.config` | 连接训练服务器 |
| `setup-ssh.ps1` | 初次登记 SSH 公钥，已完成，无需重复执行 |
| `sync-code.ps1` | 按 Git 忽略规则同步源代码 |
| `reports/` | 检查报告、结果图、依赖快照，不提交 Git |
| `checkpoints/` | 已下载的模型权重，目前主要在服务器，不提交 Git |
| `.local/` | 本机密钥和同步临时文件，不提交 Git、不上传服务器 |

## 已完成的推理是什么

模型为 MMDetection 的 `mask2former_r50_8xb2-lsj-50e_coco`：ResNet-50 提取图像特征，Mask2Former 预测每个物体的类别和掩码。当前没有加入 DSGAT、MFRM 或 BLL。

- `input.jpg`：输入的普通场景原图。
- `prediction.jpg`：模型输出叠加图；彩色区域为实例掩码，白色线条是轮廓，矩形是检测框，文字是类别及置信度。
- 置信度不是分割准确率。没有用人工真值标注计算 AP，也没有验证水下边界改进。
- 一张图只用于检查“加载模型—GPU 推理—保存结果”的链路，不能代替完整数据集实验。

## UIIS 数据准备

来源为 [WaterMask 官方仓库](https://github.com/LiamLian0727/WaterMask) 链接的 [原版 UIIS](https://huggingface.co/datasets/LiamLian0727/UIIS)，不是 UIIS10K。固定版本为 `44ca5db46599f14faf8e57643014664435823738`，下载清单保存在 `data/UIIS/download-manifest.json`。

官方说明为 3937 张训练图、691 张测试图；测试标注文件名为 `val.json`。按用户要求保留官方原始划分；目前不另划内部验证集。最终评价和模型选择规则后续确定。

已读取原始 JSON，训练集有 24626 个实例，测试集有 3784 个实例。类别编号如下，后续配置必须按标注名称和顺序映射：

| ID | 官方类别名称 | 训练实例数 | 测试实例数 |
| --- | --- | --- | --- |
| 1 | fish | 14709 | 2040 |
| 2 | reefs | 7251 | 1241 |
| 3 | aquatic plants | 1052 | 203 |
| 4 | wrecks/ruins | 211 | 37 |
| 5 | human divers | 499 | 97 |
| 6 | robots | 73 | 17 |
| 7 | sea-floor | 831 | 149 |

类别数量明显不均衡，尤其 robots 实例少。后续除整体 mask AP 外，应保留各类别结果，不能只看平均指标。

下载程序使用 Python 和 requests（本机已有）。图片与 COCO JSON 位于 `data/UIIS/{train,val,annotations}`，不提交 Git。文件校验使用官方 Git blob SHA1 或 LFS SHA256。完整下载后将数据单独传到服务器；普通代码同步脚本不会传输 `data/`。

原站两份大 JSON 曾下载不完整，已通过补传恢复并匹配官方 SHA256。本地 4631 个文件已全量复核通过。服务器使用同一官方清单与 `--mirror` 从 `hf-mirror.com` 传输部分文件；镜像限流后停止下载，从本地补传 1629 个缺失文件。服务器最终 4631 个文件全量哈希复核通过。后续可用 `--audit-only` 离线复核，默认并发已降为 8，遇到 429 会等待。

服务器已执行 `.venv/bin/python scripts/validate-uiis.py`，结果保存在本地与服务器的 `reports/uiis-audit.json`。3937+691 张图片读取及尺寸检查通过，24626+3784 个掩码解码通过，结构错误 0、空掩码 0。发现 1 对跨划分完全重复图片（仅检查字节一致，未排查近重复）：训练 XL_266.jpg 与测试 XL_679.jpg。未自动删除、改写原始数据。

`reports/uiis-ground-truth-train.jpg` 与 `reports/uiis-ground-truth-val.jpg` 各展示一张原图（左）及人工标注叠加（右），不是模型预测。本地已查看训练样例，全面标注质量仍不能仅凭抽样保证。

## 正式实验数据使用方案（按用户最新要求修订）

2026-10-12 用户明确要求：保留官方原始划分；所有对照模型使用同样的数据规则；最终评价方式最后再定；不删除已发现的重复图片。本节取代此前去重并划出约 10% 内部验证集的方案，该旧方案未执行。

- 官方训练集：3937 张，继续使用原始 `annotations/train.json`。
- 官方测试集：691 张，继续使用原始 `annotations/val.json`（文件名虽为 val，官方用途为测试集）。
- 保留 `train/XL_266.jpg` 和 `val/XL_679.jpg`，不删除图片，不从训练或测试标注中排除。两者 SHA256 均为 `ce7d3d5b5c759496d903626329a7ce9ea3cde946853596a3c9fa200c28802af8`。
- Mask2Former 基线、改进模型及计划复现的 WaterMask 共用相同数据规则。目前不生成派生划分，不另留内部验证集。
- 最终评价方式及模型选择规则待定；不预先安排排除重复测试图片的额外评估，也不使用测试成绩自动挑选模型。
- 保留已知跨划分重复的审计记录，在后续结果说明中如实披露。只确认了文件内容完全相同的重复，未排查近重复；保留它是为了遵循官方划分，不代表已经获得精度提升或消除了泄漏风险。

本步骤仅修改文档约定，没有修改图片、原始 JSON 或训练代码，没有启动训练。后续候选配置已按本协议准备，见下一节。
## 短训练流程测试（已通过）

已通过服务器 `screen` 会话 `uiis-smoke` 完成，进程正常结束。日志为 `reports/uiis-smoke-console.log`，本次权重目录由 `reports/uiis-smoke-latest.txt` 记录。使用官方 3937/691 划分，没有去重或重新划分。

设置：Mask2Former ResNet-50、7 个实例类别、输入缩放到 512×512 范围并保持比例、batch size 1、FP32、AdamW 基础学习率 0.0001、随机种子 20261012，无学习率调度。这些只用于测试流程，不是最终基线训练参数。

COCO 权重的分类层有 80 类，而 UIIS 有 7 类，因此分类层权重和偏置尺寸不匹配并重新初始化是预期现象；其余兼容权重正常加载。`reports/uiis-smoke-config-*.py` 保存实际解析后的配置。

实际验收通过：

- 50 次保存后重新启动进程，日志确认 `resumed epoch: 0, iter: 50`，继续到 100 次。
- `iter_50.pth` 和 `iter_100.pth` 均存在，迭代元数据正确，均包含 345 项优化器状态；权重各约 528 MB，保留在服务器。
- 10 条训练日志记录无 NaN/Inf，阶段报告的末步损失均为有限值。此检查不等于证明已经收敛。
- 全部 691 张图完成 bbox 与 segm 评估，最终输出 `UIIS_SMOKE_ALL_OK`。
- 流程测试 mask AP = 0.047（4.7 AP）、AP50 = 0.085（8.5 AP），bbox AP = 0.046。仅训练 100 次、保留已知重复图片，不能作为论文正式基线或模块效果结论。

本次输出目录：服务器 `work_dirs/uiis_smoke_20261012_150419`。本地及服务器 `reports/` 均保存 `uiis-smoke-50.json`、`uiis-smoke-100.json`、`uiis-smoke-checkpoints.json`、完整控制台日志、实际配置及目录记录。报告中的 `peak_gpu_mib` 是训练框架可能重置过的显存计数器读数，不能解释为整个实验的峰值。

重跑入口：同步代码后在服务器项目目录执行 `bash scripts/run-uiis-smoke.sh`；长时间运行应放入 screen 会话。重跑会创建新的权重目录，但覆盖同名 reports 流程报告，需要留存旧报告时先备份。

## 正式基线候选配置与性能检查（已完成）

入口为 `scripts/prepare-uiis-baseline.py`。不带参数仅生成 `reports/uiis-baseline-candidate.py` 并检查官方数量、类别顺序及重复图片仍在标注中；带 `--profile` 只运行 20 步，不保存训练权重或评估测试集。当前没有正式长训练启动入口。

候选设置：原版 Mask2Former ResNet-50，COCO 预训练、UIIS 七类分类层重新初始化；保留 MMDetection 官方 1024×1024 LSJ 随机缩放/裁剪训练流程，测试缩放为 (1333, 800)。单卡 batch 2、2 个数据加载进程、FP32，AdamW 基础学习率 0.0001（主干倍率 0.1），禁用自动学习率缩放。原始 3937/691 数据及已知重复图片保留。

训练预算暂拟 36 轮，第 27、33 轮降低学习率，每轮保存且只保留最近 3 份及末次权重；该预算未启动，也不代表已经证明足够收敛。由于最终评价与模型选择规则待定，候选配置禁用训练期间测试集评估及 best-checkpoint 自动选择。后续确定规则时需一并核对 checkpoint 保留策略。

2026-10-12 性能检查通过 `BASELINE_CONFIG_OK` 和 `BASELINE_PROFILE_OK`：

- 20 步、每步 2 张，所有步骤的损失检查均为有限数；无显存溢出。
- GPU 为现有 V100 32 GB；逐步统计峰值已分配显存 10558.5 MiB（约 10.31 GiB），峰值缓存预留 11230 MiB（约 10.97 GiB）。仅代表这 40 张次样本，不能保证后续所有样本的峰值。
- 去掉前 5 步后，平均纯计算时间约 0.694 秒/步，不包含数据加载。训练调用总耗时 20.41 秒，包含初始化开销，不能直接当稳定每步耗时。
- 每轮约 1969 步；若采用 36 轮，共 70884 步。由本次短测外推，纯计算约 13.7 小时；考虑数据加载、保存、样本差异，暂按约 15–22 小时作粗略排期，不是完成时间承诺，也不包含最终评估。完整训练速度仍需较长运行确认。

报告和实际配置已取回本地，与服务器均位于 `reports/uiis-baseline-*`；`uiis-baseline-profile.json` 含每步时间、显存及损失，`.log` 为完整日志。此次只检查训练容量，不产生新的 AP 成绩。正式训练仍应从 COCO 预训练权重开始，不接续性能检查或此前 100 步权重。
## 服务器依赖环境

在服务器项目目录执行 `bash scripts/install-env.sh` 安装依赖；以后使用 `.venv/bin/python` 运行代码，或先执行 `source .venv/bin/activate`。

环境基于平台镜像的 Python 3.10、PyTorch 2.1.2+cu121、torchvision 0.16.2+cu121。项目 venv 通过 `--system-site-packages` 复用基础环境，因此并非完全隔离；更换或修改基础镜像后需要重新验证。项目新增依赖写入 venv，基础 PyTorch 不改动。

主要版本固定在 `requirements.txt`。MMCV 使用官方 CUDA 12.1 / torch 2.1 预编译 wheel，避免编译 CUDA 扩展。`scripts/verify-env.py` 检查模块注册、CUDA 可变形注意力的前向与反向运算，以及 CUDA NMS。它不等同于完整模型训练验证。

安装日志：服务器 `/root/autodl-tmp/install-env.log`。环境检查与完整依赖快照保存在 `reports/`，不上传 Git。预训练权重、单图推理、UIIS 数据和短训练评估流程均已验证。

本文件夹是本地代码的唯一工作目录。Codex 修改这里的文件，VS Code 打开同一目录即可看到修改。不要在本地和服务器分别修改同一份代码。

## 正式一轮训练就绪检查（2026-10-12 晚间）

已在服务器重新构建候选配置和真实训练数据加载器：MMDetection 3.3.0、MMEngine 0.10.7；训练图片 3937 张、batch 2，每轮 1969 步；COCO 初始权重存在。仅构建加载器，没有启动训练，也没有再次逐图完整读取。

当前不能把现有命令当成已经完成的正式一轮启动工具：prepare-uiis-baseline.py 无参数只输出配置，--profile 固定运行 20 步且关闭 checkpoint。候选配置虽包含 36 轮和每轮保存最近 3 份，但正式启动/恢复入口、后台会话、首轮结束暂停检查以及额外保留 12/24/36 轮尚未实现。因此训练基础具备，完整运行封装还需补齐；正式首轮保存恢复也尚未实测。

本地仓库不是 Mask2Former 全部源码。它导入服务器虚拟环境中的 MMDetection/MMEngine，复用已经安装的模型和训练实现。实测源码位置（服务器路径）：

- `.venv/lib/python3.10/site-packages/mmdet/models/detectors/mask2former.py`：模型入口，30 行，复用父类，不能把这一文件当作全部网络。
- `.venv/lib/python3.10/site-packages/mmdet/models/dense_heads/mask2former_head.py`：分割头文件，459 行。
- `.venv/lib/python3.10/site-packages/mmdet/models/layers/msdeformattn_pixel_decoder.py`：像素解码器文件，246 行。
- `.venv/lib/python3.10/site-packages/mmengine/runner/runner.py`：通用训练管理文件，2413 行。

这些只是部分依赖文件，还包含 ResNet、Transformer 层、损失、数据处理和底层 PyTorch/MMCV 算子。以后适配模块应将自定义代码放在本地项目并注册导入，不直接改服务器 site-packages，保证 VS Code 可见、Git 可追踪。检查结果保存在本地和服务器 `reports/baseline-readiness-audit.json`。
## 实验路线

使用 UIIS 数据集，先跑通 MMDetection 的 Mask2Former ResNet-50 基线，再分别验证 WaterMask 模块的适配效果。当前已完成依赖、COCO 单图推理、UIIS 数据准备及 100 次迭代流程测试，尚未进行正式基线训练和模块适配。

## 下次服务器开机后的重连约定

用户只需说“服务器开启了”。Codex 先检查当前会话的网络及项目私钥读取授权，必要时通过 request_permissions 定向申请，再运行 `powershell -ExecutionPolicy Bypass -File ./check-server.ps1`。不要求完全访问权限，不改密钥 ACL，不重复安装公钥。固定流程已写入 AGENTS.md，后续项目任务应遵循。

2026-10-12 实测：未重新取得有效网络访问时出现域名解析失败；申请网络与精确私钥读取权限后，检查约 0.99 秒返回 SERVER_READY。GPU 为 V100 32GB、显存占用 0，项目 Python 与两份原始标注路径存在，数据盘可用约 48GB。报告在 `reports/server-check.txt`。这只是路径存在性检查，不替代环境算子或数据全量校验。

服务器开关机与 Codex 本机执行授权是两个独立层面；此前公钥被服务器接受而本地私钥读取被拒绝，不能归因于服务器关机。授权的生效范围可能是当前轮次或会话，不能承诺跨重启永久有效。成功后继续已授权步骤；准备启动训练前先检查已有进程，防止重复训练。需要用户审批时仍会出现正式授权提示，不能保证所有重连都无需交互。

本次新增脚本及约定已本地验证，未启动训练。服务器同步与 GitHub 推送分别执行，GitHub 凭据故障不应阻塞 SSH 检查。
## 连接服务器

在本文件夹打开 PowerShell，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\connect.ps1
```

SSH 密钥登录已经配置完成，正常情况下无需密码。如果提示密码，先检查密钥路径和服务器登录配置；不要把密码或私钥写入代码、聊天或 Git。

主机地址为 region-46.seetacloud.com，端口 27686。首次连接登记的主机指纹保存在本地忽略目录 `.local`。后续主机指纹变化会拒绝连接，需核实后处理。

## 常用操作与同步规则

首次设置使用 `setup-ssh.ps1`，已经验证 `SSH_KEY_OK`。专用私钥保存在 `.local/id_ed25519`，不得上传或提交。

之后执行 `powershell -ExecutionPolicy Bypass -File .\sync-code.ps1` 将代码同步到 `/root/autodl-tmp/underwater-segmentation`。脚本按 Git 忽略规则打包文件，覆盖远程同名代码，不删除远程多余文件；重命名或删除代码后需另行核对远程文件。数据、权重和训练输出应保存在被忽略的目录中。代码同步与短训练脚本均已验证。

服务器重新检查环境：

```bash
cd /root/autodl-tmp/underwater-segmentation
.venv/bin/python scripts/verify-env.py
.venv/bin/python -m pip check
```

完整工作流程：本地修改 → 同步服务器 → 运行并检查结果 → 更新 README → 提交 Git → 推送 GitHub。代码同步不是实时自动进行；GitHub 推送与服务器同步互相独立。

## 工作记录

| 日期 | 已执行步骤 | 结果 |
| --- | --- | --- |
| 2026-10-12 | 建立本地项目、Git、服务器密钥登录及同步脚本 | 已验证，VS Code 可查看同一份代码 |
| 2026-10-12 | 安装依赖并测试 GPU 算子 | 已通过，版本与报告已保存 |
| 2026-10-12 | 恢复联网授权，下载权重并运行 COCO 示例图 | 完整推理通过，图片和 JSON 已取回本地 |
| 2026-10-12 | 修复 GitHub 网络连接 | 项目级代理设置生效，fetch 成功；自动推送仍有凭据权限阻碍 |
| 2026-10-12 | 整理 Markdown 进度与交接说明 | 已核对环境报告及推理记录；后续从 UIIS 数据准备开始 |
| 2026-10-12 | 下载、补传并审计 UIIS | 本地/服务器哈希校验通过；图片和掩码结构通过；发现 1 对跨划分重复，正式实验前确定处理方式 |
| 2026-10-12 | 官方 UIIS 划分短训练与恢复测试 | 50 → 100 次训练、checkpoint/优化器检查及 691 张图 bbox/segm 评估通过；报告取回本地；GitHub 推送仍受凭据权限限制 |
| 2026-10-12 | 核对正式数据使用方案 | 复核 3937/691 数量、重复图片 SHA256 和各类别图片数；曾记录去重及约 10% 内部验证方案；未执行，已被用户后续要求取代 |
| 2026-10-12 | 按用户要求保留官方划分 | 保留 3937/691 及重复图片；所有对照共用数据规则；最终评价待定；未修改数据或启动训练 |
| 2026-10-12 | 准备基线候选配置并测容量 | 官方划分保留；1024 LSJ、batch 2、FP32 的 20 步检查通过；报告回传，完整训练未启动 |
| 2026-10-12 | 晚间重连恢复 | 定向授权后 SSH_KEY_OK；V100 显存占用 0，项目目录存在；未启动训练 |
| 2026-10-12 | 固化开机重连流程 | 新增 check-server.ps1 与 AGENTS 规则；定向授权后约 0.99 秒检查通过，未启动训练 |
| 2026-10-12 23:15 | 用户关机再开机后的重连验证 | 保持当前 Codex 会话，复用已有授权；首次检查约 1.57 秒返回 SERVER_READY。V100 显存占用 0，环境/标注路径存在，数据盘可用 48GB；未启动训练。此结果不验证 Codex 重启后的授权持久性。 |
| 2026-10-12 | 核对正式一轮训练就绪程度及源码位置 | 真实加载器 3937 图/1969 步、预训练权重存在；正式入口和阶段备份待实现；未启动训练 |
