# 研究汇报 PPT 维护

当前版本：output/水下实例分割研究进展_20261013_v1.pptx（2026-10-13，13 页）。
沿用用户提供的 4.27组会王雨乐.pptx 的母版、校徽、配色及字体；不沿用原作者身份。原模板保存在 templates/group-meeting-template.pptx，仅本地使用。

## 更新规则

- 每次完成有意义的研究进展（新实验评估、模块消融、误差分析或路线变更），同步维护本 PPT、README 和版本记录。普通连接检查不生成新汇报版本。
- build.mjs 为内容与版式源，status.json 为日期及输出文件名；指标从 reports/uiis-baseline-36e-evaluation/metrics.json 读取，不能手动编造成绩。
- 新增实验须先核对原始报告，再增加对应结果页和讲者备注来源；保留基线及局限，区分计划和完成。第二研究点仍待定。
- 修改日期及版本号后生成新文件，保留旧版本，不覆盖已汇报的 PPT。当前不知道汇报人姓名，封面未填姓名。
- 在 PowerPoint 手工改动后，应同步到生成源，否则下次重建不会保留手工修改。
- 模板、报告和 PPT 输出暂不提交 Git；源码、维护约定与 README 提交。需备份这些本地素材才能在其他电脑完整重建。

## 生成与检查

使用 Codex Presentations skill 的 bundled Node 运行 build.mjs；可通过 CODEX_PRESENTATION_RUNTIME 和 CODEX_PRESENTATION_SKILL 指定运行时及技能路径。
构建器导出 .build/candidate.pptx、逐页 PNG，再调用 finalizer 写入独立输出。每次均需核对所有页、数据、可编辑表格、模板样式、讲者备注来源。

本版记录：finalizer 在 Node realpath 阶段发生 EPERM，定向授权后仍失败，未宣称完整终检通过。已独立运行原生结构与几何检查器，均为零发现；13 页逐页检查完成，原生表格页 3/4/5/6/7/12 确认；Artifact Tool 重导入 13 页成功。检查后将候选副本交付到 output。尚未在 PowerPoint 原生程序中打开验证。

## 版本记录

- v1 / 2026-10-13：研究任务、数据规则、36轮训练配置、完整指标、小目标与类别表现、WaterMask官方参考比较、6张固定案例、第一点计划与第二点候选。尚无自有模块成绩。
