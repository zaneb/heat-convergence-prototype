def validate_create():
    res_ds = get_datastore("Resource")
    test.assertEqual(
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
             'properties': {'c': 'C_phys_id'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             }}
    )


def validate_update_A():
    res_ds = get_datastore("Resource")
    test.assertEqual(
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
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'properties': {'!a': 'updated'},
             'state': 'COMPLETE',
             'version': 2,
             'prop_refs': [{'resource': 'A', 'version': 2}],
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'properties': {'ca': 'updated'},
             'state': 'COMPLETE',
             'version': 2,
             'prop_refs': [{'resource': 'C', 'version': 2}],
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


def validate_update_long():
    res_ds = get_datastore("Resource")
    test.assertEqual(
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
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'properties': {'!a': 'updated'},
             'state': 'COMPLETE',
             'version': 2,
             'prop_refs': [{'resource': 'A', 'version': 2}],
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'properties': {'ca': 'updated'},
             'state': 'COMPLETE',
             'version': 2,
             'prop_refs': [{'resource': 'C', 'version': 2}],
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'properties': {'c': 'C_phys_id'},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             },
         5: {'key': 5,
             'name': 'F',
             'phys_id': 'F_phys_id',
             'properties': {},
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             }}
    )


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

example_template_shrunk = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B', 'A']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, ['C']),
})
engine.update_stack('update_replace', example_template_shrunk)
engine.converge('update_replace', 10)

example_template_long = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B', 'A']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, ['C']),
    'F': RsrcDef({}, ['D', 'E']),
})
engine.update_stack('update_replace', example_template_long)
engine.converge('update_replace', 10)
engine.validate(validate_update_long)
engine.delete_stack('update_replace')
