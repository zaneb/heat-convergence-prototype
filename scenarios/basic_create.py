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
engine.create_stack('basic_create', example_template)
res_ds = get_datastore("Resource")
engine.converge('basic_create', 2)
engine.converge('basic_create', 5)
engine.validate(validate)
