def validate_create():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'props_data': {'a': 'initial'},
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
             'props_data': {'!a': 'initial'},
             'stack_key': 0,
             'template_key': 0},
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'props_data': {'ca': 'initial'},
             'stack_key': 0,
             'template_key': 0},
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'props_data': {'c': 'C_phys_id'},
             'stack_key': 0,
             'template_key': 0}}
    )


def validate_update_A():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'props_data': {'a': 'updated'},
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
             'props_data': {'!a': 'updated'},
             'stack_key': 0,
             'template_key': 0},
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'props_data': {'ca': 'updated'},
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
             'props_data': {'a': 'updated'},
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
             'props_data': {'!a': 'updated'},
             'stack_key': 0,
             'template_key': 0},
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'props_data': {'ca': 'updated'},
             'stack_key': 0,
             'template_key': 0},
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'props_data': {'c': 'C_phys_id'},
             'stack_key': 0,
             'template_key': 0},
         5: {'key': 5,
             'name': 'F',
             'phys_id': 'F_phys_id',
             'props_data': {},
             'stack_key': 0,
             'template_key': 0}}
    )


example_template = Template({
    'A': RsrcDef({'a': 'initial'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, []),
})
engine.create_stack('foo', example_template)
engine.noop(5)
engine.validate(validate_create)

example_template_shrunk = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, []),
})
engine.update_stack('foo', example_template_shrunk)
engine.noop(11)

example_template_long = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, []),
    'F': RsrcDef({}, ['D', 'E']),
})
engine.update_stack('foo', example_template_long)
engine.noop(12)
engine.validate(validate_update_long)
engine.delete_stack('foo')
