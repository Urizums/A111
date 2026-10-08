"""Reject invalid real-valued data before geometry, optimization or summaries."""
import math

class InvalidInputError(ValueError):
    def __init__(self, errors):
        self.errors=errors
        super().__init__('; '.join(errors))

class InfeasibleInputError(ValueError):
    pass

def input_errors(instance, config):
    errors=[]
    def number(value, field, positive=False, nonnegative=False, integer=False):
        if isinstance(value,bool) or not isinstance(value,(int,float)):
            errors.append('invalid_numeric:'+field+':expected_JSON_number');return None
        try:
            n=float(value)
        except (OverflowError,ValueError,TypeError):
            errors.append('invalid_numeric:'+field+':not_finite');return None
        if not math.isfinite(n):errors.append('invalid_numeric:'+field+':not_finite');return None
        if (positive and n<=0) or (nonnegative and n<0) or (integer and (n!=math.floor(n) or not isinstance(value,int))):
            errors.append('invalid_range:'+field);return None
        return n
    def dimensions(obj, field):
        dims=obj.get('dims') if isinstance(obj,dict) else None
        if not isinstance(dims,list) or len(dims)!=3:errors.append('invalid_shape:'+field+'.dims');return None
        result=[number(v,field+f'.dims[{i}]',positive=True) for i,v in enumerate(dims)]
        if any(v is None for v in result):return None
        volume=math.prod(result)
        if not math.isfinite(volume) or volume<=0:errors.append('invalid_numeric:'+field+'.volume:nonfinite_or_underflow');return None
        return result
    if not isinstance(instance,dict) or not isinstance(config,dict):return ['invalid_shape:input_or_config:expected_object']
    vs=instance.get('vehicles');gs=instance.get('cargo')
    if not isinstance(vs,list) or len(vs)!=2:errors.append('invalid_shape:vehicles:two_vehicle_types_required');vs=[]
    if not isinstance(gs,list) or not gs:errors.append('invalid_shape:cargo:nonempty_list_required');gs=[]
    for label,objs in [('vehicles',vs),('cargo',gs)]:
        ids=[]
        for i,obj in enumerate(objs):
            f=f'input.{label}[{i}]'
            if not isinstance(obj,dict):errors.append('invalid_shape:'+f);continue
            identity=obj.get('id')
            if not isinstance(identity,str) or not identity:errors.append('invalid_id:'+f)
            else:ids.append(identity)
            d=dimensions(obj,f)
            if label=='vehicles':
                number(obj.get('capacity'),f+'.capacity',positive=True)
                number(obj.get('cost'),f+'.cost',positive=True)
            else:
                m=number(obj.get('mass'),f+'.mass',positive=True);q=number(obj.get('quantity'),f+'.quantity',nonnegative=True,integer=True)
                if obj.get('class') not in ['standard','fragile','oriented']:errors.append('invalid_class:'+f)
                if m is not None and q is not None and not math.isfinite(m*q):errors.append('invalid_numeric:'+f+'.batch_mass:not_finite')
                if d is not None and q is not None and not math.isfinite(math.prod(d)*q):errors.append('invalid_numeric:'+f+'.batch_volume:not_finite')
        if len(ids)!=len(set(ids)):errors.append('duplicate_id:'+label)
    gap=number(config.get('gap_cm'), 'config.gap_cm',nonnegative=True)
    number(config.get('pressure_kg_m2'),'config.pressure_kg_m2',positive=True)
    number(config.get('tolerance_cm',1e-6),'config.tolerance_cm',nonnegative=True)
    for field,default in [('seed',0),('pattern_count_per_vehicle',1),('inventory_restarts',0)]:
        number(config.get(field,default),'config.'+field,positive=field=='pattern_count_per_vehicle',nonnegative=field!='pattern_count_per_vehicle',integer=True)
    number(config.get('master_time_limit_seconds',90),'config.master_time_limit_seconds',positive=True)
    if gap is not None:
        for i,v in enumerate(vs):
            if isinstance(v,dict) and isinstance(v.get('dims'),list) and len(v['dims'])==3:
                try:
                    h=float(v['dims'][2])
                    if math.isfinite(h) and gap>=h:errors.append(f'invalid_range:config.gap_cm:leaves_no_height_in_vehicle[{i}]')
                except (ValueError,TypeError,OverflowError):pass
    if not errors:
        if sum(g['quantity'] for g in gs)<=0:errors.append('invalid_range:cargo:positive_total_inventory_required')
        for key in ['mass','volume']:
            try:
                total=math.fsum(g['mass']*g['quantity'] if key=='mass' else math.prod(g['dims'])*g['quantity'] for g in gs)
                if not math.isfinite(total):errors.append('invalid_numeric:total_'+key+':not_finite')
            except (OverflowError,TypeError,ValueError):errors.append('invalid_numeric:total_'+key+':not_finite')
    return errors

def placement_errors(rows, tolerance):
    errors=[]
    for index,row in enumerate(rows):
        for field in ['x','y','z','l','w','h']:
            name=f'placement[{index}].{field}'
            try:
                value=float(row[field])
            except (KeyError,TypeError,ValueError,OverflowError):errors.append('invalid_numeric:'+name+':not_a_real_number');continue
            if not math.isfinite(value):errors.append('invalid_numeric:'+name+':not_finite');continue
            if (field in ['l','w','h'] and value<=0) or (field in ['x','y','z'] and value < -tolerance):errors.append('invalid_range:'+name)
        try:
            dimensions=[float(row[f]) for f in ['l','w','h']]
            if all(math.isfinite(x) and x>0 for x in dimensions):
                volume=math.prod(dimensions)
                if not math.isfinite(volume) or volume<=0:errors.append(f'invalid_numeric:placement[{index}].volume:nonfinite_or_underflow')
        except (KeyError,TypeError,ValueError,OverflowError):pass
    return errors

def rejection(errors):
    return {'valid':False,'status':'invalid_input','errors':errors,'checks_not_run':['geometry','support','load','metrics'],'trucks':[],'support_loads':[]}
