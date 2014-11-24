c_uuid = None

def store_c_uuid():
    global c_uuid
    c_uuid = next(iter(reality.resources_by_logical_name('C')))

def check_c_replaced():
    test.assertNotEqual(c_uuid,
                        next(iter(reality.resources_by_logical_name('C'))))
    test.assertIsNot(c_uuid, None)


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
engine.call(store_c_uuid)

example_template_updated = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, []),
})
engine.update_stack('foo', example_template_updated)
engine.noop(11)
engine.call(verify, example_template_updated)

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
engine.call(verify, example_template_long)
engine.call(check_c_replaced)

engine.delete_stack('foo')
engine.noop(6)
engine.call(verify, Template({}))
