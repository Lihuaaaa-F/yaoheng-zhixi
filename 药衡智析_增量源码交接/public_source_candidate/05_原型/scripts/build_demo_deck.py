"""Build a local synthetic-only presentation using python-pptx and a PDF reading companion.
Optional locked python-pptx dependency; no private source data or screenshots.
"""
from pathlib import Path
import argparse
SLIDES=[
('药衡智析','数值可信 · 证据适用 · 缺证可解释 · 任务可核查\n同一核心，制药主线与机械/化工合成迁移验证\n2026年重庆市AI大模型创新应用大赛｜演示稿，真人审核待完成'),
('业务闭环','导入与勾稽 → 确定性分析 → 适用证据检索 → 结构化解释\n固定章节Word/PDF → 人工确认 → HTTP模拟RPA → 状态核查\n模拟送达不等于真实微信或整改完成'),
('可信数字','Decimal金额；产量独立去重，不随成本明细重复累加\n季度单位成本 = Σ成本 / Σ可比产量\n缺失、零与无定义分开；单位/币种/政策冲突无依据则拒算'),
('上下文与行业包','核心：事实合同、指标、检索、模型、报告、审核和outbox\n行业包：字段语义、术语、证据门槛、可信策略与章节配置\n企业：产品/规格、计量、会计政策、责任人与连接配置\n任务创建后绑定不可变版本，切换企业不能串用证据'),
('机械合成迁移','独立工单与机时语义，产出以件计\n六月：3600元 / 120件 = 30元/件\n季度：9400元 / 320件 = 29.375元/件\n机时：60小时 / 120件 = 0.5小时/件\n全部数字为合成假定，不是行业基准'),
('化工合成迁移','批次与合格产出语义，产出以kg计；成本支持第四要素（合成包扩展口径；制药主线仍为三要素）\n2400元 / 200kg = 12元/kg\n600kWh / 200kg = 3kWh/kg\n缺WIP、联副产品政策和实价实耗时明确禁算\n全部数字为合成假定，不是行业基准'),
('验收与边界','原制药场景与季度独立回归；公开合成反例覆盖多类风险\n运行模型身份/usage/解释覆盖与真人0—5评分分别记录\n热力图、任务汇总、行业切换、图谱、路由、决策、预测均已实现\n运行数据库/密钥/待发队列不入库；模拟送达不冒充真人整改'),
('加分项·知识图谱与多模型','图谱：产品-药材-工序从知识快照确定性抽取，检索词增强+前端可视化\n多模型：narrative=glm-5.3-flash，决策说明=glm-4.5-air 轻量路由\n调用账本按任务路由分开记账，身份核验与预算独立\n未配置第二模型时同源回退并如实标注，不伪造多模型实调'),
('加分项·自主决策与预测','决策：无报告/数据变化→建议生成报告；同快照→仅更新看板\n确定性策略+小模型说明+SQLite台账，可按决策一键入队报告\n预测：Holt双参数指数平滑，总体与分要素，80%区间带\n预测是趋势外推参考，不构成预算承诺；负外推显式告警'),
('后续规划与交接','先完成一个细分行业的真实数据闭环，再扩展下一行业\n核对数据来源许可、成本政策、字段、专业知识与证据门槛\n优先改行业包和企业配置；核心不足先给最小反例\n重要非视觉工作由主力大模型完成，视觉检查按需使用轻量视觉模型\n专业归因、可读性和版式仍须真人评审')]

def main():
 from pptx import Presentation
 from pptx.util import Inches,Pt
 from pptx.dml.color import RGBColor
 import fitz
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--reading-preview',action='store_true');a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 pres=Presentation();pres.slide_width=Inches(13.33);pres.slide_height=Inches(7.5)
 pdf=fitz.open();font=Path(__file__).resolve().parents[1]/'assets/fonts/NotoSansSC-Regular.ttf'
 for index,(title,body) in enumerate(SLIDES,1):
  slide=pres.slides.add_slide(pres.slide_layouts[6]);slide.background.fill.solid();slide.background.fill.fore_color.rgb=RGBColor.from_string('F7FAFB')
  for x,y,w,h,text,size,color in [(0.7,0.6,12,0.9,title,32,'174C5F'),(0.7,2,12,4.8,body,21,'243C48'),(0.7,7,12,0.3,f'药衡智析 · 合成演示与验收边界 / {index}',11,'567580')]:
   box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=box.text_frame;tf.word_wrap=True
   for i,line in enumerate(text.splitlines()):
    para=tf.paragraphs[0] if i==0 else tf.add_paragraph();para.text=line;para.font.name='Noto Sans SC';para.font.size=Pt(size);para.font.color.rgb=RGBColor.from_string(color);para.space_after=Pt(15 if size==21 else 0)
  if a.reading_preview:
   page=pdf.new_page(width=960,height=540);page.draw_rect(page.rect,color=None,fill=(.97,.98,.985));page.insert_font(fontname='Noto',fontfile=str(font))
   page.insert_text((50,75),title,fontname='Noto',fontsize=31,color=(.09,.30,.37))
   y=160
   for line in body.splitlines():
    rc=page.insert_textbox(fitz.Rect(50,y,910,y+65),line,fontname='Noto',fontsize=20,color=(.14,.24,.28))
    if rc<0:raise ValueError('Slide text overflow')
    y+=57
   page.insert_text((50,515),f'合成演示 · 真人审核待完成 / {index}',fontname='Noto',fontsize=11)
 path=a.output_dir/'药衡智析_演示与答辩稿.pptx';pres.save(path)
 reopened=Presentation(path)
 if len(reopened.slides)!=len(SLIDES):raise ValueError('Slide count mismatch')
 if a.reading_preview:
  preview=a.output_dir/'_reading_preview';preview.mkdir(exist_ok=True)
  pdf.save(preview/'药衡智析_演示与答辩稿_阅读版.pdf')
  for i,page in enumerate(pdf):page.get_pixmap(matrix=fitz.Matrix(.8,.8)).save(preview/f'slide-{i+1}.png')
 print('Verified PPTX slides:',len(reopened.slides),'reading preview:',a.reading_preview,'; native rendering is separate')
if __name__=='__main__':main()
