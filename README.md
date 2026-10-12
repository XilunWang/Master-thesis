# 水下实例分割实验

## 当前进度（2026-10-12）

**当前阶段：原版 Mask2Former 单图推理已跑通；尚未开始 UIIS 数据准备和训练。**

| 步骤 | 状态与验证 |
| --- | --- |
| 本地项目、Git、VS Code 共用目录 | 已完成 |
| SSH 密钥登录、代码同步 | 已实际验证成功 |
| 实验依赖安装 | 已完成：PyTorch 2.1.2+cu121、MMCV 2.1.0、MMEngine 0.10.7、MMDetection 3.3.0 |
| 依赖与 GPU 算子验证 | 导入、可变形注意力前向/反向、NMS 均通过；pip check 无冲突 |
| 官方 COCO 权重下载 | 已完成，SHA256 前缀 41b088b6 校验通过 |
| Mask2Former ResNet-50 单图推理 | 已完成，输出 MASK2FORMER_DEMO_OK；阈值 0.5 下有 20 个实例 |
| UIIS 数据集、训练配置、短训练与评估 | 未开始 |
| WaterMask 模块适配 | 未开始 |

本次使用 COCO 预训练模型与普通场景示例图，仅验证完整推理链路，不代表水下精度或训练已验证。示例图片因服务器访问 GitHub 超时，经本机下载后上传服务器。

结果在本地和服务器项目目录下的 `reports/demo-mask2former/`：`input.jpg` 为原图，`prediction.jpg` 为分割可视化，`summary.json` 为运行记录。首轮推理约 2.78 秒、峰值已分配 GPU 显存约 1197 MiB，不作为吞吐量或训练显存结论。

### 当前阻碍与同步状态

- 服务器 SSH 已恢复，单图推理代码与结果同步成功。
- GitHub 连接超时已通过项目级代理 `http://127.0.0.1:7890` 修复，fetch 已验证成功。该配置仅保存在本机仓库配置中，依赖本机代理运行。
- Codex 执行环境读取 Windows GitHub 凭据时仍被拒绝访问，自动推送问题未解决。此前推理提交 `97bdcfc` 在本轮检查时已与本地记录的 `origin/master` 一致；本文档更新的推送状态以实际推送结果为准。

### 下一步从这里开始

1. 获取并检查 WaterMask 使用的 UIIS 数据集，确认来源、图片、实例标注、类别及官方训练/验证划分。
2. 建立 Mask2Former ResNet-50 的 UIIS 配置，先用少量迭代验证训练、保存与恢复权重、评估流程。
3. 再正式训练原版基线，保存指标与分割效果，之后逐个验证 WaterMask 模块适配。

需要重跑单图验证时，在本机项目目录执行 `powershell -ExecutionPolicy Bypass -File .\run-demo.ps1`。权重与图片存在时会复用；GitHub 图片下载超时时需处理网络或提供同一示例图，不能把下载失败误判为模型失败。

每完成或尝试一个工作步骤，都更新本节的结果、阻碍和下一步，相关文档与代码一同提交。

## 服务器依赖环境

在服务器项目目录执行 `bash scripts/install-env.sh` 安装依赖；以后使用 `.venv/bin/python` 运行代码，或先执行 `source .venv/bin/activate`。

环境基于平台镜像的 Python 3.10、PyTorch 2.1.2+cu121、torchvision 0.16.2+cu121。项目 venv 通过 `--system-site-packages` 复用基础环境，因此并非完全隔离；更换或修改基础镜像后需要重新验证。项目新增依赖写入 venv，基础 PyTorch 不改动。

主要版本固定在 `requirements.txt`。MMCV 使用官方 CUDA 12.1 / torch 2.1 预编译 wheel，避免编译 CUDA 扩展。`scripts/verify-env.py` 检查模块注册、CUDA 可变形注意力的前向与反向运算，以及 CUDA NMS。它不等同于完整模型训练验证。

安装日志：服务器 `/root/autodl-tmp/install-env.log`。环境检查与完整依赖快照保存在 `reports/`，不上传 Git。预训练权重和完整单图推理已验证，后续仍需准备 UIIS 数据及训练评估流程。

本文件夹是本地代码的唯一工作目录。Codex 修改这里的文件，VS Code 打开同一目录即可看到修改。不要在本地和服务器分别修改同一份代码。

## 实验路线

使用 UIIS 数据集，先跑通 MMDetection 的 Mask2Former ResNet-50 基线，再分别验证 WaterMask 模块的适配效果。当前已安装依赖并完成 COCO 单图推理，尚未下载 UIIS 或启动训练。

## 连接服务器

在本文件夹打开 PowerShell，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\connect.ps1
```

如果提示密码，在终端输入平台提供的密码；输入时不显示字符是正常现象。不要把密码或私钥写入代码、聊天或 Git。

主机地址为 region-46.seetacloud.com，端口 27686。首次连接登记的主机指纹保存在本地忽略目录 `.local`。后续主机指纹变化会拒绝连接，需核实后处理。

## 后续工作

首次在本机 PowerShell 执行 `powershell -ExecutionPolicy Bypass -File .\setup-ssh.ps1`，在终端输入平台密码。看到 `SSH_KEY_OK` 表示密钥登录成功。专用私钥保存在 `.local/id_ed25519`，不得上传或提交。

之后执行 `powershell -ExecutionPolicy Bypass -File .\sync-code.ps1` 将代码同步到 `/root/autodl-tmp/underwater-segmentation`。脚本按 Git 忽略规则打包文件，覆盖远程同名代码，不删除远程多余文件；重命名或删除代码后需另行核对远程文件。数据、权重和训练输出应保存在被忽略的目录中。代码同步已验证，训练脚本尚未配置。
