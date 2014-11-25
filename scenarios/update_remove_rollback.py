b_uuid = None

def store_b_uuid():
    global b_uuid
    b_uuid = next(iter(reality.resources_by_logical_name('B')))

def check_b_not_replaced():
    test.assertEqual(b_uuid,
                     next(iter(reality.resources_by_logical_name('B'))))
    test.assertIsNot(b_uuid, None)

example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
})
engine.create_stack('foo', example_template)
engine.noop(5)
engine.call(verify, example_template)
engine.call(store_b_uuid)

example_template2 = Template({
    'A': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
})
engine.update_stack('foo', example_template2)
engine.noop(2)

engine.rollback_stack('foo')
engine.noop(10)

engine.call(verify, example_template)
engine.call(check_b_not_replaced)
