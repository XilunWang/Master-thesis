"""Fixed-threshold mask diagnostics, not COCO AP or TIDE attribution.
Run with numpy, Pillow and pycocotools. Does not modify predictions or annotations.
"""
import json, hashlib, colorsys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pycocotools.coco import COCO
from pycocotools import mask as mu

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/uiis-baseline-36e-evaluation'
OUT = ROOT / 'reports/uiis-error-analysis'


def match(iou, predcats, gtcats, threshold=.5):
    """Predictions must be in descending confidence order; one-to-one same-class."""
    used = set()
    labels, matches = [], []
    for row, cat in zip(iou, predcats):
        available = [j for j, gc in enumerate(gtcats) if gc == cat and j not in used and row[j] >= threshold]
        if available:
            j = max(available, key=lambda j: row[j])
            used.add(j); labels.append('matched'); matches.append(j)
            continue
        same = [j for j, gc in enumerate(gtcats) if gc == cat]
        other = [j for j, gc in enumerate(gtcats) if gc != cat]
        if any(row[j] >= threshold for j in same):
            label = 'duplicate'
        elif any(row[j] >= threshold for j in other):
            label = 'class_confusion'
        elif any(row[j] >= .1 for j in same):
            label = 'localization'
        elif any(row[j] >= .1 for j in other):
            label = 'class_and_localization'
        else:
            label = 'background'
        labels.append(label); matches.append(None)
    return labels, matches, used


def self_test():
    labels, _, used = match(np.array([[.9,0],[.8,0],[0,.8],[0,.2],[0,0]]),[1,1,1,2,1],[1,2])
    assert labels == ['matched','duplicate','class_confusion','localization','background']
    assert used == {0}
    assert match(np.zeros((1,0)),[1],[])[0] == ['background']
    assert match(np.zeros((0,1)),[],[1])[2] == set()
    assert match(np.array([[.5]]),[1],[1])[0] == ['matched']


def panel(raw, anns, masks, names, title, predictions=False):
    width=800; height=round(raw.height*width/raw.width)
    canvas=raw.resize((width,height)).convert('RGB'); arr=np.array(canvas)
    for k, mask in enumerate(masks):
        region=np.array(Image.fromarray(mask.astype('uint8')*255).resize((width,height),Image.Resampling.NEAREST))>0
        color=np.array([round(x*255) for x in colorsys.hsv_to_rgb((k*.618034)%1,.75,1)])
        arr[region]=(arr[region]*.66+color*.34).astype('uint8')
    legend_height=32+24*len(anns)
    out=Image.new('RGB',(width,40+height+legend_height),'white');out.paste(Image.fromarray(arr),(0,40))
    draw=ImageDraw.Draw(out); font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    draw.text((8,8),title,fill='black',font=font)
    for k,(ann,mask) in enumerate(zip(anns,masks)):
        ys,xs=np.where(mask)
        color=tuple(round(x*255) for x in colorsys.hsv_to_rgb((k*.618034)%1,.75,1))
        if len(xs):
            x=min(width-42,int(np.median(xs)*width/raw.width)); y=min(height+14,int(np.median(ys)*height/raw.height)+40)
            draw.rectangle((x,y,x+40,y+24),fill='black');draw.text((x+2,y+1),str(k+1),fill=color,font=font)
        text=f'{k+1}: {names[ann["category_id"]]}'
        if predictions: text+=f'  score={ann["score"]:.3f}'
        draw.rectangle((8,48+height+k*24,22,62+height+k*24),fill=color)
        draw.text((28,44+height+k*24),text,fill='black',font=font)
    return out


def main():
    self_test();OUT.mkdir(exist_ok=True);(OUT/'examples').mkdir(exist_ok=True)
    annpath=ROOT/'data/UIIS/annotations/val.json';predpath=SOURCE/'predictions.segm.json'
    coco=COCO(str(annpath)); preds=json.loads(predpath.read_text())
    names={k:v['name'] for k,v in coco.cats.items()};grouped=defaultdict(list)
    for p in preds: grouped[p['image_id']].append(p)
    assert set(grouped)<=set(coco.imgs)
    # Support crowd explicitly; reject unsupported standalone ignore annotations.
    assert not any(a.get('ignore',0) and not a.get('iscrowd',0) for a in coco.anns.values())
    totals={str(t):Counter() for t in [.3,.5,.7]}; byclass=defaultdict(Counter); bysize=defaultdict(Counter); rows=[]
    for index,(iid,im) in enumerate(coco.imgs.items()):
        crowd=[a for a in coco.imgToAnns[iid] if a.get('iscrowd',0)]
        gt=[a for a in coco.imgToAnns[iid] if not a.get('iscrowd',0)]; gt_rles=[coco.annToRLE(a) for a in gt];gc=[a['category_id'] for a in gt]
        pp=sorted(grouped[iid],key=lambda p:-p['score']);pp=[p for p in pp if p['score']>=.3]
        iou=mu.iou([p['segmentation'] for p in pp],gt_rles,[0]*len(gt)) if pp and gt else np.zeros((len(pp),len(gt)))
        crowd_iou=mu.iou([p['segmentation'] for p in pp],[coco.annToRLE(a) for a in crowd],[1]*len(crowd)) if pp and crowd else np.zeros((len(pp),len(crowd)))
        local={}
        for threshold in [.3,.5,.7]:
            n=sum(p['score']>=threshold for p in pp)
            labels,matches,used=match(iou[:n],[p['category_id'] for p in pp[:n]],gc)
            for k,label in enumerate(labels):
                if label!='matched' and any(a['category_id']==pp[k]['category_id'] and crowd_iou[k,j]>=.5 for j,a in enumerate(crowd)):
                    labels[k]='ignored_crowd'
            c=Counter(labels);c.update(gt=len(gt),crowd_gt=len(crowd),predictions=n,missed=len(gt)-len(used))
            assert c['matched']+c['missed']==len(gt)
            assert sum(c[k] for k in ['matched','duplicate','class_confusion','localization','class_and_localization','background','ignored_crowd'])==n
            totals[str(threshold)].update(c);local[str(threshold)]=dict(c)
            if threshold==.5:
                for j,a in enumerate(gt):
                    size='small' if a['area']<32**2 else 'medium' if a['area']<96**2 else 'large'
                    for bucket in [byclass[names[a['category_id']]],bysize[size]]:
                        bucket['gt']+=1;bucket['matched' if j in used else 'missed']+=1
                for p,label in zip(pp[:n],labels):byclass[names[p['category_id']]][label+'_predictions']+=1
                for k,j in enumerate(matches):
                    if j is not None:totals['0.5']['matched_iou_ge_075' if iou[k,j]>=.75 else 'matched_iou_050_075']+=1
        rows.append({'image_id':iid,'file_name':im['file_name'],'thresholds':local})
        if index<6:
            raw=Image.open(ROOT/'data/UIIS/val'/im['file_name']).convert('RGB');show=[p for p in pp if p['score']>=.5]
            panels=[panel(raw,[],[],names,'Original image'),panel(raw,gt,[mu.decode(r) for r in gt_rles],names,'Ground truth: instance IDs'),panel(raw,show,[mu.decode(p['segmentation']) for p in show],names,'Prediction: score >= 0.5',True)]
            sheet=Image.new('RGB',(2400,max(x.height for x in panels)),'white')
            for j,p in enumerate(panels):sheet.paste(p,(j*800,0))
            sheet.save(OUT/'examples'/f'{iid}.jpg',quality=94)
        if index%100==0:print(f'Processed {index+1}/{len(coco.imgs)}',flush=True)
    report={'images':len(rows),'annotation_sha256':hashlib.sha256(annpath.read_bytes()).hexdigest(),'prediction_sha256':hashlib.sha256(predpath.read_bytes()).hexdigest(),'protocol':'score descending, same-category one-to-one greedy mask IoU >=0.5; crowd GT excluded; unmatched same-class crowd IoA>=0.5 ignored; confidence thresholds 0.3/0.5/0.7; not AP or TIDE','totals':totals,'by_class_at_05':byclass,'by_size_at_05':bysize,'per_image':rows}
    (OUT/'diagnostics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    lines=['# UIIS 基线误差诊断','',f'完整分析 {len(rows)} 张测试图；原始预测、标注和正式 AP 均未修改。','', '## 统计口径','', '预测按置信度降序，以同类别 mask IoU≥0.5 与未匹配普通标注一对一配对。crowd 标注不算漏检；未匹配预测与同类 crowd 的 IoA≥0.5 时忽略，不计误报。非 AP、非 TIDE，不是各类错误对 AP 的损失归因。','', '未匹配预测按优先级分组：同类 IoU≥0.5 为重复；异类 IoU≥0.5 为类别混淆；同类 IoU≥0.1 为定位不足；仅异类 IoU≥0.1 为类别与定位混合；其余为低重合背景。定位不足包含整体范围偏差，不能等同于边界误差；重复也不能证明实例拆分。','', '|置信度阈值|预测数|匹配数|未匹配标注|重复|类别混淆|定位不足|混合|背景|crowd忽略|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for t,c in totals.items():lines.append('|'+t+'|'+'|'.join(str(c[k]) for k in ['predictions','matched','missed','duplicate','class_confusion','localization','class_and_localization','background','ignored_crowd'])+'|')
    for title,buckets in [('尺寸',bysize),('类别',byclass)]:
        lines+=['',f'## 按{title}统计（置信度≥0.5）','', '|分组|标注数|匹配数|未匹配数|匹配率|','|---|---:|---:|---:|---:|']
        for name,c in buckets.items():lines.append(f'|{name}|{c["gt"]}|{c["matched"]}|{c["missed"]}|{c["matched"]/c["gt"]:.1%}|')
    c=totals['0.5'];lines+=['',f'已匹配预测中，IoU≥0.75 为 {c["matched_iou_ge_075"]}，0.5≤IoU<0.75 为 {c["matched_iou_050_075"]}。这是匹配后的条件统计，不是 AP75。','', '## 固定前六张诊断图','', '从左至右：原图、标注、预测。每个面板实例分别编号和着色，下方图例列出类别和分数；左右编号不表示匹配关系。未筛选好图。']
    for row in rows[:6]:lines += ['',f'### {row["file_name"]}',f'![诊断图](examples/{row["image_id"]}.jpg)']
    lines+=['','## 结论边界与下一步','','先区分阈值敏感的小目标漏检、类别错误与掩码范围问题。当前统计不能证明 DSGAT/MFRM/BLL 有效，也未直接测量边界质量；下一步需补边界指标及模块接口核对，再确定首个适配。保留官方划分与已知重复，不再用测试集选择训练权重或调参。']
    (OUT/'report.md').write_text('\n'.join(lines),encoding='utf8');print(json.dumps(totals,ensure_ascii=False))

if __name__=='__main__':main()
