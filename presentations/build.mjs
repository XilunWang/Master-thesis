process.on('uncaughtException',e=>{console.error(e.message);process.exit(1);});
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
const RUNTIME=process.env.CODEX_PRESENTATION_RUNTIME || 'C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const SKILL=process.env.CODEX_PRESENTATION_SKILL || 'C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1011.11113/skills/presentations';
const {Presentation,PresentationFile,FileBlob}=await import(pathToFileURL(path.join(RUNTIME,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const ROOT=path.resolve(import.meta.dirname,'..');
const BUILD=path.join(ROOT,'presentations/.build');
const TEMPLATE=path.join(ROOT,'presentations/templates/group-meeting-template.pptx');
const EVAL=path.join(ROOT,'reports/uiis-baseline-36e-evaluation');
const metrics=JSON.parse(await fs.readFile(path.join(EVAL,'metrics.json'),'utf8'));
const status=JSON.parse(await fs.readFile(path.join(ROOT,'presentations/status.json'),'utf8'));
const finalPath=path.join(ROOT,`presentations/output/${status.outputName}.pptx`);
await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(path.dirname(finalPath),{recursive:true});
const imported=await PresentationFile.importPptx(await FileBlob.load(TEMPLATE));
const proto=imported.toProto();
for(const slide of proto.slides){slide.elements=[];slide.speakerNotes=undefined;}
const p=Presentation.load(proto);p.slides.keep([0,1,5]);
const cover=p.slides.items[0], base=p.slides.items[1], close=p.slides.items[2];
const content=[base]; for(let i=1;i<11;i++) content.push(base.duplicate());
const diagnostics=base.duplicate(), errors=base.duplicate(), protocol=base.duplicate();
p.slides.reorder([cover,...content.slice(0,9),protocol,diagnostics,errors,...content.slice(9),close].map(s=>'sl/'+s.id));
const teal='#008899',ink='#172126';
function tx(s,text,x,y,w,h,size=24,opts={}){
 const a=s.shapes.add({geometry:'textbox',name:opts.name||text.slice(0,24),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=text;a.text.style={typeface:opts.font||'黑体',fontSize:size,color:opts.color||ink,bold:opts.bold||false,alignment:opts.align||'left',verticalAlignment:'middle',wrap:true,insets:{left:0,right:0,top:0,bottom:0}};return a;
}
function heading(s,n,title){tx(s,'水下实例分割研究进展',178,37,655,40,24,{color:teal,font:'宋体'});tx(s,title,38,107,1170,48,28,{color:teal,font:'宋体',bold:true});}
function note(s,t,src='README.md'){s.speakerNotes.text=t+'\n\n数据来源：'+src;}
function line(s,t,y,size=26){return tx(s,t,65,y,1145,66,size);}
async function pic(s,i,x,y,w,h){s.images.add({blob:new Uint8Array(await fs.readFile(path.join(EVAL,`examples/${i}.jpg`))).buffer,contentType:'image/jpeg',alt:`UIIS 固定第${i+1}张：左侧人工标注，右侧预测`,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function table(s,values,x,y,w,h,widths){const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){let a=t.getCell(r,c);a.fill=r===0?'#E8F3F3':'#FFFFFF';a.text.style={typeface:'黑体',fontSize:24,color:r===0?teal:ink,bold:r===0,verticalAlignment:'middle'};}
 t.borders.assign({style:'solid',fill:'#CCDADA',width:.7});return t;}
const m=metrics.metrics;const v=k=>(m[k]*100).toFixed(1);
// Template cover and footer artwork remain inherited from its original layout.
tx(cover,'水下场景实例分割研究',130,228,1020,60,44,{font:'宋体',align:'center',bold:true});
tx(cover,'Mask2Former 基线结果、误差诊断与研究计划',140,296,1000,42,28,{font:'宋体',align:'center'});
tx(cover,'阶段汇报 · 整合版',400,453,480,50,28,{align:'center'});
tx(cover,status.date,965,599,245,44,28,{font:'宋体',align:'right'});
note(cover,'本次汇报涵盖基线实验、错误案例和后续路线。尚未提出并验证自有改进模型。模板中的汇报人姓名不沿用。');
let s=content[0];heading(s,1,'研究目标与当前进展');
line(s,'研究任务：识别水下物体类别，并分别分割每一个实例',203);
line(s,'已完成：UIIS 数据核验、训练恢复流程、36 轮正式基线',307);
line(s,`当前结果：691 张测试图，实例分割 AP ${v('coco/segm_mAP')}`,411);
line(s,'当前阶段：全量阈值诊断已完成，待边界评价与模块适配',515);
note(s,'第一研究点以 Mask2Former 为基线，候选模块来自 WaterMask。第二研究点仍未最终确定。本次没有模块改进成绩。');
s=content[1];heading(s,2,'UIIS 数据集与使用规则');
table(s,[['划分','图片数','实例数'],['训练集','3937','24626'],['测试集','691','3784']],65,196,670,207,[300,175,195]);
tx(s,'7 类水下目标',805,202,360,44,28,{bold:true});tx(s,'鱼、礁石、水草\n残骸、潜水员、机器人、海底',805,266,370,140,25);
line(s,'沿用官方原始划分，所有后续对照使用相同数据规则',451,25);
line(s,'保留已知 1 对跨划分重复图片，并在结果中披露',524,25);
note(s,'测试标注文件名为 val.json，但官方用途为测试集。训练 XL_266.jpg 与测试 XL_679.jpg 字节一致，按用户确认规则保留。未排查近重复，未另划内部验证集。','reports/uiis-audit.json；data/UIIS/download-manifest.json；https://github.com/LiamLian0727/WaterMask');
s=content[2];heading(s,3,'Mask2Former 基线实验设置');
table(s,[['项目','本次设置'],['模型与初始化','Mask2Former-R50，COCO 整模型预训练'],['训练数据与精度','UIIS 七类，单卡 V100 32GB，FP32'],['批量与训练预算','batch 2，36 轮，共 70,884 步'],['优化器与学习率','AdamW，0.0001，第 27 / 33 轮衰减'],['训练与测试尺寸','训练 1024 LSJ，测试保持比例 (1333, 800)'],['模型选择','固定最后第 36 轮，训练期间不按测试集选优']],65,181,1150,392,[280,870]);
tx(s,'尚未加入 DSGAT、MFRM 或 BLL',65,600,1150,44,25,{color:teal});
note(s,'七类分类层重新初始化。骨干学习率倍率 0.1。seed 20261012。恢复时核对轮数、步数、优化器和调度器状态。原官方配置文件名含 8xb2、50e，不代表本次卡数和轮数。','reports/formal-training-preflight.json；reports/uiis-baseline-36e-evaluation/evaluation-config.py');
s=content[3];heading(s,4,'正式基线评估结果');
table(s,[['评价任务','AP','AP50','AP75'],['实例分割',v('coco/segm_mAP'),v('coco/segm_mAP_50'),v('coco/segm_mAP_75')],['检测框',v('coco/bbox_mAP'),v('coco/bbox_mAP_50'),v('coco/bbox_mAP_75')]],65,197,1150,211,[460,230,230,230]);
line(s,'固定最终权重，完整评估官方 691 张测试图片',448,25);
line(s,'AP50 / AP75 分别采用 0.50 / 0.75 的掩码重合阈值',512,24);
line(s,'主 AP 综合多个重合阈值，数值不是像素正确率',576,24);
note(s,'AP 对 IoU 0.50 至 0.95、步长 0.05 的阈值与类别平均，并考虑预测排序、误报和漏检。JSON 数值乘 100 展示。本次为单次实验。','reports/uiis-baseline-36e-evaluation/metrics.json；https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/cocoeval.py');
s=content[4];heading(s,5,'小目标与不同类别的表现');
table(s,[['目标尺寸','分割 AP'],['小目标',v('coco/segm_mAP_s')],['中目标',v('coco/segm_mAP_m')],['大目标',v('coco/segm_mAP_l')]],65,205,450,248,[290,160]);
const cats=[['类别','分割 AP'],...['fish','reefs','aquatic plants','wrecks/ruins','human divers','robots','sea-floor'].map(k=>[k,v('coco/'+k+'_precision')])];
table(s,cats,605,185,610,400,[420,190]);
tx(s,'小目标 AP 较低\n后文结合阈值诊断分析',65,503,490,95,26,{color:teal});
note(s,'类别 AP 字段名为 coco/类别_precision，来自最后的 segm classwise 评估。小目标 AP 低不直接证明边界模块是解决办法。类别样本不均衡，robots 测试实例仅17。','reports/uiis-baseline-36e-evaluation/metrics.json；data/UIIS/annotations/val.json');
s=content[5];heading(s,6,'与 WaterMask 官方结果的参考比较');
table(s,[['方法','AP','AP50','AP75'],['WaterMask R50，官方 3×','26.4','43.6','28.8'],['WaterMask R101，官方 3×','27.2','43.7','29.3'],['本次 Mask2Former R50',v('coco/segm_mAP'),v('coco/segm_mAP_50'),v('coco/segm_mAP_75')]],65,191,1150,255,[610,180,180,180]);
tx(s,'相对官方 R50 数值：AP 高 6.2 点',65,474,1150,48,28,{color:teal});
tx(s,'双方均为 36 轮，但优化器、增强和预训练条件未完全统一\nWaterMask 尚未自行复现，差值不属于自有模块的提升',65,538,1150,96,24);
note(s,'仅比较官方公布值与本次实测值。官方 3× 配置为36轮、SGD、多尺度缩放；本次为AdamW、LSJ、COCO整模型预训练。对方实际预训练加载仍需核对，不能声称公平控制条件下胜出。','https://github.com/LiamLian0727/WaterMask#main-results；https://raw.githubusercontent.com/LiamLian0727/WaterMask/mmdet2/configs/_our_/water_r50_fpn_ms3x.py；reports/uiis-baseline-36e-evaluation/metrics.json');
const cases=[
 ['案例一：主体识别与轮廓缺失',[4,1],['L_1032：鱼主体轮廓较接近标注','L_1001：上方细长部分缺失'],'同一模型在不同图像上的效果差异明显'],
 ['案例二：小目标与实例数量失配',[2,5],['L_1025：标注 4 条鱼，显示 0 条','L_1046：标注 5 个礁石，显示 15 个'],'漏检与多报需要分别分析，不能仅归结为边界'],
 ['案例三：区域划分与类别混淆',[0,3],['L_1000：鱼主体较接近，海底未显示','L_1029：同一目标附近出现鱼和礁石预测'],'原报告图同类同色，新诊断报告已补实例编号与分数']];
for(let i=0;i<3;i++){s=content[6+i];heading(s,7+i,cases[i][0]);await pic(s,cases[i][1][0],46,221,574,323);await pic(s,cases[i][1][1],658,221,574,323);tx(s,cases[i][2][0],46,175,590,40,22);tx(s,cases[i][2][1],658,175,585,40,22);tx(s,cases[i][3],52,560,1180,42,25,{color:teal});tx(s,'每幅图左侧为人工标注，右侧为预测。显示阈值 0.5，仅用于画图。',52,613,1180,35,21);note(s,'图片固定来自原报告前6张。展示阈值不用于AP计算。小鱼最高候选分数0.410，未显示不等于没有候选。实例数量差异为初步证据，尚未逐掩码匹配归因。','reports/uiis-baseline-36e-evaluation/examples；predictions.segm.json；README.md 第6节');}
s=content[9];heading(s,12,'第一研究点：逐步验证模块适配');
line(s,'当前 P2：已完成全量阈值诊断，边界质量仍待量化',189,26);
line(s,'下一步 P3：核对 DSGAT、MFRM、BLL 的作用与接口',283,26);
line(s,'先实现一个有针对性的适配，再做单模块及组合消融',377,26);
line(s,'严格对照原版 32.6 AP，固定训练设置并记录计算开销',471,26);
tx(s,'候选模块尚未实现，插入位置与效果均未定',65,582,1150,48,26,{color:teal});
note(s,'这页是研究计划而非已完成贡献。先核对原文和源码、输入输出、损失及初始化，再选最小适配。不能预设三个模块都必须加入或必然提高。种子重复验证和负结果也要记录。','README.md 第2节 P2–P5、E0–E6');
s=content[10];heading(s,13,'后续安排与待讨论问题');
table(s,[['阶段','计划交付'],['近期：完成 P2/P3','已完成诊断图与阈值统计，待边界分析及接口核对'],['随后：P4/P5','单模块实验、消融表、稳定性与开销记录'],['第二研究点：P6/P7','DINOv2 / DiveSeg 为候选，先确定独立问题'],['论文整理：P8','两点方法与证据、已有方法对比、局限与复现说明']],65,189,1150,310,[365,785]);
tx(s,'需要讨论：第一点优先解决哪类错误？第二点如何形成独立贡献？',65,534,1150,92,27,{color:teal});
note(s,'第二点未定案。TIDE 可作诊断工具，本身不自动构成创新。当前已有完整基线，尚无自有改进成绩。下一次汇报重点是问题证据与适配方案，不承诺预期涨点。','README.md 第2节、第12节');


heading(protocol,10,'整体评估与误差诊断的关系');
table(protocol,[['比较项','正式基线评估','全量误差诊断'],['数据来源','第36轮，691张测试图','同一权重、同一批预测'],['回答的问题','总体分割表现如何','漏检与误报体现在哪里'],['指标口径','COCO AP / AP50 / AP75','固定IoU 0.5，三档置信度'],['已完成产出','AP 32.6，类别及尺寸AP','匹配统计、错误分组、诊断图'],['后续用途','改进模型的成绩对照','确定研究问题及适配动机']],65,185,1150,330,[230,460,460]);
tx(protocol,'未重新训练，正式 AP 仍为 32.6',65,545,1150,48,28,{color:teal});
tx(protocol,'匹配率不是 AP，不能把两种数值的差异当作精度提升',65,606,1150,38,24);
note(protocol,'整合v1正式基线与v2诊断进展，避免将两套统计误认为两次模型实验。诊断处理36个crowd标注，普通标注3748个。','reports/uiis-baseline-36e-evaluation/metrics.json；reports/uiis-error-analysis/diagnostics.json');

const diag=JSON.parse(await fs.readFile(path.join(ROOT,'reports/uiis-error-analysis/diagnostics.json'),'utf8'));
heading(diagnostics,10,'全量诊断：小目标更容易未匹配');
table(diagnostics,[['置信度阈值','预测数','匹配数','未匹配标注'],...['0.3','0.5','0.7'].map(t=>[t,...['predictions','matched','missed'].map(k=>String(diag.totals[t][k]))])],65,185,1150,245,[340,270,270,270]);
tx(diagnostics,'置信度 0.5 时：小目标匹配率 54.9%，大目标 73.1%',65,466,1150,62,26,{color:teal});
tx(diagnostics,'691 张图，3748 个普通标注，36 个 crowd 标注单独处理\n同类别 mask IoU ≥ 0.5 配对；这是诊断统计，不是 AP',65,546,1150,90,24);
note(diagnostics,'三档阈值的匹配数、忽略数和预测数已与官方 COCOeval 验证一致。阈值仅分析已有预测，不改变AP、模型权重或数据划分。','reports/uiis-error-analysis/diagnostics.json；scripts/verify-uiis-error-analysis.py');
heading(errors,11,'误报构成与结论边界');
table(errors,[['未匹配预测分组','数量'],['低重合背景','1596'],['同类定位不足','444'],['类别混淆','260'],['类别与定位混合','84'],['重复预测','51']],65,180,1150,335,[850,300]);
tx(errors,'不能把所有问题都归结为边界：还存在漏检与误报',65,541,1150,48,25,{color:teal});
tx(errors,'置信度 ≥ 0.5；78 个 crowd 忽略预测不计入上述分组',65,603,1150,40,23);
note(errors,'自定义互斥分组，顺序为重复、类别混淆、同类定位、异类定位、背景。背景指mask IoU低于0.1，不证明语义上完全没有目标。不是TIDE，不量化AP损失。已生成固定前6张原图/标注/预测三栏诊断图，每实例单独编号与置信度。下一步补充边界指标后核对模块接口。','reports/uiis-error-analysis/report.md；scripts/analyze-uiis-errors.py');

tx(close,'敬请老师批评指正',250,253,800,92,49,{font:'宋体',align:'center'});tx(close,'当前成果：正式基线与初步问题分析',235,421,820,48,30,{align:'center'});tx(close,status.date,965,599,245,44,28,{font:'宋体',align:'right'});note(close,'总结：已完成基线实验，下一步进入有针对性的模块适配。');
const candidate=path.join(BUILD,'candidate.pptx');await (await PresentationFile.exportPptx(p)).save(candidate);
for(let i=0;i<p.slides.items.length;i++){await fs.writeFile(path.join(BUILD,`slide-${i+1}.png`),new Uint8Array(await (await p.export({slide:p.slides.items[i],format:'png',scale:1})).arrayBuffer()));}
const {finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const hash=crypto.createHash('sha256').update(await fs.readFile(TEMPLATE)).digest('hex');
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath,pythonExecutable:path.join(RUNTIME,'python/python.exe'),integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],requiredNativeTableOwnerSlides:[3,4,5,6,7,11,12,13,15],fontPolicy:{basis:'reference',families:['宋体','黑体'],referencePath:TEMPLATE,referenceSha256:hash},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,status.outputName+'.validation.json')});
console.log(JSON.stringify(result));