def validate_create():
    res_ds = get_datastore("Resource")
    test.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'properties': {},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             },
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'properties': {},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             },
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'properties': {'a': '4alpha'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'properties': {'ca': '4alpha'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [{'resource': 'C', 'version': 1}],
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'properties': {'c': 'C_phys_id'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             }}
    )


def validate_update():
    res_ds = get_datastore("Resource")
    test.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'properties': {},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             },
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'properties': {},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             },
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'propertiels': {'a': '4alpha'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'properties': {'c': 'C_phys_id'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             }}
    )

example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
})
engine.create_stack('foo', example_template)
engine.converge('foo', 10)
engine.validate(validate_create)

example_template2 = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
})
engine.update_stack('foo', example_template2)
engine.converge('foo', 10)
engine.validate(validate_update)
engine.delete_stack('foo')
