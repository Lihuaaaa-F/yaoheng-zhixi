# 审计发现：报告生成链（reports.py / reference_report.py / docx_compat.py）

- 审查对象：D:/yaoheng-audit-wt-1f78b2f（yaoheng-zhixi @ 1f78b2f，已核实 `git log -1`）
- 项目根：药衡智析_增量源码交接/public_source_candidate/05_原型/
- 方法：逐文件完整阅读（reports.py 1–1660 行全读）＋跨文件协议核对（metrics.py / narrative.py / worker.py / api.py / import_pipeline.py / jobs.py / versions.py / config.py 只读引用）＋题包模板原件 XML 实测解包（00_赛题原始资料/…/04_报告模板/月度成本分析报告模板.docx）
- 审查者无视觉能力：所有"待实测"项指需真实 Word/LibreOffice 渲染验证
- 行号均指本 worktree 中 reports.py（除非另注明文件）

---

## 0. 判定总览（赛题 5.1 对应项）

| 赛题要求 | 判定 | 依据 |
|---|---|---|
| 5.1.1 Word模板解析：固定章节标题+动态占位符 | 满足（静态确认） | PATTERN `{{…}}`（reports.py:17）；六章节完整性三道闸：data_import.check_template（import_pipeline.py:425 安装前六章节+占位符≥20）、verify_docx headings==6（reports.py:828）、convert_pdf PDF 层 page_map（reports.py:857-874） |
| 5.1.3 三种主题/月份/产品参数 | 满足 | working_template 按 monthly/quarterly/special 解析（31-41）；季度词替换+期间标签（367、589-591）；未安装季度/专题模板回退月度模板（绑定合同一致，注释 25） |
| 5.1.3 四层融合（模板+数据+RAG+模型文本） | 满足 | 模板结构 Document(template_path)（574）；数据 build_bindings（576）；RAG：证据引用/知识库引用/未引用证据清单（751-781）；模型文本 narrative findings 渲染+在体核验（562-566、525-548） |
| 5.1.3 PDF+Word 双格式导出、专业排版 | 满足（Word 实际分页待实测） | convert_pdf LibreOffice（834-923）；页脚 PAGE/NUMPAGES 域重建（988-1011）；页眉模板水印保留；表格边框/灰底表头/跨页重复/斑马纹/列宽自适应（602-638、1078-1212）；matplotlib 图嵌入居中（1544）；原生 TOC 域+缓存条目+PDF 分页回填（1402-1459、901-918） |
| 5.1.4 结构完整度机器校验 | 满足 | verify_docx：headings==6、residual==0、tables>=11、images>0、数值绑定逐项、重复单位（826-832） |
| 数字一致性（与 dashboard 同口径同源） | 满足 | 报告/看板/验收共用 JobStore 中同一 metrics 快照；verify_docx 用 build_bindings(snapshot,{}) 复算（809） |
| 占位符数值舍入 | 满足（half-even，见 F12） | number() 2 位小数、|x|<0.005 时 4 位防"0.00"（264-271）；环比/贡献度 rate 均为×100 后百分数（metrics.py:38-46 实核） |
| 除零/缺期/缺预算占位符行为 | 满足 | change()/contribution() 显式 None+reason（metrics.py:38-46、19-23）→ number(None)=NA='N/A（无可用基期或明细）'；模板 '）%' 尾巴清理（593、822） |
| 生成器/验收器协议一致、非恒真 | 满足（自洽校验边界见 F3） | 验收看的是保存后文件重解压的书签处实际文本 vs 复算期望（815-825），可发现丢替换/舍入错/残留/错位；reference 路径角色绑定 verify（reference_report.py:21-113） |
| 失败路径 | 满足（瑕疵 F2/F9） | 见 §3 |
| docx 改写用 lxml 不用 xml.etree | 满足 | 序列化仅 LET.tostring（107、256）；ET 仅 verify 只读解析（807/813/830）；docx_compat 出厂闸（normalize 261 / install 111 / render 788） |

判定统计：满足 10、部分满足 1（6.2"需关注问题"与 3.3"变动说明"为固定文案非模型文本，见 F6）、不满足 0、未实现 0、待实测 3（W1-W3）。

---

## 1. 逐函数记录（reports.py，43 个函数全部覆盖）

| # | 函数:行 | 职责 | 前提（谁建立） | 异常路径 | 调用关系 |
|---|---|---|---|---|---|
| 1 | working_template:31 | 按报告类型选模板：RUNTIME/templates/{type}.docx 优先，回退题包工作模板 | RUNTIME 目录由 config 创建；安装由 install_template 建立 | 缺文件静默回退（设计） | api._generation_versions、worker:47、render_docx:570、installed_templates |
| 2 | installed_templates:44 | 已安装模板清单（数据中心展示） | 同上 | map 损坏→meta={} 容错（52-53） | api 模板页 |
| 3 | install_template:61 | 用户模板安装：占位符→书签、同名改名（_比例/_金额）、_relayout、validate、写 map | check_template 已保证六章节+≥20 占位符（import_pipeline.py:425-431） | 类型非法 raise UNKNOWN_TEMPLATE_TYPE；validate_word_compat 违规 raise | import_pipeline.run_template_parse:437 |
| 4 | _relayout_front_section:120 | 安装模板手术：前置区解分页/删目录域；概览表三要素同比空白格补绑定 | 概览表含"去年同月"表头 | 章节缺失跳过分页调整；无该表安全跳过（159-161） | install_template:110 |
| 5 | replace_text_nodes:182 | 跨 run 拆分安全替换，保留 run 样式 | nodes 为同一 w:p 内全部 w:t | 无（mapping 未命中即跳过） | normalize/install/render 主替换 |
| 6 | binding_semantics:197 | 占位符名→语义数据源+单位（map 清单元数据） | 命名合同与 build_bindings 键一致 | nothing found（无显式异常；未匹配走末行兜底 period_values） | normalize/install 元数据 |
| 7 | normalize_template:221 | 题包原件→工作模板：改名、书签、贡献度合计 100% 单元格替换（i==235）、compact、validate、写 map | PACKAGE/04_报告模板 存在 .docx（config.py:20） | 锁文件跳过（222）；原件缺失→next() StopIteration→任务 FAILED（fail-closed） | render_docx:572、api:175 |
| 8 | number:264 | 数值格式化：dict 取 value；None→NA；2 位小数、非零且 <0.005 升 4 位 | — | 异常→str(value) 原样 | 全渲染/验收链 |
| 9 | _text:273 | 简单 run 保留替换（首 run 承载全文） | — | old 不在则 no-op | sanitize、render N/A 清理 |
| 10 | rewrite_template_prose:282 | 静态模板文字替换（季度词），RESIDUAL 保护占位符区 | — | 无 | render_docx:591 |
| 11 | _all_paragraphs:305 | body 全部段落（含表格外 body 直属，python-docx Paragraph 包装） | — | — | 多处 |
| 12 | layout_text:309 | 清 U+2060/U+FEFF，NBSP→空格（只清排版符不动数值） | — | — | 验收/排版链 |
| 13 | protect_number_units:314 | 数字与单位间只注 NBSP（FEFF 已停注，注释 316-320）；含占位符段跳过 | — | — | style_reader |
| 14 | report_period_label:339 | 期间标签 | period 或 month | 缺→'期间未提供' | 尾注 764 |
| 15 | benchmark_precision:345 | 季度 4 位小数，其余 2 位 | — | — | 对标表/图 |
| 16 | benchmark_labels:349 | 从 comparison 取两厂名+方向声明；缺失回退解析 direction；再缺回退占位名 | benchmark dict 可为 None | 方向冲突 raise BENCHMARK_DIRECTION_CONFLICT | build_bindings、图表、reference |
| 17 | build_bindings:365 | 占位符→值总装（117 行）：封面/三行对比/三要素/同比补绑/人工指标/制造费 5 类/文本占位 | snapshot 结构由 metrics.py build 建立（elements/period_values/period_changes/labor_metrics/expenses_summary/materials_summary/details/trend/alerts/budget_bridge 已实核存在） | 缺数→number(None)=NA；书签合同缺失字段 setdefault(NA)（render 577） | render_docx:576、verify_docx:809 |
| 18 | sanitize_template_identity:483 | 编制人/审核人等固定角色值；core_properties 作者改写 | 模板表格含这些标签 | 无（找不到即跳过） | render_docx:575 |
| 19 | insert_element_analysis:510 | 3.2/3.3 节末插入程序归因句+bindings 文本（人工绑定锚 '3.3'、制造费用锚 '四、'） | 模板存在以 '3.3'、'四、' 开头段落 | 缺失 raise MISSING_COST_SECTION:* → 任务 FAILED | render_docx:739 |
| 20 | explanation_presence:525 | 模型解释必须在对应章节正文逐字出现（3.1/3.2/3.3/5.3 分桶） | narrative.findings 带 origin/claim_type/section | 缺失记 failure → 上层 raise（见 F1） | verify_docx:799 |
| 21 | render_docx:551 | 主渲染（240 行）：非赛题 context 走 reference_report.render；否则模板装值→动态表→归因表→建议/整改表→图→摘要/TOC→题注→编制说明→样式→machine_audit→tmp 保存→verify→compat→replace | working_template/map 存在（模板缺失自动 normalize） | verify 不 PASS raise 报告验证失败；compat raise；tmp 不晋升 output | worker:100 |
| 22 | verify_docx:792 | 文件级验收：书签处实际文本 vs 复算期望逐项；residual；六章节；核心数字；tables>=11；images>0；checked>=70；重复单位 | 保存后的 docx | status FAIL（不 raise 自身） | render_docx:786、reference 分支 555 |
| 23 | convert_pdf:834 | LibreOffice 转 PDF（win 下多路径探测 soffice）；PDF 文本/页数/孤儿标题/章节页码提取；孤儿标题 keep-with-next 补救；TOC 缓存条目页码回填；≤5 轮重转 | LibreOffice 可执行存在 | 无转换器→FAILED CONVERTER_NOT_FOUND（不 raise）；超时/OSError→FAILED | worker:104 |
| 24 | readable_source:926 | 证据来源可读行 | e dict | 缺省'来源待补' | 附录 771 |
| 25 | compact_working_template:933 | 工作模板手术 v5：前置区解分页/删域、正文首页、同比三要素补绑定（22000 段书签）、map 版本升级 | map 存在 | reader-v5 幂等跳过（939） | normalize_template:260、render_docx:573 |
| 26 | rebuild_report_footer:988 | 页脚整体接管：居中"第 PAGE 页共 NUMPAGES 页"域 | — | — | style_reader:1066 |
| 27 | keep_source_block:1014 | 尾部证据块 ≤12 段 keep 绑定 | 找到标题段 | 无则跳过 | style_reader |
| 28 | expand_soft_breaks:1027 | w:t 内 \n 展开为 w:br | — | — | style_reader |
| 29 | style_reader:1045 | 只管新增内容：题注居中灰字、目录行距、数字-单位防断行、软换行、页脚 | — | — | render:782、reference render:181 |
| 30 | _body_usable_emu:1072 | 正文可用宽（EMU），边距缺省 1 英寸 | sections 非空 | — | 列宽/TOC 制表位 |
| 31 | _fit_table_columns:1078 | 列宽内容加权：数值列不折行、文本列限宽 1800、溢出先 8.5pt 再等比缩；含合并单元格跳过 | 无合并单元格 | 返回 False 跳过 | _beautify_native_tables |
| 32 | _beautify_native_tables:1161 | 全表统一：表头灰底加粗+跨页重复、隔行浅灰、9pt、涨跌列红绿、列宽 | — | — | render:745 |
| 33 | _number_and_caption:1214 | 图"图几-几"/动态表"表几-几"题注+同页绑定；原生表按裁定不加 | 章节可识别（_heading_level） | — | render:746 |
| 34 | _key_conclusion_lines:1277 | 核心结论 5 类条目（总量/要素/根因/对标/行动），缺数据跳过 | snapshot/narrative | 逐条 try 容错 | add_reader_summary |
| 35 | _set_east_asia:1321 | run/样式 eastAsia 字体 | — | — | 样式链 |
| 36 | _ensure_outline_styles:1331 | H1 15/H2 14/H3 12pt + toc1/toc2 样式定义 | — | 样式已存在则改 | add_reader_summary |
| 37 | _heading_level:1360 | 章级/小节级正则识别（要求编号后空格） | — | — | 多处 |
| 38 | _apply_outline_styles:1366 | 标题挂 Heading 样式+run 直排双保险 | — | KeyError 容错 | add_reader_summary |
| 39 | _fix_reading_guide:1382 | 题包原件阅读指南截断章节名补全 | 原件含截断词 | 无则跳过（安装模板安全） | add_reader_summary |
| 40 | _insert_native_toc:1402 | 原生 TOC 域（begin/separate…end 缓存条目，hyperlink→YH_SEC_T* 书签，不标 dirty 防弹窗） | 标题书签已插 | 无条目 return | add_reader_summary:1519 |
| 41 | add_reader_summary:1462 | 封面前增补：报告编号/人工审核状态/核心结论；目录标题清理；标题书签；TOC 插入 | 找得到 '一、封面与基本信息' 与 '目录' | 找不到 return（静默降级） | render:741 |
| 42 | add_reader_charts:1523 | 4 图：趋势折线（纵轴范围诚实+标注值）、三要素饼图、零线双区瀑布、跨厂对比柱 | anchors 含趋势/对标锚；基准非 None 才画瀑布 | 字体缺失回退 sans-serif | render:740 |
| 43 | assess_report:1600 | 八维验收：file_openable/calculation_consistency/evidence_applicability/task_actionability/model_participation 机器判 + 3 人工维 PENDING；overall 无人工评审不可能 PASS | result 结构由 worker 建立 | 无（返回判定） | worker:111、api._recalc_acceptance |

reference_report.py（合成数据上下文，184 行）：
- comparison_basis:11 / benchmark_unit_of:16——对标口径（unit/total）单一来源。
- verify:21——角色绑定验收：按 Heading 1 分节、表格表头精确匹配定位单元格、`actual != [expected]` 单值比对；缺失或重复都 fail；绑定下限由快照结构声明（105-106 expected 公式），非恒真。
- render:115——六章节合同（len(headings)!=6 raise REPORT_SECTION_CONTRACT_REQUIRES_SIX）；paragraph() 内 RESIDUAL 即 raise UNRESOLVED_REPORT_FIELD（防残留进产物）；复用 style_reader 排版合同。
- 注意 render:174 `paragraph(...).paragraph_format.keep_with_next=True`——paragraph() 返回 Paragraph，链式合法。

docx_compat.py（60 行）：validate_word_compat——①[Content_Types].xml 存在 ②xml/rels 良构 ③mc:Ignorable 前缀作用域内已声明（lxml nsmap 继承语义）。违规 raise WORD_COMPAT_CHECK_FAILED。三处出厂点接入：normalize:261、install:111、render:788（convert_pdf 的 TOC 回填保存未接，见 F2）。
- 历史教训实证：07_交付/delivery_20260919_final/demo/report.docx 的 document.xml 实测含 `ns0:` 前缀（旧版 ET 序列化产物）——2026-09-22 事故真实存在，现行代码已修复（序列化全部 LET）。

---

## 2. 占位符覆盖对照表

题包模板原件实测：330 个 w:p、**101 个唯一占位符、108 处出现**；'100%' 段落位于 233（占比合计）与 235（贡献度合计），234={{总环比}}——**normalize 的 i==235 替换命中"贡献度合计"列，选择正确**（已用解包实证，非推测）。compact/install 再补 7 个绑定（去年材料/人工/制造费用成本、材料/人工/制造费用成本同比——注：制造费用同比字段名为"制造费用成本同比"）+ 合计贡献度。同名歧义改名：人工环比→人工环比_金额/_比例、制造费用环比→_金额/_比例（246、97）。

下表"行"= build_bindings 或渲染处；"缺数行为"均为 number(None)→NA 文本（'N/A（无可用基期或明细）'，模板尾部 % 被清理）。

| 模板占位符（组） | 渲染代码位置 | 绑定数值来源 | 缺数行为 |
|---|---|---|---|
| 报告标题/报告类型/分析月份/产品名称/产品规格/编制日期/本月产量 | 367-368 | product+analysis_type 拼接；常量映射；month/period；specification；datetime.now；metrics.quantity(0位) | 规格→'未提供规格'；产量 None→NA |
| 上月/去年/预算×(产量/单位成本/总成本) | 371-374、382-386 | comparison.{mom,yoy,budget}.base；period_values.{period}.{quantity,unit_cost,total_cost} | None→NA；去年同月产量=去年产量别名 |
| ×量环比/同比/预算偏差（产量/单位成本/总成本） | 387-389 | period_changes.{key}.{mom,yoy,budget}.rate（×100 百分数） | None→NA |
| 单位成本环比/同比/预算偏差 | 370 | metrics.{mom,yoy,budget}（快照计算列） | 同上 |
| 本月X成本/上月X成本/X成本环比（材料/人工/制造费用） | 377-378 | elements[key].unit / previous_unit / unit_mom | 同上 |
| 预算X成本/X预算偏差 | 395-396 | elements.budget_unit / budget_rate | 同上 |
| 去年X成本/X成本同比（compact/install 补绑单元格） | 406-407；模板侧 970-977、162-179 | period_values.yoy.elements_unit / elements.comparisons.yoy.unit.rate | 同上 |
| X金额/X占比/X贡献度（2.2 结构表） | 377、393 | elements.unit / share / unit_contribution | share 在 total_cost=0 时 None→NA；贡献度在总变动 0 时 None→NA |
| 单位成本（2.2 合计行）/总环比 | 368、390（379 后被覆盖） | metrics.unit_cost；period_changes.unit_cost.mom.delta（元/盒） | NA |
| 合计贡献度（由模板字面 100% 换来） | 480；模板侧 234-237 | 常量 '100.00'（总变动≠0）/NA | 总变动 0 或无基期→'N/A（总变动为0或无基期）' |
| 原材料成本明细表格 | 656-658 | details.materials × materials_summary（prev/delta/contribution），列结构按模板 md | 明细空→['N/A：无可用明细'…]行 |
| 材料成本归因分析文本 | 411-417 | 程序句+materials_summary 前4条+narrative prose('materials') | 逐字段 NA；prose 可为空串 |
| 人工单位成本/上月人工单位成本 | 379 | elements.labor.unit/previous_unit | NA |
| 人工环比_比例（3.2 表，改名） | 377 | elements.labor.unit_mom | NA |
| 本月/上月×(工时/时薪/效率)、X环比 | 398-399 | labor_metrics.current/mom/rates.{hours_per_10000,hourly_wage,efficiency} | 缺工时数据 metrics:232 全 None→NA |
| 本月/上月×(折旧/动力/间接人工/检验/其他)、X环比、X变动说明 | 400-404 | expenses_summary[name→别名].current/previous/rate；变动说明=固定句或 NA | 名称不匹配别名→跳过→setdefault NA；current None→NA |
| 制造费用合计/上月制造费用合计/制造费用合计环比 | 379 | elements.overhead.unit/previous_unit/unit_mom | NA |
| 近6个月成本趋势表格 | 659-670（动态表） | snapshot.trend（逐行单位成本环比程序算） | 除零→'—' |
| 成本异常排查分析 | 420-444 | alerts+概览+材料价格传导判定+产量分摊方向 | 无材料汇总且产量变动 0/None→setdefault NA（444 条件分支） |
| 原材料价格跟踪表格 | 671-681 | details.market（{N}月价格列），涨幅程序算 | 解析失败→'—' |
| 对标差异表格 | 699-704 | benchmark.summary+elements（left/right/delta/rate/方向） | benchmark 空表头仍出、行空→N/A 行 |
| 差异结构拆解分析 | 447-449 | benchmark.elements contribution + direction | 无记录→'该期间没有可比跨厂记录。' |
| 差异归因分析文本 | 450-455 | prose('benchmark') 回退固定句 + 合成明细边界注 | 固定回退句 |
| 本月亮点 | 456-477 | 确定性规则（环比下降/最大改善要素/行业分位），无则如实说明 | 永不空 |
| 需关注问题 | 478 | **固定文案**（见 F6） | 永不空 |
| 改进建议表格 | 705-728 | narrative findings.suggestion 去重（二元组 Jaccard≥0.6，模型源优先） | 空 findings→'待补'行？否——actionable 空则 rows 空列表→table() 填 N/A 行 |
| 整改任务表格 | 729-737 | 同上 + sha256 任务编号 + RPA 说明 | 同上 |

残留防线（{{}} 会不会留在产物里）：① render:577 对 map 内全部 field setdefault(NA)；② 579 表格类清空待动态插入；③ verify_docx residual 全 XML 部件扫描（826-827）FAIL；④ convert_pdf 对 PDF 文本再扫（875）。三重独立检查，判定：模板内已知占位符不可能残留；用户安装模板的占位符由安装时 entries 全量登记，同被 ①③ 覆盖。

---

## 3. 失败路径核查

| 场景 | 行为 | 结论 |
|---|---|---|
| 模型不可用 | narrative.generate 降级 rules（model_live=False）→ 报告照常渲染 → assess.model_participation=FAIL → overall=FAIL → 任务 DEGRADED（报告可下载但状态明确降级） | 满足 |
| 数据缺失 | metrics change()/contribution() 显式 None+reason → 占位符 NA+清理 '%'；表格 N/A 行 | 满足 |
| 工作模板缺失 | render_docx:572 自动 normalize_template 重建 | 满足 |
| 题包原件也缺失 | next() StopIteration → 任务 FAILED（fail-closed，无产物） | 满足 |
| .docx 打不开防线 | validate_word_compat 三处出厂闸（见 §1.23 注）；历史 ns0: 事故在 2026-09-19 交付物中实证存在、现行代码已修 | 满足 |
| 半成品当正式产物 | render 存 .tmp.docx 验证通过才 replace；convert_pdf staged .tmp.pdf；jobs.artifact_path：FAILED 任务禁下载、哈希不符 raise、非终态仅"草稿预览_未审核"带 X-Artifact-Preview 头（jobs.py:127-138） | 满足 |
| 模板版本漂移 | api._generation_versions 模板哈希 + worker:47 TEMPLATE_VERSION_CHANGED_RESUBMIT；渲染器版本 RENDERER_VERSION 入 soft_items（versions.py:22） | 满足 |
| PDF 转换失败 | convert_pdf 返回 FAILED（不 raise）→ assess.file_openable=FAIL → DEGRADED；docx 仍注册（TOC 未回填版） | 满足 |
| 部分失败残留 | 失败时 .tmp.docx 与 machine_audit.json 可能残留在产物目录（未被晋升/注册，不影响正确性） | INFO |

---

## 4. 问题清单（严重度 P0-P3/INFO；每条含反证）

**F1 [P2] explanation_presence 章节映射不全：模型 findings 带 section='summary'/'actions' 时报告整链硬失败**
reports.py:525-548 只把 3.1/3.2/3.3/5.3 四节文本入桶；narrative.py:1013-1015 的 legacy 路径（模型返回 `{"findings":…}` 而非 `{"explanations":…}`，重试提示词 1075 行"不要findings"证明该形状真实出现过）允许 section ∈ {'summary','actions'}∪element keys 的模型 hypothesis 通过校验（origin='model'）。此类 finding 在 by_section 无桶 → MODEL_EXPLANATION_MISSING_FROM_BODY → verify FAIL → render raise → 任务 FAILED——narrative 层精心设计的"降级"被报告层变成"全灭"，且报因不直观。
反证：compile_task_explanations 主路径 section 来自 required_explanation_sections（narrative.py:134-140，仅 element keys+benchmark），均被 525 覆盖；故仅在模型偏离 instructions 且走 legacy 解析时触发。fail-closed，不产生错误产物，故不定 P1。

**F2 [P3] convert_pdf 的 TOC 回填保存未经 validate_word_compat 复验**
reports.py:919-920 `d.save(path)` 直接改写已验收的 report.docx（页码回填+keep_with_next），未再跑 compat 校验，与 docx_compat.py:10-11"任何 docx 出厂都必须先通过本校验"的合同不一致。
反证：该保存全部经 python-docx（lxml），新增节点均为 OxmlElement 构造，无字符串重序列化，前缀丢失的事故根因不适用；属合同缺口而非已知损坏路径。

**F3 [P3] verify_docx 是自洽校验而非真值校验**
expected 由同一 build_bindings(snapshot,{}) 复算（809、821）——若绑定公式本身口径错（例如把 budget_rate 绑到环比位），渲染与验收双双通过。
反证：数字所有权在 metrics 层同一快照（报告/看板/验收三处同源），口径错误会在 dashboard 对拍与评测场景对照中暴露；且 verify 确能发现保存丢失、替换错位、舍入不一致、残留、重复单位（对保存后文件重新解压比对），不是恒真。

**F4 [P3] normalize_template 硬编码 document.xml 段落号 235**
reports.py:234 `i==235 and text=='100%'` 对题包模板版本脆弱：模板换版段号漂移时静默不替换，"贡献度合计"退回字面 100%——总变动为 0（贡献度无定义）时仍显示 100%，轻微误导。
反证：本次已解包实证 235 即贡献度合计单元格（233/235 两个 '100%'，234 为 {{总环比}}）；双条件（段号+文本）使误替换不可能，仅可能"不替换"。

**F5 [INFO] 占比合计单元格保持字面 '100%'**
total_cost=0 时要素占比 NA 而合计行仍 100%（normalize 只换了贡献度列那个）。极端数据观感不一致。

**F6 [P3→部分满足] 两处模板占位符为固定文案而非分析文本**
'需关注问题'（478）恒为同一段管理提示；3.3 表 'X变动说明'（404）恒为'{费用名}变动需核对费用台账及分摊依据'。赛题 5.1.3 要求"大模型生成的分析文本"融入——这两处未接模型/数据。
反证：这是"不编造"的确定性回退（注释 456-458 同思路），6.1 亮点已做成数据驱动；但 6.2 需关注问题与波动数据完全无关，人工归因评分（0-5）可能扣分。

**F7 [P3] 贡献度口径：单位成本口径 vs 赛题字面"总成本变动额"**
metrics contribution=unit_delta/unit_cost_delta（元/盒口径，metrics.py:140）；赛题 5.2.1 公式为"该要素变动额/总成本变动额"。产量变化时两口径数值不同；报告 2.2 表上下文为元/盒，内部自洽且随表注明。
反证：elements 同时有 total_mom/total_delta（metrics.py:137-139），如需总额口径数据已在快照中；差异仅在产量环比≠0 的月份出现，量级=产量变化率×贡献度。待实测评测评分口径。

**F8 [P3] '成本异常排查分析' 依赖条件分支**
444 行 `if directions:` 才赋值——材料汇总为空且产量变动 None/0 时该占位符落到 NA。4.2 节仍有归因定位表（685-698）与 alert 文本兜底。
反证：materials_summary 由题包数据必有；仅极端缺数据时触发，且 NA 措辞明确。

**F9 [INFO] worker.py:96-98 benchmark 回退分支为死代码**
62-82 行已保证 result['benchmark'] 必被赋值（成功或 UNAVAILABLE），96 行 `if 'benchmark' not in result:` 永假。（属 worker 范围，顺带记录。）

**F10 [INFO] number() 为 ROUND_HALF_EVEN（银行家舍入）**
Decimal.__format__ 默认 half-even；metrics 侧 quantize 同样 half-even——两侧一致，无对内矛盾；与教学语境"四舍五入"在恰半分位（x.xx5）差 1 个末位。模拟数据两位小数下几乎不可见。

**F11 [INFO] 季度报告沿用月度模板时的措辞残留**
词替换覆盖 本月/上月/去年同月/分析月份 四组（589-591）；'4.1 近6个月单位成本趋势' 标题、'编制人 财务部成本会计' 等保持月度措辞。绑定合同不受影响（注释 25 已声明回退策略）。

**F12 [INFO] machine_audit.json 在验证前写入产物目录**
783-784 先写 audit 再保存/验证 docx；验证失败时 audit 残留（未注册、不可下载）。无正确性影响。

**F13 [INFO] verify 的 numeric 判定按"值以数字开头"纳入**
'分析月份'（'2026-03…'）等数字开头文本也进 checked——expected/actual 同源同值，不构成漏洞；仅说明 checked>=70 下限的分母口径宽松（实测模板 108 处出现+7 补绑，正常数据下 checked≈90+，下限有余量）。

---

## 5. 已知修复"仍在"核验（用户关注点）

| 已知修复 | 现状 | 证据行 |
|---|---|---|
| docx 改写用 lxml（防 ns0: 前缀丢失） | 在 | 9（导入与注释）、107/256（LET.tostring）；ET 仅 807/813/830 只读；docx_compat 出厂闸 261/111/788 |
| U+FEFF 注入停用（目录数字"7.26 元"异常符号） | 在 | protect_number_units 314-336 仅 NBSP；layout_text:311 清残留 |
| 图片居中 | 在 | 1544 pic.alignment=CENTER |
| 字号层级（H1 15/H2 14/H3 12） | 在 | _ensure_outline_styles:1348 + run 直排 1377-1380 |
| 水印原样保留、每页显示 | 在 | 注释 250-255、978-985（仅前置区解分节） |
| 占比用饼图、瀑布图零线双区 | 在 | 1553-1559、1566-1586 |
| 表格题注"表几-几"/图"图几-几"、模板原生表不加 | 在 | _number_and_caption:1214-1275 |
| 目录：原生域+缓存条目+页码回填、不标 dirty 防弹窗 | 在 | _insert_native_toc:1402-1459、convert_pdf:901-918、1438-1443 |
| N/A 后悬挂 '%' 清理 | 在 | 593、822（渲染与验收两侧同规则） |
| 数字-单位防断行 | 在 | protect_number_units（NBSP 方案） |

---

## 6. 待实测（本审计静态无法终判）

- W1 MS Word 实际打开渲染：TOC 缓存页码与 Word 自身分页一致性（代码注释称 14/14 报告实测一致，本次未复测）；Word 更新域后 toc1/toc2 样式接管效果。
- W2 评测机 LibreOffice 存在性（CONVERTER_NOT_FOUND 降级路径）与中文字体渲染（fonts.conf 指向 assets/fonts，字体文件已确认在库）。
- W3 评测场景下 F7 贡献度口径与标准答案（若按总成本口径评分，产量变动月将有系统性偏差>1% 阈值的可能）。

## 7. 搜索关键词记录（"未实现"项核查）

- 残留占位符防护：`RESIDUAL`、`residual_placeholders` → 命中 18、326、555+（reference）、826、875、1653；无未防护出厂路径。
- xml.etree 序列化：`ET.tostring|ElementTree` → 仅 docx_compat 注释与 reports.py 导入/只读解析命中；无写路径。
- Word 兼容校验接入点：`validate_word_compat` → normalize:261、install:111、render:788（convert_pdf 保存除外，F2）。
- '需关注问题'数据驱动化：`需关注问题` → 仅 478 一处固定文案（F6）。
- 模板缺失自动重建：`not TEMPLATE.exists()` → render:572、api:175。
