"""OOXML 出厂兼容校验（Word 严格、LibreOffice 宽容）。

2026-09-22 事故根因：模板手术曾用 xml.etree.ElementTree 重序列化整份
document.xml，序列化丢失原命名空间前缀（w:→ns0:、mc:→ns1:、w14:→ns2:），
根元素的 mc:Ignorable="w14 w15 wp14" 仍按前缀引用，但这些前缀已不在
文件中声明。按 OOXML 标记兼容规范该文件非法——MS Word 直接报"文件可能
已经损坏"（wdmain11.chm 25272）拒开；LibreOffice 宽容放行，因此 PDF
转换与机器审计全绿也拦不住。

任何 docx 出厂（模板安装/模板规范化/报告渲染）都必须先通过本校验：
违规抛 ValueError 让任务显式失败，杜绝静默交付 Word 打不开的文件。
"""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree

MC_NS = 'http://schemas.openxmlformats.org/markup-compatibility/2006'


def validate_word_compat(path) -> dict:
    """校验 docx 的 Word 兼容性。

    检查项（Word 拒开的高频根因，LibreOffice 均宽容）：
    ① [Content_Types].xml 必须存在；
    ② 所有 xml/rels 部件必须是良构 XML；
    ③ mc:Ignorable 引用的每个前缀必须在该元素作用域内已声明
       （lxml 的 nsmap 含继承声明，正是"作用域内"语义）。

    返回 {'status':'PASS','parts':N}；违规抛 ValueError，消息列出
    部件名与原因，便于定位到具体 XML。
    """
    path = Path(path)
    problems = []
    parts = 0
    with ZipFile(path) as z:
        names = z.namelist()
        if '[Content_Types].xml' not in names:
            problems.append('[Content_Types].xml 缺失')
        for name in names:
            if not name.endswith(('.xml', '.rels')):
                continue
            parts += 1
            try:
                root = etree.fromstring(z.read(name))
            except etree.XMLSyntaxError as exc:
                problems.append(f'{name}: XML 解析失败（{exc}）')
                continue
            for el in root.iter():
                value = el.get(f'{{{MC_NS}}}Ignorable')
                if not value:
                    continue
                declared = set(el.nsmap) | {'xml'}
                for token in value.split():
                    if token not in declared:
                        problems.append(
                            f'{name}: mc:Ignorable 引用未声明前缀 "{token}"'
                            '（Word 判定文件损坏的典型根因：重序列化丢失命名空间前缀）')
    if problems:
        raise ValueError('WORD_COMPAT_CHECK_FAILED: ' + '; '.join(problems))
    return {'status': 'PASS', 'parts': parts}
