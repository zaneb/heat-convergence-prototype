def validate_delete():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        len(res_ds._store),
        0,
    )


def validate_update():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        res_ds.dump(),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'props_data': {},
             'stack_key': 0,
             'template_key': 1},
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'props_data': {},
             'stack_key': 0,
             'template_key': 1},
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'props_data': {'a': '4alpha'},
             'stack_key': 0,
             'template_key': 1},
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'props_data': {'ca': '4alpha'},
             'stack_key': 0,
             'template_key': 1},
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'props_data': {'c': 'C_phys_id'},
             'stack_key': 0,
             'template_key': 1},
         5: {'key': 5,
             'name': 'F',
             'phys_id': 'F_phys_id',
             'props_data': {},
             'stack_key': 0,
             'template_key': 1}}
    )


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


example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
})
engine.create_stack('basic_update_delete', example_template)
engine.noop(2)
engine.validate(validate_create)

example_template2 = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
    'F': RsrcDef({}, ['D', 'E']),
})
engine.update_stack('basic_update_delete', example_template2)
engine.noop(12)
engine.validate(validate_update)
engine.delete_stack('basic_update_delete')
engine.noop(10)
engine.validate(validate_delete)
