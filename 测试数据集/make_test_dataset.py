# -*- coding: utf-8 -*-
"""生成“测试数据集”文件夹内容（幂等，可重复运行）。

数据来源与改写规则：
- 业务 CSV 从仓库根目录的 导入示例/ 派生：工厂/产品名统一加“测试”前缀，
  企业名改为 测试药厂；数值保持与源数据一致（源数据已通过解析校验，
  勾稽关系成立），保证本测试集可直接通过后端字段映射与质量校验。
- 行业参考 CSV、知识文档为本目录独立编制，全部内容标注“测试数据”。
- 报告模板由已验证可解析的示例模板改写（python-docx 逐段替换企业名）。

所有文件仅为“药衡智析”功能演示构造，与现实企业、行业数值无关。
"""
from __future__ import annotations

import csv
import io
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / '导入示例'

RENAME_TEXT = [('示例药厂', '测试药厂'), ('示例一厂', '测试一厂'), ('示例二厂', '测试二厂')]

BUSINESS_FILES = [
    '示例药厂_成本汇总_2025年1-6月.csv',
    '示例药厂_成本汇总_2026年1-6月.csv',
    '示例药厂_原材料消耗明细_2026年1-6月.csv',
    '示例药厂_制造费用明细_2026年1-6月.csv',
    '示例药厂_人工工时明细_2026年1-6月.csv',
    '示例药厂_预算数据_2026年.csv',
]


def _prefixed(value: str) -> str:
    value = value.strip()
    for old, new in RENAME_TEXT:
        value = value.replace(old, new)
    if value and not value.startswith('测试'):
        value = '测试' + value
    return value


def derive_business_csv(name: str, target: Path) -> None:
    raw = (SOURCE / name).read_text(encoding='utf-8-sig')
    rows = list(csv.reader(io.StringIO(raw)))
    if not rows:
        raise SystemExit(f'{name}: 空文件')
    header = rows[0]
    factory_col = header.index('工厂') if '工厂' in header else None
    product_col = header.index('产品名称') if '产品名称' in header else None
    out_rows = []
    for row in rows:
        row = list(row)
        for index, cell in enumerate(row):
            for old, new in RENAME_TEXT:
                cell = cell.replace(old, new)
            row[index] = cell
        if factory_col is not None and row[factory_col].strip():
            row[factory_col] = _prefixed(row[factory_col])
        if product_col is not None and row[product_col].strip():
            row[product_col] = _prefixed(row[product_col])
        out_rows.append(row)
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator='\r\n').writerows(out_rows)
    target.write_text('\ufeff' + buffer.getvalue(), encoding='utf-8')


INDUSTRY_ROWS = [
    ['产品类别', '指标', '行业P25', '行业P50', '行业P75', '样本说明'],
    ['颗粒剂类', '材料成本占比', '52%', '58%', '65%', '测试数据：虚构区间，仅演示'],
    ['颗粒剂类', '人工成本占比', '18%', '22%', '27%', '测试数据：虚构区间，仅演示'],
    ['颗粒剂类', '制造费用占比', '15%', '19%', '24%', '测试数据：虚构区间，仅演示'],
    ['口服液类', '材料成本占比', '55%', '62%', '68%', '测试数据：虚构区间，仅演示'],
    ['口服液类', '人工成本占比', '16%', '20%', '25%', '测试数据：虚构区间，仅演示'],
    ['口服液类', '制造费用占比', '14%', '17%', '22%', '测试数据：虚构区间，仅演示'],
    ['胶囊类', '材料成本占比', '50%', '57%', '64%', '测试数据：虚构区间，仅演示'],
    ['胶囊类', '人工成本占比', '17%', '21%', '26%', '测试数据：虚构区间，仅演示'],
    ['胶囊类', '制造费用占比', '16%', '20%', '25%', '测试数据：虚构区间，仅演示'],
]

PRODUCT_KNOWLEDGE = '''【测试数据声明】本文档是"药衡智析"演示用测试数据集的一部分，全部内容为独立编制的虚构资料，与任何真实企业、真实产品、真实行业数值无关；用于演示证据检索与引用，不得作为现实决策依据。

产品知识档案：测试板蓝根颗粒
企业：测试药厂（虚构测试企业）
产品规格：10g×10袋/盒
主要成分：板蓝根、大青叶、蔗糖糊精辅料。
工艺流程：净药材投料→水提两次（合并提取液）→减压浓缩→喷雾干燥制粒→总混→铝塑包装→装箱入库。
产能与瓶颈：提取与浓缩环节为产能瓶颈；单批投料 120 万袋，月度排产 2～4 批。
质量标准：浸出物、栀子苷转移率按企业内控标准（测试值）执行；微生物限度按现行药典要求（演示口径）。
成本波动机制（测试说明）：药材收获季节性影响采购价；提取收率波动 1 个百分点约影响单位材料成本 2%（测试系数）；蒸汽与电力价格在夏季高峰期上浮，制造费用随之变化。
关键记录：批生产记录、药材采购台账、提取收率化验单、月度能耗分摊表。

产品知识档案：测试六味地黄胶囊
企业：测试药厂（虚构测试企业）
产品规格：0.5g×24粒/盒
主要成分：熟地黄、山茱萸、山药、泽泻、牡丹皮、茯苓。
工艺流程：药材净制→提取浓缩→干膏粉碎→填充胶囊→铝塑泡罩包装。
产能与瓶颈：填充与铝塑环节节拍决定产量；月度产能 80 万盒（测试值）。
质量标准：丹皮酚含量按内控标准（测试值）；装量差异按药典演示口径。
成本波动机制（测试说明）：熟地黄、山茱萸采购价季节波动明显；胶囊壳价格受明胶行情影响；包装材料（铝箔、PVC）按季度招标定价。
关键记录：批生产记录、药材采购台账、装量差异检验记录、包装材料入库单。
'''

INDUSTRY_KNOWLEDGE = '''【测试数据声明】本文档是"药衡智析"演示用测试数据集的一部分，行业基准区间为独立编制的虚构数值，不是任何真实行业协会或统计机构发布的数据；仅用于演示行业参考对比功能。

行业成本参考说明（测试数据，2026 年演示口径）
一、材料成本占比：中药制造行业常见区间为 50%～68%（测试区间），颗粒剂类中位约 58%，口服液类中位约 62%。材料占比偏高通常指向药材采购价上涨或消耗上升，须核对采购台账与实物耗量。
二、人工成本占比：常见区间 16%～27%（测试区间）。占比偏高时优先核对工时台账与工资分配口径。
三、制造费用占比：常见区间 14%～25%（测试区间）。占比偏高时核对费用归集范围、折旧与能耗分摊方法是否变化。
四、使用限制：行业参考为静态演示数据，不是所选月份的实测行业水平；不能替代企业自身的预算与标准成本；缺收入口径时毛利率与费用收入比不可独立计算。
五、证据引用说明：本文件可被系统的证据检索命中，用于演示"行业参考数据"区块与解释的证据引用链路；引用前应核对其"测试数据"标注。
'''

TEMPLATE_DISCLAIMER = ('数据说明（测试数据）：本模板属于"药衡智析"演示用测试数据集，'
                       '企业、产品与数值均为虚构，仅用于演示报告结构。')


def rewrite_template(target: Path) -> None:
    import docx
    document = docx.Document(str(SOURCE / '示例药厂_月度成本分析报告模板.docx'))
    replaced = 0

    def replace_in_paragraphs(paragraphs) -> None:
        nonlocal replaced
        for paragraph in paragraphs:
            for run in paragraph.runs:
                if '示例药厂' in run.text:
                    run.text = run.text.replace('示例药厂', '测试药厂（测试数据）')
                    replaced += 1

    replace_in_paragraphs(document.paragraphs)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                replace_in_paragraphs(cell.paragraphs)
    if not replaced:
        document.add_paragraph(TEMPLATE_DISCLAIMER)
    else:
        document.add_paragraph('')
        document.add_paragraph(TEMPLATE_DISCLAIMER)
    document.save(str(target))


def main() -> None:
    business = HERE / '业务数据'
    industry = HERE / '行业参考数据'
    knowledge = HERE / '知识文档'
    templates = HERE / '报告模板'
    for folder in (business, industry, knowledge, templates):
        folder.mkdir(parents=True, exist_ok=True)
    for name in BUSINESS_FILES:
        target = business / ('测试数据_' + name.replace('示例药厂', '测试药厂'))
        derive_business_csv(name, target)
        print('业务数据:', target.name)
    industry_csv = industry / '测试数据_中药行业成本基准_2026.csv'
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator='\r\n').writerows(INDUSTRY_ROWS)
    industry_csv.write_text('\ufeff' + buffer.getvalue(), encoding='utf-8')
    print('行业参考数据:', industry_csv.name)
    product_doc = knowledge / '测试数据_测试药厂_产品知识.txt'
    product_doc.write_text(PRODUCT_KNOWLEDGE, encoding='utf-8')
    industry_doc = knowledge / '测试数据_行业成本参考说明.txt'
    industry_doc.write_text(INDUSTRY_KNOWLEDGE, encoding='utf-8')
    print('知识文档:', product_doc.name, ',', industry_doc.name)
    template = templates / '测试数据_测试药厂_月度成本分析报告模板.docx'
    rewrite_template(template)
    print('报告模板:', template.name)
    print('完成：', HERE)


if __name__ == '__main__':
    main()
