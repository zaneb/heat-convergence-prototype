def validate():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'props_data': None,
             'stack_key': 0,
             'template_key': 0},
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'props_data': {},
             'stack_key': 0,
             'template_key': 0},
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'props_data': {'a': '4alpha'},
             'stack_key': 0,
             'template_key': 0},
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'props_data': {'ca': '4alpha'},
             'stack_key': 0,
             'template_key': 0},
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'props_data': {'c': 'C_phys_id'},
             'stack_key': 0,
             'template_key': 0}}
    )

example_template = Template({
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
})
engine.create_stack('basic_create', example_template)
engine.validate(validate)
