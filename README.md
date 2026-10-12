# 水下实例分割实验

## 当前进度（2026-10-12）

**当前阶段：UIIS 已下载到本地和服务器并完成审计；下一步配置数据划分和短训练，尚未训练。**

| 步骤 | 状态与验证 |
| --- | --- |
| 本地项目、Git、VS Code 共用目录 | 已完成 |
| SSH 密钥登录、代码同步 | 已实际验证成功 |
| 实验依赖安装 | 已完成：PyTorch 2.1.2+cu121、MMCV 2.1.0、MMEngine 0.10.7、MMDetection 3.3.0 |
| 依赖与 GPU 算子验证 | 导入、可变形注意力前向/反向、NMS 均通过；pip check 无冲突 |
| 官方 COCO 权重下载 | 已完成，SHA256 前缀 41b088b6 校验通过 |
| Mask2Former ResNet-50 单图推理 | 已完成，输出 MASK2FORMER_DEMO_OK；阈值 0.5 下有 20 个实例 |
| UIIS 数据集 | 本地与服务器 4631 个文件均通过官方哈希校验；图片与全部掩码审计通过，发现 1 对跨划分重复图片 |
| UIIS 训练配置、短训练与评估 | 未开始 |
| WaterMask 模块适配 | 未开始 |

本次使用 COCO 预训练模型与普通场景示例图，仅验证完整推理链路，不代表水下精度或训练已验证。示例图片因服务器访问 GitHub 超时，经本机下载后上传服务器。

结果在本地和服务器项目目录下的 `reports/demo-mask2former/`：`input.jpg` 为原图，`prediction.jpg` 为分割可视化，`summary.json` 为运行记录。首轮推理约 2.78 秒、峰值已分配 GPU 显存约 1197 MiB，不作为吞吐量或训练显存结论。

### 当前阻碍与同步状态

- 服务器 SSH 已恢复，单图推理代码与结果同步成功。
- GitHub 连接超时已通过项目级代理 `http://127.0.0.1:7890` 修复，fetch 已验证成功。该配置仅保存在本机仓库配置中，依赖本机代理运行。
- Codex 执行环境读取 Windows GitHub 凭据时仍被拒绝访问，自动推送问题未解决。最近一次推送失败，不能把本地提交视为已经上传 GitHub。
- 本步骤开始时已有两个文档提交等待推送；凭据权限问题仍未解决。最新同步状态以 `git status -sb` 和实际推送结果为准。
- 数据审计发现 train/XL_266.jpg 与 val/XL_679.jpg 内容完全相同。原始划分未修改；训练配置前应明确去重方案，避免泄漏。

### 下一步从这里开始

1. 在保留原始文件的前提下，制定派生数据划分：建议从训练侧排除与测试集重复的图片，并从其余训练图划出固定内部验证集。记录这与原论文协议的差异，后续所有对照模型保持同一划分。
2. 建立 Mask2Former ResNet-50 的七类 UIIS 配置，先用少量迭代验证训练、保存与恢复权重、评估流程。
3. 再正式训练原版基线，保存指标与分割效果，之后逐个验证 WaterMask 模块适配。

下一次工作从第 1 项“派生划分与训练配置”开始，不需要重复安装依赖或下载已有权重、数据。正式长训练前，必须先完成小规模训练与评估验证。

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

官方说明为 3937 张训练图、691 张测试图；测试标注文件名为 `val.json`。保留官方划分。后续调参需要从训练集另划内部验证集，避免反复用官方测试集挑选模型。

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

## 服务器依赖环境

在服务器项目目录执行 `bash scripts/install-env.sh` 安装依赖；以后使用 `.venv/bin/python` 运行代码，或先执行 `source .venv/bin/activate`。

环境基于平台镜像的 Python 3.10、PyTorch 2.1.2+cu121、torchvision 0.16.2+cu121。项目 venv 通过 `--system-site-packages` 复用基础环境，因此并非完全隔离；更换或修改基础镜像后需要重新验证。项目新增依赖写入 venv，基础 PyTorch 不改动。

主要版本固定在 `requirements.txt`。MMCV 使用官方 CUDA 12.1 / torch 2.1 预编译 wheel，避免编译 CUDA 扩展。`scripts/verify-env.py` 检查模块注册、CUDA 可变形注意力的前向与反向运算，以及 CUDA NMS。它不等同于完整模型训练验证。

安装日志：服务器 `/root/autodl-tmp/install-env.log`。环境检查与完整依赖快照保存在 `reports/`，不上传 Git。预训练权重、完整单图推理与 UIIS 数据已验证，后续仍需配置训练评估流程。

本文件夹是本地代码的唯一工作目录。Codex 修改这里的文件，VS Code 打开同一目录即可看到修改。不要在本地和服务器分别修改同一份代码。

## 实验路线

使用 UIIS 数据集，先跑通 MMDetection 的 Mask2Former ResNet-50 基线，再分别验证 WaterMask 模块的适配效果。当前已完成依赖、COCO 单图推理及 UIIS 数据准备，尚未启动训练。

## 连接服务器

在本文件夹打开 PowerShell，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\connect.ps1
```

SSH 密钥登录已经配置完成，正常情况下无需密码。如果提示密码，先检查密钥路径和服务器登录配置；不要把密码或私钥写入代码、聊天或 Git。

主机地址为 region-46.seetacloud.com，端口 27686。首次连接登记的主机指纹保存在本地忽略目录 `.local`。后续主机指纹变化会拒绝连接，需核实后处理。

## 常用操作与同步规则

首次设置使用 `setup-ssh.ps1`，已经验证 `SSH_KEY_OK`。专用私钥保存在 `.local/id_ed25519`，不得上传或提交。

之后执行 `powershell -ExecutionPolicy Bypass -File .\sync-code.ps1` 将代码同步到 `/root/autodl-tmp/underwater-segmentation`。脚本按 Git 忽略规则打包文件，覆盖远程同名代码，不删除远程多余文件；重命名或删除代码后需另行核对远程文件。数据、权重和训练输出应保存在被忽略的目录中。代码同步已验证，训练脚本尚未配置。

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
| 2026-10-12 | 下载、补传并审计 UIIS | 本地/服务器哈希校验通过；图片和掩码结构通过；发现 1 对跨划分重复，待配置训练时处理 |
