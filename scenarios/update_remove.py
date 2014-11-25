example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
})
engine.create_stack('foo', example_template)
engine.noop(10)
engine.call(verify, example_template)

example_template2 = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
})
engine.update_stack('foo', example_template2)
engine.noop(10)
engine.call(verify, example_template2)
engine.delete_stack('foo')
