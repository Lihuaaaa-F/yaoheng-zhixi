"""类型化成本事实与显式注册的本地行业包。

无进程级“当前行业”：每个任务通过 AnalysisContext 绑定不可变输入
（数据快照哈希、策略注册表、模板与知识版本），保证同 ID 任务可复现。
上传配置只能引用已注册的策略名，不能执行代码或 SQL。
No process-wide active industry. A context binds immutable inputs for every job.
Uploaded configuration names trusted strategies; it cannot execute code or SQL.
"""
from __future__ import annotations
from collections import defaultdict
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Literal
import csv
import json
import os
import tempfile
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .config import APP, PACKAGE, RUNTIME

D = Decimal
CORE_VERSION = '1.0'
PACKS = APP / 'industry_packs'
FORMULA_VERSION = 'normalized-cost-2-typed-drivers'
SNAPSHOT_CONTRACT_VERSION = 'analysis-snapshot-2-frozen-template'
ENTERPRISE_REGISTRY = RUNTIME / 'enterprise_registry.json'


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(',', ':')).encode()).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, str_strip_whitespace=True, str_min_length=1)


class AnalysisContext(Contract):
    enterprise_id: str
    dataset_id: str
    industry_id: str
    industry_version: str
    policy_version: str = Field(min_length=1)
    data_snapshot: str
    knowledge_snapshot: str
    template_version: str
    formula_version: str
    enterprise_config_version: str = 'legacy'

    @property
    def context_hash(self):
        return digest(self.model_dump())


class FactScope(Contract):
    fact_id: str = Field(min_length=1)
    enterprise_id: str = Field(min_length=1)
    factory_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    product_version: str = Field(min_length=1)
    period: str = Field(pattern=r'^\d{4}-(0[1-9]|1[0-2])$')
    period_granularity: Literal['monthly'] = 'monthly'
    cost_object: str = Field(min_length=1)
    grain: Literal['product_period', 'work_order', 'batch'] = 'product_period'
    scenario: Literal['actual','budget','standard'] = 'actual'
    policy_version: str = Field(min_length=1)
    scope: Literal['completed','wip','combined'] = 'completed'
    source_row: str = Field(min_length=1)
    source_snapshot: str = Field(min_length=1)
    source_mode: Literal['imported_cost','driver_rebuilt'] = 'imported_cost'


class CostFact(FactScope):
    element_id: str = Field(min_length=1)
    parent_element_id: str | None = None
    level: Literal['detail','summary'] = 'detail'
    amount: Decimal
    currency: str = Field(pattern=r'^[A-Z]{3}$')
    quantity_unit: str = Field(min_length=1)

    @field_validator('amount')
    @classmethod
    def finite(cls, value):
        if not value.is_finite(): raise ValueError('NON_FINITE_NUMBER')
        return value


class QuantityFact(FactScope):
    quantity: Decimal = Field(ge=0)
    unit: str = Field(min_length=1)

    @field_validator('quantity')
    @classmethod
    def finite(cls, value):
        if not value.is_finite(): raise ValueError('NON_FINITE_NUMBER')
        return value


class OptionalFact(FactScope):
    """Extension data, not implicitly added to imported costs."""
    kind: Literal['machine_hours','labor_hours','energy_kwh','purchase_quantity','purchase_price',
                  'bom_input','recipe_input','scrap','rework','coproduct_output']
    value: Decimal = Field(ge=0)
    unit: str = Field(min_length=1)
    operation_id: str | None = None
    input_product_id: str | None = None

    @field_validator('value')
    @classmethod
    def finite(cls, value):
        if not value.is_finite(): raise ValueError('NON_FINITE_NUMBER')
        return value


class NormalizedDataset(Contract):
    costs: tuple[CostFact, ...]
    quantities: tuple[QuantityFact, ...]
    optional: tuple[OptionalFact, ...] = ()


class PackManifest(Contract):
    id: str = Field(pattern=r'^[a-z][a-z0-9_]*$')
    version: str
    name: str
    core_compatibility: str
    manufacturing_mode: Literal['discrete','process','hybrid']
    data_label: str
    capabilities: dict[str, list[str]]
    elements: dict[str, str]
    strategies: tuple[str, ...] = ()
    mapping_entry: str = 'mapping.json'
    knowledge_entry: str = 'knowledge.json'
    template_entry: str = 'template.json'
    evaluation_entry: str = 'evaluation.json'
    enterprise_entry: str = 'enterprise.json'


# Trusted functions are registered by deployment code, never by uploaded JSON.
def _production_key(row):
    return (row.enterprise_id,row.factory_id,row.product_id,row.product_version,
            row.period,row.scenario,row.cost_object,row.grain)


def _optional_ratio(optional, current, *, kind, output_unit, input_units):
    """One additive driver aggregate per production object/operation/kind.

    Known physical conversions are exact rational arithmetic. Unknown units,
    orphan objects and contradictory exports reject instead of yielding a ratio.
    Missing production objects yield a specifically unavailable metric.
    """
    quantity_unit=current['quantity_unit']
    if output_unit=='件':
        if quantity_unit!='件':raise ValueError('STRATEGY_OUTPUT_UNIT_CONFLICT')
        denominator=current['quantity']
    else:
        if quantity_unit not in ('kg','t','吨'):raise ValueError('STRATEGY_OUTPUT_UNIT_CONFLICT')
        denominator=convert_quantity(current['quantity'],quantity_unit,'kg')
    selected=[row for row in optional if row.kind==kind]
    if selected:_check_scope([*current['quantity_rows'],*selected])
    production={_production_key(row) for row in current['quantity_rows']}
    seen={};natural={};values=[];sources=[]
    for row in selected:
        key=_production_key(row)
        if key not in production:raise ValueError('OPTIONAL_OBJECT_NOT_IN_OUTPUT')
        if row.unit not in input_units:raise ValueError('OPTIONAL_UNIT_CONFLICT')
        if row.fact_id in seen:
            if seen[row.fact_id]!=row:raise ValueError('CONFLICTING_OPTIONAL_FACT_ID')
            continue
        natural_key=(key,row.kind,row.operation_id)
        if natural_key in natural:raise ValueError('OPTIONAL_DUPLICATE_OBJECT_OPERATION')
        seen[row.fact_id]=row;natural[natural_key]=row
        multiplier,divisor=input_units[row.unit]
        values.append(row.value*multiplier/divisor);sources.append(row)
    covered={_production_key(row) for row in sources}
    if covered!=production:
        return {'value':None,'numerator':None,'denominator':denominator,
                'reason':'OPTIONAL_OBJECT_COVERAGE_INCOMPLETE：缺少部分产出对象的完整驱动事实','rows':sources}
    numerator=sum(values,D(0))
    return {'value':numerator/denominator if denominator else None,'numerator':numerator,
            'denominator':denominator,'reason':None if denominator else 'ZERO_QUALIFIED_OUTPUT','rows':sources}


def _machine_hours(optional, current):
    return _optional_ratio(optional,current,kind='machine_hours',output_unit='件',
        input_units={'小时':(D(1),D(1)),'h':(D(1),D(1)),'分钟':(D(1),D(60)),
                     'min':(D(1),D(60)),'秒':(D(1),D(3600)),'s':(D(1),D(3600))})


def _energy(optional, current):
    return _optional_ratio(optional,current,kind='energy_kwh',output_unit='kg',
        input_units={'kWh':(D(1),D(1)),'MWh':(D(1000),D(1)),'Wh':(D(1),D(1000))})


STRATEGIES = {'machine_hours_per_piece': (_machine_hours,'小时/件','machine_hours'),
              'energy_per_kg': (_energy,'kWh/kg','energy_kwh')}


def load_pack(pack):
    if isinstance(pack, str):
        if not pack.replace('_','').isalnum(): raise ValueError('UNKNOWN_INDUSTRY_PACK')
        path = PACKS / pack / 'manifest.json'
        if not path.is_file(): raise ValueError('UNKNOWN_INDUSTRY_PACK')
        pack = json.loads(path.read_text())
    result = PackManifest.model_validate(pack)
    if result.core_compatibility != '>=1,<2': raise ValueError('INCOMPATIBLE_CORE_VERSION')
    if any(name not in STRATEGIES for name in result.strategies): raise ValueError('UNREGISTERED_STRATEGY')
    for entry in (result.mapping_entry,result.knowledge_entry,result.template_entry,result.evaluation_entry,result.enterprise_entry):
        if Path(entry).name != entry: raise ValueError('UNSAFE_PACK_ENTRY')
    return result


def list_packs():
    return [load_pack(path.parent.name).model_dump(mode='json') for path in sorted(PACKS.glob('*/manifest.json'))]


class ProductConfig(Contract):
    name: str
    specification: str
    version: str = '1'


class EnterpriseConfig(Contract):
    id: str = Field(pattern=r'^[a-z][a-z0-9_-]*$')
    name: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    quantity_unit: str = Field(min_length=1)
    currency: str = Field(pattern=r'^[A-Z]{3}$')
    products: dict[str, ProductConfig] = Field(min_length=1)
    responsibilities: dict[str,str] = {}
    source_mode: Literal['imported_cost','driver_rebuilt'] = 'imported_cost'
    facts_entry: str = 'facts.json'
    knowledge_entry: str = 'knowledge.json'

    @field_validator('facts_entry','knowledge_entry')
    @classmethod
    def local_file(cls,value):
        if Path(value).name != value or not value.endswith('.json'): raise ValueError('UNSAFE_ENTERPRISE_ENTRY')
        return value


def _load_enterprise_file(path):
    path=Path(path).resolve()
    value=EnterpriseConfig.model_validate(json.loads(path.read_text())).model_dump()
    value['_base_dir']=path.parent
    value['_config_file']=path
    return value


def _registered():
    if not ENTERPRISE_REGISTRY.is_file():return {}
    return json.loads(ENTERPRISE_REGISTRY.read_text())


def _enterprises(pack):
    default=_load_enterprise_file(PACKS / pack.id / pack.enterprise_entry)
    result=[default]
    for key,path in sorted(_registered().items()):
        industry,_,enterprise=key.partition(':')
        if industry != pack.id: continue
        value=_load_enterprise_file(path)
        if value['id'] != enterprise or enterprise==default['id']: raise ValueError('ENTERPRISE_REGISTRATION_CONFLICT')
        result.append(value)
    return result


def _enterprise(pack, company=None):
    entries=_enterprises(pack)
    if company is None:return entries[0]
    for entry in entries:
        if entry['id']==company:return entry
    raise ValueError('UNKNOWN_ENTERPRISE_CONTEXT')


def _read_dataset(pack, enterprise=None):
    enterprise=enterprise or _enterprise(pack)
    raw = json.loads((enterprise['_base_dir'] / enterprise['facts_entry']).read_text())
    dataset=NormalizedDataset.model_validate(raw)
    if any(x.quantity_unit!=enterprise['quantity_unit'] for x in dataset.costs) or any(x.unit!=enterprise['quantity_unit'] for x in dataset.quantities):
        raise ValueError('ENTERPRISE_UNIT_CONFLICT')
    if any(x.currency!=enterprise['currency'] for x in dataset.costs):raise ValueError('ENTERPRISE_CURRENCY_CONFLICT')
    if any(x.enterprise_id!=enterprise['id'] for x in (*dataset.costs,*dataset.quantities,*dataset.optional)):
        raise ValueError('ENTERPRISE_DATA_SCOPE_MISMATCH')
    if any(x.product_id not in enterprise['products'] or x.product_version!=enterprise['products'][x.product_id]['version'] for x in (*dataset.costs,*dataset.quantities,*dataset.optional)):
        raise ValueError('ENTERPRISE_PRODUCT_VERSION_MISMATCH')
    if any(x.policy_version!=enterprise['policy_version'] for x in (*dataset.costs,*dataset.quantities,*dataset.optional)):
        raise ValueError('ENTERPRISE_POLICY_MISMATCH')
    return dataset


def register_enterprise(pack_id, configuration_path):
    """Register a trusted local config; no uploads, imports, eval or networking.

    The caller owns authorization to install local enterprise configuration.
    Registry paths stay in the ignored runtime, outside public package manifests.
    """
    from .locks import exclusive
    pack=load_pack(pack_id)
    enterprise=_load_enterprise_file(configuration_path)
    if enterprise['id']==_enterprise(pack)['id']: raise ValueError('DEFAULT_ENTERPRISE_CANNOT_BE_REPLACED')
    dataset=_read_dataset(pack,enterprise)
    if not dataset.costs or not dataset.quantities:raise ValueError('EMPTY_DATASET')
    for factory,product,scenario in {(x.factory_id,x.product_id,x.scenario) for x in dataset.costs}:
        filtered=NormalizedDataset(costs=tuple(x for x in dataset.costs if (x.factory_id,x.product_id,x.scenario)==(factory,product,scenario)),quantities=tuple(x for x in dataset.quantities if (x.factory_id,x.product_id,x.scenario)==(factory,product,scenario)))
        aggregate(filtered,sorted({x.period for x in filtered.costs}),scenario)
    knowledge=json.loads((enterprise['_base_dir']/enterprise['knowledge_entry']).read_text())
    if not isinstance(knowledge,list) or any(x.get('enterprise_id')!=enterprise['id'] or x.get('industry_id')!=pack.id for x in knowledge):
        raise ValueError('ENTERPRISE_KNOWLEDGE_SCOPE_MISMATCH')
    key=pack.id+':'+enterprise['id']
    ENTERPRISE_REGISTRY.parent.mkdir(parents=True,exist_ok=True)
    with exclusive(ENTERPRISE_REGISTRY.with_suffix('.lock')):
        entries=_registered();path=str(enterprise['_config_file'])
        if key in entries and entries[key]!=path:raise ValueError('ENTERPRISE_REGISTRATION_CONFLICT')
        entries[key]=path
        with tempfile.TemporaryDirectory(dir=ENTERPRISE_REGISTRY.parent,prefix='enterprise-') as temporary:
            candidate=Path(temporary)/'registry.json';candidate.write_text(json.dumps(entries,ensure_ascii=False,sort_keys=True))
            os.replace(candidate,ENTERPRISE_REGISTRY)
    return key


def knowledge_entry_for_context(context):
    context=context.model_dump() if hasattr(context,'model_dump') else context
    pack=load_pack(context['industry_id'])
    enterprise=_enterprise(pack,context['enterprise_id'])
    return enterprise['_base_dir']/enterprise['knowledge_entry']


def resolve_context(context_id=None):
    context_id = context_id or 'pharmaceutical:synthetic-pharma'
    pack_id, _, company = context_id.partition(':')
    pack = load_pack(pack_id)
    enterprise = _enterprise(pack,None if context_id=='pharmaceutical:competition' else company)
    if context_id == 'pharmaceutical:competition':
        from .ingestion import ingest
        snapshot = ingest()['snapshot_id']
    else:
        snapshot = digest(_read_dataset(pack,enterprise).model_dump(mode='json'))
    knowledge_path = enterprise['_base_dir'] / enterprise['knowledge_entry']
    knowledge_snapshot = sha256(knowledge_path.read_bytes()).hexdigest()
    template_version = sha256((PACKS / pack_id / pack.template_entry).read_bytes()).hexdigest()
    dataset_id, policy_version = enterprise['dataset_id'], enterprise['policy_version']
    if context_id == 'pharmaceutical:competition':
        from .knowledge import source_snapshot
        knowledge_snapshot = source_snapshot(PACKAGE / '03_制药知识文档')
        dataset_id, policy_version = 'competition-private', 'pharmaceutical-original-1'
        # Template content participates even before the working copy is created.
        templates = sorted((PACKAGE / '04_报告模板').glob('*.docx'))
        template_version = digest({p.name:sha256(p.read_bytes()).hexdigest() for p in templates})
    return AnalysisContext(enterprise_id=company,dataset_id=dataset_id,industry_id=pack.id,
        industry_version=pack.version,policy_version=policy_version,data_snapshot=snapshot,
        knowledge_snapshot=knowledge_snapshot,template_version=template_version,
        formula_version=FORMULA_VERSION,enterprise_config_version=sha256(enterprise['_config_file'].read_bytes()).hexdigest())


def generation_key(context, actual_input, *, prompt_version='1', model='glm-5.3-flash', provider='openai-compatible',
                   embedding_model='default', retriever_version='hybrid-1', parameters=None):
    return digest([context.model_dump(),actual_input,prompt_version,model,provider,embedding_model,retriever_version,parameters or {}])


class UnitConversion(Contract):
    source_unit: str
    target_unit: str
    factor: Decimal = Field(gt=0, allow_inf_nan=False)
    product_id: str = Field(min_length=1)
    product_version: str = Field(min_length=1)
    evidence_ref: str = Field(min_length=1)


def convert_quantity(value, source, target, *, conversion=None, product_id=None, product_version=None):
    value = D(value)
    if not value.is_finite(): raise ValueError('NON_FINITE_NUMBER')
    if source == target: return value
    physical = {('t','kg'):D(1000),('kg','t'):D('0.001'),('吨','kg'):D(1000),('kg','吨'):D('0.001')}
    if (source,target) in physical: return value * physical[(source,target)]
    if conversion is None: raise ValueError('CONVERSION_EVIDENCE_REQUIRED')
    conversion=UnitConversion.model_validate(conversion)
    if (conversion.source_unit,conversion.target_unit,conversion.product_id,conversion.product_version) != (source,target,product_id,product_version):
        raise ValueError('CONVERSION_SCOPE_MISMATCH')
    return value * conversion.factor


def _check_scope(rows):
    if not rows: raise ValueError('NO_COST_FACTS')
    if any(x.scope != 'completed' for x in rows): raise ValueError('WIP_ALLOCATION_NOT_SUPPORTED')
    for field,error in [('enterprise_id','ENTERPRISE'),('factory_id','FACTORY'),('product_id','PRODUCT'),
            ('product_version','PRODUCT_VERSION'),('policy_version','POLICY'),('source_mode','SOURCE_MODE'),
            ('period_granularity','PERIOD_GRANULARITY'),('grain','GRAIN'),('scope','SCOPE')]:
        if len({getattr(x,field) for x in rows}) != 1: raise ValueError(error+'_CONFLICT')


def aggregate(dataset, months, scenario='actual'):
    costs = [x for x in dataset.costs if x.period in months and x.scenario == scenario]
    quantities = [x for x in dataset.quantities if x.period in months and x.scenario == scenario]
    if {x.period for x in costs} != set(months) or {x.period for x in quantities} != set(months):
        raise ValueError('INCOMPLETE_PERIOD')
    if any(x.scope != 'completed' for x in costs+quantities): raise ValueError('WIP_ALLOCATION_NOT_SUPPORTED')
    _check_scope(costs+quantities)
    if len({x.currency for x in costs}) != 1: raise ValueError('CURRENCY_CONFLICT_NO_FX')
    if len({x.quantity_unit for x in costs} | {x.unit for x in quantities}) != 1: raise ValueError('UNIT_CONFLICT')
    hierarchy_groups=defaultdict(list)
    for x in costs:hierarchy_groups[(x.period,x.scenario,x.cost_object,x.grain)].append(x)
    for group in hierarchy_groups.values():
        by_element=defaultdict(list)
        for x in group:by_element[x.element_id].append(x)
        if any(x.parent_element_id in by_element for x in group):raise ValueError('HIERARCHY_DOUBLE_COUNT')
        for rows in by_element.values():
            if len({x.level for x in rows})>1:raise ValueError('DETAIL_SUMMARY_DOUBLE_COUNT')
            if rows[0].level=='summary' and len({x.fact_id for x in rows})>1:raise ValueError('DUPLICATE_SUMMARY_FACT')
    seen, unique_costs = {}, []
    for x in costs:
        if x.fact_id in seen:
            if seen[x.fact_id] != x: raise ValueError('CONFLICTING_COST_FACT_ID')
            continue
        seen[x.fact_id] = x; unique_costs.append(x)
    # Quantity is a separate relation keyed by production object, never joined to
    # each element. Duplicate exports can repeat it without multiplying output.
    qty = {}
    for x in quantities:
        key=(x.enterprise_id,x.factory_id,x.product_id,x.product_version,x.period,x.scenario,x.cost_object,x.grain)
        if key in qty and (qty[key].quantity,qty[key].unit) != (x.quantity,x.unit):
            raise ValueError('CONFLICTING_QUANTITY')
        qty[key]=x
    cost_objects={(x.period,x.cost_object,x.grain) for x in unique_costs}
    qty_objects={(x.period,x.cost_object,x.grain) for x in qty.values()}
    if cost_objects != qty_objects: raise ValueError('COST_QUANTITY_OBJECT_MISMATCH')
    quantity=sum((x.quantity for x in qty.values()),D(0))
    elements=defaultdict(lambda:D(0))
    for x in unique_costs: elements[x.element_id]+=x.amount
    total=sum(elements.values(),D(0))
    first=costs[0]
    return {'quantity':quantity,'total_cost':total,'unit_cost':total/quantity if quantity else None,
        'elements_total':dict(elements),'elements_unit':{k:v/quantity if quantity else None for k,v in elements.items()},
        'currency':first.currency,'quantity_unit':first.quantity_unit,'enterprise_id':first.enterprise_id,
        'factory_id':first.factory_id,'product_id':first.product_id,'product_version':first.product_version,
        'policy_version':first.policy_version,'scope':first.scope,'source_mode':first.source_mode,
        'grain':first.grain,'period_granularity':first.period_granularity,'scenario':scenario,'months':list(months),'rows':unique_costs,'quantity_rows':list(qty.values())}


class PolicyBridge(Contract):
    enterprise_id: str = Field(min_length=1)
    factory_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    product_version: str = Field(min_length=1)
    periods: tuple[str,...] = Field(min_length=1)
    scenario: Literal['actual','budget','standard']
    source_policy_version: str = Field(min_length=1)
    target_policy_version: str = Field(min_length=1)
    amount_adjustment: Decimal = Field(allow_inf_nan=False)
    evidence_ref: str = Field(min_length=1)


class ComparisonAlignment(Contract):
    unit_conversion: UnitConversion | None = None
    policy_bridge: PolicyBridge | None = None


def _align_base(current, base, alignments):
    aligned=dict(base)
    if alignments is None:return aligned,[]
    # Revalidate even model_copy/model_construct objects supplied by Python callers.
    raw=alignments.model_dump() if hasattr(alignments,'model_dump') else alignments
    alignment=ComparisonAlignment.model_validate(raw)
    evidence=[]
    conversion=alignment.unit_conversion
    if conversion:
        if (conversion.source_unit,conversion.target_unit,conversion.product_id,conversion.product_version) != (base['quantity_unit'],current['quantity_unit'],base['product_id'],base['product_version']):
            raise ValueError('CONVERSION_SCOPE_MISMATCH')
        physical={('t','kg'):D(1000),('kg','t'):D('0.001'),('吨','kg'):D(1000),('kg','吨'):D('0.001')}
        expected=physical.get((conversion.source_unit,conversion.target_unit))
        if expected is not None and conversion.factor != expected:raise ValueError('CONVERSION_FACTOR_CONFLICT')
        aligned['quantity']=base['quantity']*conversion.factor
        aligned['quantity_unit']=current['quantity_unit']
        evidence.append(conversion.evidence_ref)
    bridge=alignment.policy_bridge
    if bridge:
        expected=(base['enterprise_id'],base['factory_id'],base['product_id'],base['product_version'],tuple(base['months']),base['scenario'],base['policy_version'],current['policy_version'])
        actual=(bridge.enterprise_id,bridge.factory_id,bridge.product_id,bridge.product_version,bridge.periods,bridge.scenario,bridge.source_policy_version,bridge.target_policy_version)
        if actual != expected:raise ValueError('POLICY_BRIDGE_SCOPE_MISMATCH')
        aligned['total_cost']=base['total_cost']+bridge.amount_adjustment
        aligned['policy_version']=current['policy_version']
        evidence.append(bridge.evidence_ref)
    aligned['unit_cost']=aligned['total_cost']/aligned['quantity'] if aligned['quantity'] else None
    return aligned,evidence


def compare(current, base, comparison, *, alignments=None):
    if comparison not in ('mom','yoy','budget','standard','factory'): raise ValueError('UNDEFINED_COMPARISON')
    base,alignment_evidence=_align_base(current,base,alignments)
    for field in ('enterprise_id','product_id','product_version','currency','quantity_unit','policy_version','scope','source_mode','grain','period_granularity'):
        if current[field] != base[field]: raise ValueError(field.upper()+'_CONFLICT')
    if comparison!='factory' and current['factory_id']!=base['factory_id']:raise ValueError('FACTORY_CONFLICT')
    if len(current['months']) != len(base['months']): raise ValueError('PERIOD_GRANULARITY_CONFLICT')
    from .metrics import _shift, change
    if comparison in ('mom','yoy'):
        shift = -12 if comparison == 'yoy' else -len(current['months'])
        if [_shift(m,shift) for m in current['months']] != base['months']: raise ValueError('INVALID_COMPARISON_PERIOD')
        if current['scenario'] != base['scenario']: raise ValueError('SCENARIO_CONFLICT')
    if comparison == 'factory' and (current['months'] != base['months'] or current['scenario'] != base['scenario']):
        raise ValueError('INVALID_FACTORY_COMPARISON')
    if comparison in ('budget','standard'):
        if current['months'] != base['months'] or current['scenario'] != 'actual' or base['scenario'] != comparison:
            raise ValueError('INVALID_SCENARIO_COMPARISON')
    return {**change(current['unit_cost'],base['unit_cost']),'alignment_evidence':alignment_evidence}


def publish_snapshot(dataset, destination):
    """Validate a complete candidate before atomically publishing its pointer."""
    if not dataset.costs or not dataset.quantities: raise ValueError('EMPTY_DATASET')
    cohorts=lambda rows:{(x.enterprise_id,x.factory_id,x.product_id,x.scenario) for x in rows}
    if cohorts(dataset.costs)!=cohorts(dataset.quantities): raise ValueError('ORPHAN_QUANTITY_COHORT')
    destination = Path(destination); destination.mkdir(parents=True,exist_ok=True)
    for company,factory,product,scenario in {(x.enterprise_id,x.factory_id,x.product_id,x.scenario) for x in dataset.costs}:
        selected = NormalizedDataset(costs=tuple(x for x in dataset.costs if (x.enterprise_id,x.factory_id,x.product_id,x.scenario)==(company,factory,product,scenario)),quantities=tuple(x for x in dataset.quantities if (x.enterprise_id,x.factory_id,x.product_id,x.scenario)==(company,factory,product,scenario)))
        aggregate(selected,sorted({x.period for x in selected.costs}),scenario)
    body=dataset.model_dump(mode='json'); snapshot=digest(body)
    document={'snapshot_id':snapshot,'dataset':body}
    with tempfile.TemporaryDirectory(prefix='candidate-',dir=destination) as staging:
        path=Path(staging)/'snapshot.json';path.write_text(json.dumps(document,ensure_ascii=False))
        os.replace(path,destination/(snapshot+'.json'))
        pointer=Path(staging)/'current.json';pointer.write_text(json.dumps({'snapshot_id':snapshot}))
        os.replace(pointer,destination/'current.json')
    return {'snapshot_id':snapshot}


def load_snapshot(destination):
    destination=Path(destination)
    snapshot=json.loads((destination/'current.json').read_text())['snapshot_id']
    if len(snapshot)!=64 or any(c not in '0123456789abcdef' for c in snapshot): raise ValueError('INVALID_SNAPSHOT_ID')
    result=json.loads((destination/(snapshot+'.json')).read_text())
    if digest(result['dataset']) != snapshot: raise ValueError('SNAPSHOT_HASH_MISMATCH')
    return result


def import_csv(cost_path, quantity_path, destination):
    """Canonical CSV adapter; field mappings belong to a pack, not the engine."""
    def read(path, model):
        with Path(path).open(encoding='utf-8-sig',newline='') as stream:
            return [model.model_validate({k:v for k,v in row.items() if v != ''}) for row in csv.DictReader(stream)]
    return publish_snapshot(NormalizedDataset(costs=read(cost_path,CostFact),quantities=read(quantity_path,QuantityFact)),destination)


def capabilities(pack, dataset=None, services=None):
    if services is None:
        import importlib.util
        import shutil
        key_path=os.getenv('PHARMA_MODEL_KEY_FILE') or os.getenv('PHARMA_API_KEY_FILE')
        configured=bool(any(os.getenv(k) for k in ('PHARMA_API_KEY','GLM_API_KEY','ZHIPU_API_KEY')) or
                        (key_path and Path(key_path).is_file() and Path(key_path).stat().st_size))
        services={'word_service':importlib.util.find_spec('docx') is not None,
                  'pdf_service':shutil.which('libreoffice') is not None,
                  'model_service':configured,'rpa_service':False}
    present={'costs','quantities'} if dataset and dataset.costs and dataset.quantities else set()
    if dataset: present.update(x.kind for x in dataset.optional)
    result=[]
    for name, requirements in pack.capabilities.items():
        missing=[r for r in requirements if r not in present and not services.get(r,False)]
        result.append({'id':name,'name':{'cost_analysis':'成本分析','word_export':'Word导出','pdf_export':'PDF导出','model_explanation':'大模型解释','simulated_delivery':'模拟送达','machine_hours_per_piece':'单位机时','energy_per_kg':'单位能耗'}.get(name,name),'status':'available' if not missing else 'degraded','missing':missing,
                       'reason':None if not missing else '缺少：'+'、'.join({'word_service':'python-docx依赖','pdf_service':'LibreOffice转换服务','model_service':'应用模型API凭据','rpa_service':'模拟RPA在线验证（连接配置不等于已送达）'}.get(r,r) for r in missing)})
        if name=='model_explanation' and not missing:
            result[-1].update(status='configured',reason='已配置应用凭据；本轮真实模型调用待验证')
    for name,reason in [('wip','缺少在制品计价与完工分配策略'),('coproduct_allocation','缺少联副产品分配政策和产出事实'),('price_quantity_decomposition','缺少实际采购价格及实物耗用量')]:
        result.append({'id':name,'name':{'wip':'在制品计价','coproduct_allocation':'联副产品分配','price_quantity_decomposition':'严格价量分解'}.get(name,name),'status':'unavailable','missing':[reason],'reason':reason})
    return result


def context_catalog():
    contexts=[]
    for raw in list_packs():
        pack=load_pack(raw)
        for enterprise in _enterprises(pack):
            dataset=_read_dataset(pack,enterprise)
            cid=pack.id+':'+enterprise['id']
            contexts.append({'id':cid,'context_id':cid,'industry_id':pack.id,'industry_name':pack.name,
                 'company_id':enterprise['id'],'company_name':enterprise['name'],
                 'capabilities':capabilities(pack,dataset),'data_label':pack.data_label})
    default='pharmaceutical:synthetic-pharma'
    if os.environ.get('PHARMA_DATA_PACKAGE'):
        contexts.append({'id':'pharmaceutical:competition','context_id':'pharmaceutical:competition','industry_id':'pharmaceutical','industry_name':'制药行业包','company_id':'competition','company_name':'赛题私有环境','capabilities':[],'data_label':'私有原题数据，仅本机使用'})
        default='pharmaceutical:competition'
    return {'contexts':contexts,'default_context_id':default}


def catalog(context_id):
    if context_id == 'pharmaceutical:competition':
        from .metrics import catalog as legacy
        return {**legacy(),'context_id':context_id,'quantity_unit':'盒','currency':'CNY'}
    pack=load_pack(context_id.split(':')[0]);enterprise=_enterprise(pack,context_id.partition(':')[2])
    if context_id != pack.id+':'+enterprise['id']: raise ValueError('UNKNOWN_ENTERPRISE_CONTEXT')
    dataset=_read_dataset(pack,enterprise)
    return {'factories':sorted({x.factory_id for x in dataset.costs}), 'products':sorted({x.product_id for x in dataset.costs}),
        'months':sorted({x.period for x in dataset.costs if x.scenario=='actual'}),'context_id':context_id,
        'snapshot_id':digest(dataset.model_dump(mode='json')),'quantity_unit':enterprise['quantity_unit'],
        'currency':enterprise['currency'],'capabilities':capabilities(pack,dataset),'data_label':pack.data_label}


def retrieve_reference(context, query, *, product=None, limit=8):
    """Small pack reference adapter: scope before ranking, never global top-K."""
    from .context_services import retrieve
    return retrieve({'analysis_context':context.model_dump(),'product':product},query,limit=limit)['evidence']


def analyze_reference(context_id, factory=None, product=None, month=None, analysis_type='monthly', basis='unit'):
    from .metrics import _months, _shift, change, contribution, threshold_alert
    if context_id == 'pharmaceutical:competition':
        from .metrics import analyze, catalog as private_catalog
        choices=private_catalog()
        factory=factory or choices['factories'][0]
        product=product or choices['products'][0]
        month=month or choices['months'][-1]
        snapshot=analyze(factory,product,month,analysis_type,basis)
        context=resolve_context(context_id)
        return {**snapshot,'context_id':context_id,'analysis_context':context.model_dump(),'context_hash':context.context_hash}
    context=resolve_context(context_id);pack=load_pack(context.industry_id);enterprise=_enterprise(pack,context.enterprise_id)
    # Read once, verify those exact bytes, then retain an independent JSON copy.
    # Queued reports consume this bound copy rather than the mutable pack file.
    template_bytes=(PACKS / pack.id / pack.template_entry).read_bytes()
    if sha256(template_bytes).hexdigest()!=context.template_version:raise ValueError('TEMPLATE_SNAPSHOT_CHANGED')
    report_template=json.loads(template_bytes)
    if basis not in ('unit','total'): raise ValueError('INVALID_BASIS')
    ds=_read_dataset(pack,enterprise);factory=factory or sorted({x.factory_id for x in ds.costs})[0];product=product or sorted({x.product_id for x in ds.costs})[0]
    month=month or max(x.period for x in ds.costs if x.scenario=='actual')
    ds=NormalizedDataset(costs=tuple(x for x in ds.costs if x.enterprise_id==context.enterprise_id and x.factory_id==factory and x.product_id==product),
        quantities=tuple(x for x in ds.quantities if x.enterprise_id==context.enterprise_id and x.factory_id==factory and x.product_id==product),
        optional=tuple(x for x in ds.optional if x.enterprise_id==context.enterprise_id and x.factory_id==factory and x.product_id==product))
    months=_months(month,analysis_type);current=aggregate(ds,months)
    periods={'mom':[_shift(m,-3 if analysis_type=='quarterly' else -1) for m in months],'yoy':[_shift(m,-12) for m in months],'budget':months}
    bases={}
    for label,period in periods.items():
        try: bases[label]=aggregate(ds,period,'budget' if label=='budget' else 'actual')
        except ValueError as exc:
            if str(exc)!='INCOMPLETE_PERIOD': raise
            bases[label]=None
        if bases[label] is not None:compare(current,bases[label],label)
    scope=context.context_hash+f':{factory}:{product}:{month}:{analysis_type}:{basis}'
    currency=enterprise['currency'];unit=enterprise['quantity_unit'];money='元' if currency=='CNY' else currency
    def metric(key,value,units,formula,den=None,period=None,numerator=None):
        return {'metric_id':scope+':'+key,'value':None if value is None else str(value),'display':'N/A' if value is None else str(D(value).quantize(D('0.01'))),'unit':units,'formula':formula,'formula_version':FORMULA_VERSION,'numerator':None if numerator is None and value is None else str(value if numerator is None else numerator),'denominator':None if den is None else str(den),'comparison_period':period,'row_keys':[x.source_row for x in current['rows']],'source_hash':[context.data_snapshot],'reason':'缺少完整基期或分母为零' if value is None else None}
    metrics={k:metric(k,current[k],u,f,current['quantity'] if k=='unit_cost' else 1,numerator=current['total_cost'] if k=='unit_cost' else current[k]) for k,u,f in [('unit_cost',money+'/'+unit,'Σ金额/Σ独立产量'),('total_cost',money,'Σ成本明细金额'),('quantity',unit,'Σ独立生产对象产量')]}
    selected='unit_cost' if basis=='unit' else 'total_cost'
    comparisons={label:change(current[selected],base[selected] if base else None) for label,base in bases.items()}
    for k,v in comparisons.items(): metrics[k]=metric(k,v['rate'],'%','(本期−基期)/基期×100',v['base'],periods[k],numerator=v['delta'])
    elements=[];alerts=[]
    for key,amount in current['elements_total'].items():
        cu=current['elements_unit'][key]; prior=bases['mom'];changes={b:change(current['elements_'+b][key],prior['elements_'+b].get(key) if prior else None) for b in ('unit','total')}
        flags={b:threshold_alert(c['rate']) for b,c in changes.items()};name=pack.elements.get(key,key)
        item={'key':key,'name':name,'unit':None if cu is None else str(cu),'total':str(amount),'share':str(amount/current['total_cost']*100) if current['total_cost'] else None,
            'alerts':flags,'unit_mom':changes['unit']['rate'],'total_mom':changes['total']['rate'],
            'unit_delta':changes['unit']['delta'],'total_delta':changes['total']['delta'],'delta':changes[basis]['delta'],
            'contribution':contribution(changes[basis]['delta'],comparisons['mom']['delta']),'comparisons':{}}
        for label,base in bases.items():
            item['comparisons'][label]={}
            for b in ('unit','total'):
                c=change(current['elements_'+b][key],base['elements_'+b].get(key) if base else None)
                denom=change(current['unit_cost' if b=='unit' else 'total_cost'],base['unit_cost' if b=='unit' else 'total_cost'] if base else None)['delta']
                item['comparisons'][label][b]={**c,'contribution':contribution(c['delta'],denom),'numerator':c['delta'],'denominator':denom,'comparison_period':periods[label]}
        metrics[key]=metric(key,cu if basis=='unit' else amount,money+'/'+unit if basis=='unit' else money,'Σ要素金额/Σ产量' if basis=='unit' else 'Σ要素金额',current['quantity'] if basis=='unit' else 1,numerator=amount)
        for b,c in changes.items():
            mk=key+'_'+b+'_rate';metrics[mk]=metric(mk,c['rate'],'%','(本期要素−基期要素)/基期要素×100',c['base'],periods['mom'],numerator=c['delta'])
            if flags[b]: alerts.append({'alert_id':'alert-'+digest([scope,key,b])[:20],'element_key':key,'element':name,'basis':b,'current':c['current'],'base':c['base'],'value_unit':money+'/'+unit if b=='unit' else money,'rate':c['rate'],'metric_id':metrics[mk]['metric_id'],'fact_summary':f'{name} {b} 环比 {c["rate"]}%，本期 {c["current"]}，基期 {c["base"]}','rule':'严格超过±10%','note':'合成演示阈值；非行业标准'})
        elements.append(item)
    optional=[x for x in ds.optional if x.period in months and x.scenario=='actual' and x.scope=='completed']
    # WIP/联产口径的驱动事实（工时、能耗）不支持分摊，直接拒绝而非静默计入
    rejected_optional=[x for x in ds.optional if x.period in months and x.scenario=='actual' and x.scope!='completed']
    if rejected_optional: raise ValueError('WIP_ALLOCATION_NOT_SUPPORTED: optional driver facts with scope!=completed')
    for name in pack.strategies:
        fn,u,required=STRATEGIES[name]
        evaluated=fn(optional,current)
        metrics[name]=metric(name,evaluated['value'],u,'Σ'+required+'/Σ合格产出',evaluated['denominator'],numerator=evaluated['numerator'])
        metrics[name]['reason']=evaluated['reason']
        metrics[name]['row_keys']=[row.source_row for row in evaluated['rows']+current['quantity_rows']]

    trend=[]
    for m in sorted({x.period for x in ds.costs if x.scenario=='actual' and _shift(month,-5)<=x.period<=month}):
        a=aggregate(ds,[m]);trend.append({'month':m,**{k:None if a[k] is None else str(a[k]) for k in ('unit_cost','total_cost','quantity')},**{k:None if v is None else str(v) for k,v in a['elements_'+basis].items()}})
    result={'snapshot_contract_version':SNAPSHOT_CONTRACT_VERSION,'report_template':report_template,'context_id':context_id,'analysis_context':context.model_dump(),'context_hash':context.context_hash,'data_version':context.data_snapshot,
        'snapshot_id':'','formula_version':FORMULA_VERSION,'factory':factory,'product':product,'month':month,'analysis_type':analysis_type,'basis':basis,
        'specification':enterprise['products'][product]['specification'],'period':{'start':months[0],'end':months[-1]},'metrics':metrics,'elements':elements,'trend':trend,
        'alerts':alerts,'comparison':comparisons,'details':{'available':False,'reason':'仅合成已归集成本与专用驱动事实；不推算采购/BOM明细','materials':[],'expenses':[],'labor':[],'market':[]},
        'industry':{'rows':[],'converted_unit_cost':metrics['unit_cost']['value'],'unit':money+'/'+unit,'notice':pack.data_label},'budget_bridge':None,
        'period_values':{},'period_changes':{},'materials_summary':[],'expenses_summary':[],'labor_metrics':{},'source_hashes':[context.data_snapshot],
        'quantity_unit':unit,'currency':currency,'data_label':pack.data_label,'capabilities':capabilities(pack,ds),
        'limits':[pack.data_label,'未支持联副产品分配和在制品计价；缺少实际价格/实耗不能严格价量分解','维修记录仅支持待验证假设；不是已证实净原因']}
    for capability in result['capabilities']:
        if capability['id'] in pack.strategies and metrics[capability['id']]['value'] is None:
            capability.update(status='degraded',reason=metrics[capability['id']]['reason'],missing=['complete_validated_driver_facts'])
    result['comparison_scope']={key:current[key] for key in ('enterprise_id','factory_id','product_id','product_version','currency','quantity_unit','policy_version','scope','source_mode','grain','period_granularity','scenario','months')}
    result['specialized_metrics']=[{'key':name,'name':{'machine_hours_per_piece':'单位机时','energy_per_kg':'单位能耗'}.get(name,name),**metrics[name]} for name in pack.strategies]
    result['snapshot_id']=digest(result)
    return result


def benchmark_reference(context_id, product, month, left, right, analysis_type='monthly', basis='unit'):
    """Same-period cross-factory comparison, preserving each side's facts."""
    from .metrics import change, contribution
    if left == right: raise ValueError('DISTINCT_FACTORIES_REQUIRED')
    a=analyze_reference(context_id,left,product,month,analysis_type,basis)
    b=analyze_reference(context_id,right,product,month,analysis_type,basis)
    if a['context_hash'] != b['context_hash']: raise ValueError('CONTEXT_DRIFT')
    if 'comparison_scope' in a and 'comparison_scope' in b:
        def comparable(snapshot):
            return {**snapshot['comparison_scope'],**{key:None if snapshot['metrics'][key]['value'] is None else D(snapshot['metrics'][key]['value']) for key in ('unit_cost','total_cost','quantity')}}
        compare(comparable(a),comparable(b),'factory')
    summary=[]
    for key,name in [('unit_cost','单位成本'),('total_cost','总成本'),('quantity','产量')]:
        x,y=a['metrics'][key],b['metrics'][key]
        summary.append({'key':key,'name':name,'unit':x['unit'],'left':x['value'],'right':y['value'],
                        **{k:v for k,v in change(x['value'],y['value']).items() if k in ('delta','rate','reason')}})
    elements=[];bm={x['key']:x for x in b['elements']}
    for row in a['elements']:
        other=bm.get(row['key'])
        c=change(row['unit'],other['unit'] if other else None)
        elements.append({'key':row['key'],'name':row['name'],'unit':a['metrics']['unit_cost']['unit'],'left':row['unit'],
            'right':other['unit'] if other else None,**{k:v for k,v in c.items() if k in ('delta','rate','reason')},
            'contribution':contribution(c['delta'],summary[0]['delta']),'numerator':c['delta'],'denominator':summary[0]['delta'],
            'comparison_period':a['period'],'comparison_object':left+'−'+right})
    comparison={'analysis_type':analysis_type,'period':a['period'],'direction':left+'−'+right+'，以'+right+'为分母',
        'product':product,'month':month,'left':left,'right':right,'snapshot_ids':[a['snapshot_id'],b['snapshot_id']],
        'summary':summary,'elements':elements,'details':{'left':a['details'],'right':b['details']},
        'hypotheses':[],'limits':['合成演示工厂；只比较同产品、规格、期间与政策的归集结果','缺采购/BOM/批次实耗不推算成本净原因'],
        'context_id':context_id,'analysis_context':a['analysis_context']}
    for row in summary+elements:
        row['metric_refs']={}
        for field in ('delta','rate','contribution'):
            if field not in row: continue
            key='benchmark:'+left+':'+right+':'+row['key']+':'+field
            unit='%' if field in ('rate','contribution') else row['unit']
            row['metric_refs'][field]=key
            a['metrics'][key]={**a['metrics'][row['key']],'metric_id':key,'label':row['name']+'跨厂'+field,'value':row[field],
                'display':'N/A' if row[field] is None else str(D(row[field]).quantize(D('0.01'))),'unit':unit,
                'formula':'左厂−右厂' if field=='delta' else '(左厂−右厂)/右厂×100' if field=='rate' else '要素差额/单位成本总差额×100'}
    a['benchmark_context']={k:comparison[k] for k in ('left','right','direction','summary','elements','limits','period')}
    a['snapshot_id']=digest({k:v for k,v in a.items() if k!='snapshot_id'})
    return a,comparison
