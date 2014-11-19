def ipdb():
    res_ds = get_datastore("Resource")
    from IPython import embed; embed()

def validate():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'properties': {},
             'stack_key': 0,
             'template_key': 0},
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'properties': {},
             'stack_key': 0,
             'template_key': 0},
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'properties': {'a': '4alpha'},
             'stack_key': 0,
             'template_key': 0},
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'properties': {'ca': '4alpha'},
             'stack_key': 0,
             'template_key': 0},
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'properties': {'c': 'C_phys_id'},
             'stack_key': 0,
             'template_key': 0}}
    )

example_template = Template({
    'C': RsrcDef({'a': '4alpha'}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, ['A']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C', 'D']),
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, ['A']),
})
engine.create_stack('basic_create', example_template)
res_ds = get_datastore("Resource")
engine.converge('basic_create', 2)
engine.validate(ipdb)
engine.converge('basic_create', 5)
engine.validate(ipdb)
engine.validate(validate)
