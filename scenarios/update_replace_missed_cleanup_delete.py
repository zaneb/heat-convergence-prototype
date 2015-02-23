def check_resource_count(expected_count):
    test.assertEqual(expected_count, len(reality.all_resources()))

def check_c_count(expected_count):
    test.assertEqual(expected_count,
                     len(reality.resources_by_logical_name('C')))

example_template = Template({
    'A': RsrcDef({'a': 'initial'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, []),
})
engine.create_stack('foo', example_template)
engine.noop(5)
engine.call(verify, example_template)

example_template_shrunk = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, []),
})
engine.update_stack('foo', example_template_shrunk)
engine.noop(7)

engine.delete_stack('foo')
engine.call(check_c_count, 2)
engine.noop(11)
engine.call(verify, Template({}))
