example_template = Template({
    'C': RsrcDef({'a': '4alpha'}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C', 'E']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, ['A']),
})
engine.create_stack('basic_create', example_template)
engine.noop(7)
engine.call(verify, example_template)
