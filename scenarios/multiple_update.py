
def validate_create():
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


def validate_update_long():
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
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'props_data': {'c': 'C_phys_id'},
             'stack_key': 0,
             'template_key': 0},
         5: {'key': 5,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'props_data': {'ca': '4alpha'},
             'stack_key': 0,
             'template_key': 0},
         6: {'key': 6,
             'name': 'F',
             'phys_id': 'F_phys_id',
             'props_data': {},
             'stack_key': 0,
             'template_key': 0},
         },
    )


def validate_update_shrunk():
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
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'props_data': {'c': 'C_phys_id'},
             'stack_key': 0,
             'template_key': 0}}
    )


example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
})
engine.create_stack('multiple_update', example_template)
engine.validate(validate_create)
engine.noop(5)

example_template_shrunk = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
})
engine.update_stack('multiple_update', example_template_shrunk)
engine.noop(10)
engine.validate(validate_update_shrunk)

example_template_long = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'F': RsrcDef({}, ['D', 'E']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
})
engine.update_stack('multiple_update', example_template_long)
engine.noop(12)
engine.validate(validate_update_long)
