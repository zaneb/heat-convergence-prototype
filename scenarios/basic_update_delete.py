example_template = Template({
    'C': RsrcDef({'a': '4alpha'}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C', 'E']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, ['A']),
})
engine.create_stack('basic_update_delete', example_template)
engine.noop(5)
engine.call(verify, example_template)

example_template2 = Template({
    'C': RsrcDef({'a': '4alpha'}, ['B']),
    'D': RsrcDef({'c': GetRes('C')}, ['C', 'E']),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, ['C']),
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, ['A']),
    'F': RsrcDef({}, ['D', 'E'])
})
engine.update_stack('basic_update_delete', example_template2)
engine.noop(4)
engine.call(verify, example_template2)
engine.delete_stack('basic_update_delete')
engine.noop(6)
engine.call(verify, Template({}))
