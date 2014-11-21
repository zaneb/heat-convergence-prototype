def validate_delete():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        len(res_ds._store),
        0,
    )


def validate_update():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'state': 'COMPLETE',
             'properties': {},
             },
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'state': 'COMPLETE',
             'properties': {},
             },
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'state': 'COMPLETE',
             'properties': {'a': '4alpha'},
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'state': 'COMPLETE',
             'properties': {'ca': '4alpha'},
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'state': 'COMPLETE',
             'properties': {'c': 'C_phys_id'},
             },
         5: {'key': 5,
             'name': 'F',
             'phys_id': 'F_phys_id',
             'state': 'COMPLETE',
             'properties': {},
             }
         }
    )


def validate_create():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'state': 'COMPLETE',
             'properties': {},
             },
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'state': 'COMPLETE',
             'properties': {},
             },
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'state': 'COMPLETE',
             'properties': {'a': '4alpha'},
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'state': 'COMPLETE',
             'properties': {'ca': '4alpha'},
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'state': 'COMPLETE',
             'properties': {'c': 'C_phys_id'},
             }
         }
    )


example_template = Template({
    'C': RsrcDef({'a': '4alpha'}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C', 'E']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, ['A']),
})
engine.create_stack('basic_update_delete', example_template)
engine.converge('basic_update_delete', 5)
engine.validate(validate_create)

example_template2 = Template({
    'C': RsrcDef({'a': '4alpha'}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C', 'E']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, ['A']),
    'F': RsrcDef({}, ['D', 'E'])
})
engine.update_stack('basic_update_delete', example_template2)
engine.converge('basic_update_delete', 12)
engine.validate(validate_update)
engine.delete_stack('basic_update_delete')
engine.converge('basic_update_delete', 10)
engine.validate(validate_delete)
