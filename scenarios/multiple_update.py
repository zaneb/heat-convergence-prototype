example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
})
engine.create_stack('multiple_update', example_template)
engine.noop(5)
engine.call(verify, example_template)

example_template_shrunk = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
})
engine.update_stack('multiple_update', example_template_shrunk)
engine.noop(6)
engine.call(verify, example_template_shrunk)

example_template_long = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'a': '4alpha'}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'F': RsrcDef({}, ['D', 'E']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
})
engine.update_stack('multiple_update', example_template_long)
engine.noop(10)
engine.call(verify, example_template_long)
