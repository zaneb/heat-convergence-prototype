def validate_create():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'properties': {'a': 'initial'},
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
             'properties': {'!a': 'initial'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [{'resource': 'A', 'version': 1}],
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'properties': {'ca': 'initial'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [{'resource': 'C', 'version': 1}],
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'properties': {'c': {'name': 'C', 'phys_id': 'C_phys_id'}},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             }}
    )

def validate_rollback():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'properties': {'a': 'updated'},
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
             'properties': {'!a': 'initial'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [{'resource': 'A', 'version': 1}],
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'properties': {'ca': 'initial'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [{'resource': 'C', 'version': 1}],
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'properties': {'c': {'name': 'C', 'phys_id': 'C_phys_id'}},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             },
         5: {'key': 5,
             'name': 'C2',
             'phys_id': 'C2_phys_id',
             'properties': {'!a': 'initial'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             }}
    )

def validate_update():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'properties': {'a': 'updated'},
             'state': 'COMPLETE',
             'version': 2,
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
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'properties': {'ca': 'updated'},
             'state': 'COMPLETE',
             'version': 2,
             'prop_refs': [{'resource': 'C2', 'version': 1}],
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'properties': {'c': {'name': 'C2', 'phys_id': 'C2_phys_id'}},
             'state': 'COMPLETE',
             'version': 2,
             'prop_refs': [],
             },
         5: {'key': 5,
             'name': 'C2',
             'phys_id': 'C2_phys_id',
             'properties': {'!a': 'updated'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [{'resource': 'A', 'version': 2}],
             },
         }
    )

def ipdb():
    res_ds = get_datastore("Resource")
    from IPython import embed; embed()

example_template = Template({
    'A': RsrcDef({'a': 'initial'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B', 'A']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, ['C']),
})
engine.create_stack('update_replace', example_template)
engine.converge('update_replace', 10)
engine.validate(validate_create)

example_template_replaced = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'C2': RsrcDef({'!a': GetAtt('A', 'a')}, ['B', 'A']), # , replacement_of='C'
    'D': RsrcDef({'c': GetRes('C2')}, ['C2']),
    'E': RsrcDef({'ca': GetAtt('C2', '!a')}, ['C2']),
})
engine.update_stack('update_replace', example_template_replaced)

engine.converge('update_replace', 1)
engine.validate(validate_rollback)

engine.converge('update_replace', 10)

engine.validate(validate_update)
engine.delete_stack('update_replace')
