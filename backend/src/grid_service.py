from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select
from .models import Layout,Sweep
from .grid_models import ConditionGrid
from .calibration_service import locked
from .services import get,pack,audit
MIN_SAMPLES=3
SPEED_AXIS=(0.0,100.0)
ANGLE_AXIS=(-30.0,30.0)

def signed_layout(s,id):
    l=locked(s,Layout,id)
    if l.status!='signed':raise HTTPException(409,'工况表须基于已审签布置，同一套接线的留出预测才作数')
    return l

def normalize(intervals,axis,bounds,label):
    out=sorted(({'lo':float(i.lo),'hi':float(i.hi)} for i in intervals),key=lambda x:(x['lo'],x['hi']))
    for iv in out:
        if iv['lo']<bounds[0] or iv['hi']>bounds[1]:raise HTTPException(409,f'{label}区间超出{label}登记包线{bounds[0]}–{bounds[1]}')
    for a,b in zip(out,out[1:]):
        if b['lo']<a['hi']:raise HTTPException(409,f'{label}区间须不重叠：{a["lo"]}–{a["hi"]} 与 {b["lo"]}–{b["hi"]} 相接或重叠')
    return out

def locate(value,intervals):
    # 左闭右开 [lo, hi)；全表最高端点归属最高区间，包线顶值不落到表外
    for i,iv in enumerate(intervals):
        if iv['lo']<=value<iv['hi'] or (i==len(intervals)-1 and value==iv['hi']):return i
    return None

def evaluate(s,layout,speed_intervals,angle_intervals,mae_limit):
    holdout=(layout.evidence or {}).get('holdout') or []
    sweeps={x.code:x for x in s.scalars(select(Sweep))}
    cells=[]
    for si,siv in enumerate(speed_intervals):
        for ai,aiv in enumerate(angle_intervals):
            readings=[]
            for h in holdout:
                sw=sweeps.get(h['sweep'])
                if not sw:continue
                if locate(sw.speed,speed_intervals)==si and locate(sw.angle,angle_intervals)==ai:
                    readings.append({'sweep':sw.code,'actual':h['actual'],'predicted':h['predicted'],'abs_error_n':round(abs(h['actual']-h['predicted']),3)})
            mae=round(sum(x['abs_error_n'] for x in readings)/len(readings),3) if readings else None
            cells.append({'speed_index':si,'angle_index':ai,'speed':siv,'angle':aiv,'samples':len(readings),'mae_n':mae,'passed':mae is not None and len(readings)>=MIN_SAMPLES and mae<=mae_limit,'readings':readings})
    return cells

def failing(cells):return [c for c in cells if not c['passed']]
def describe(c):return f"{c['speed']['lo']}–{c['speed']['hi']}m/s × {c['angle']['lo']}–{c['angle']['hi']}°（样本{c['samples']}条" + (f"，误差{c['mae_n']}N）" if c['mae_n'] is not None else '）')

def view(s,x):return pack(x)|{'layout_code':get(s,Layout,x.layout_id).code}
def create(s,d,u):
    l=signed_layout(s,d.layout_id)
    speed=normalize(d.speed_intervals,'speed',SPEED_AXIS,'风速');angle=normalize(d.angle_intervals,'angle',ANGLE_AXIS,'攻角')
    x=ConditionGrid(layout_id=l.id,code=d.code,mae_limit=d.mae_limit,speed_intervals=speed,angle_intervals=angle,cells=evaluate(s,l,speed,angle,d.mae_limit))
    s.add(x);s.flush();audit(s,u,'划定工况表 '+x.code);return view(s,x)
def revise(s,id,d,u):
    x=locked(s,ConditionGrid,id)
    if x.state!='draft':raise HTTPException(409,'已签发工况表不可修改，换用工况表须另划新表并重新签发')
    if x.layout_id!=d.layout_id or x.code!=d.code:raise HTTPException(409,'工况表编号与布置关联不可变更')
    l=signed_layout(s,x.layout_id)
    speed=normalize(d.speed_intervals,'speed',SPEED_AXIS,'风速');angle=normalize(d.angle_intervals,'angle',ANGLE_AXIS,'攻角')
    x.speed_intervals=speed;x.angle_intervals=angle;x.mae_limit=d.mae_limit
    x.cells=evaluate(s,l,speed,angle,d.mae_limit)
    audit(s,u,'修订工况表 '+x.code);return view(s,x)
def issue(s,id,u):
    preview=get(s,ConditionGrid,id);l=signed_layout(s,preview.layout_id);x=locked(s,ConditionGrid,id)
    if x.state!='draft':raise HTTPException(409,'工况表已签发，重试不会新增签发表')
    cells=evaluate(s,l,x.speed_intervals,x.angle_intervals,x.mae_limit)
    bad=failing(cells)
    if bad:raise HTTPException(409,'样本不足三条或误差超限的格子不放行：'+'；'.join(describe(c) for c in bad[:4]))
    x.cells=cells;x.state='issued';x.issued_by=u.email;x.issued_at=datetime.now(timezone.utc).isoformat()
    audit(s,u,'负责人签发工况表 '+x.code);return view(s,x)
def current(s,layout_id):
    return s.scalar(select(ConditionGrid).where(ConditionGrid.layout_id==layout_id,ConditionGrid.state=='issued').order_by(ConditionGrid.issued_at.desc(),ConditionGrid.id.desc()).limit(1))
