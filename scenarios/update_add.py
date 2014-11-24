
def validate_create():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {},
             },
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {},
             },
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {'a': '4alpha'},
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'prop_refs': [{'resource': 'C', 'version': 1}],
             'properties': {'ca': '4alpha'},
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {'c': 'C_phys_id'},
             }
         }
    )


def validate_create_add():
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds.dump()),
        {0: {'key': 0,
             'name': 'A',
             'phys_id': 'A_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {},
             },
         1: {'key': 1,
             'name': 'B',
             'phys_id': 'B_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {},
             },
         2: {'key': 2,
             'name': 'C',
             'phys_id': 'C_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {'a': '4alpha'},
             },
         3: {'key': 3,
             'name': 'E',
             'phys_id': 'E_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'prop_refs': [{'resource': 'C', 'version': 1}],
             'properties': {'ca': '4alpha'},
             },
         4: {'key': 4,
             'name': 'D',
             'phys_id': 'D_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {'c': 'C_phys_id'},
             },
         5: {'key': 5,
             'name': 'F',
             'phys_id': 'F_phys_id',
             'state': 'COMPLETE',
             'version': 1,
             'prop_refs': [],
             'properties': {},
             }
         }
    )


example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
})
engine.create_stack('update_add', example_template)
engine.converge('update_add', 5)
engine.validate(validate_create)

example_template2 = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
    'F': RsrcDef({}, ['D', 'E']),
})
engine.update_stack('update_add', example_template2)
engine.converge('update_add', 6)
engine.validate(validate_create_add)
