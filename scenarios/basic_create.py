example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
})
engine.create_stack('foo', example_template)


def validate():
    tpl_ds = get_datastore("Template")
    res_ds = get_datastore("Resource")
    test.testcase.assertEqual(
        dict(res_ds._store[0].__dict__),
        {
            'name': 'A',
            'key': 0,
            'props_data': {},
            'stack_key': 0,
            'template_key': 0,
            'phys_id': 'A_phys_id',
        }
    )
