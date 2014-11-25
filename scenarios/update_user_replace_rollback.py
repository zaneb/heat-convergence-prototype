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

example_template_updated = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'newC': RsrcDef({'!a': GetAtt('A', 'a')}, ['B']),
    'D': RsrcDef({'c': GetRes('newC')}, []),
    'E': RsrcDef({'ca': GetAtt('newC', '!a')}, []),
})
engine.update_stack('foo', example_template_updated)
engine.noop(3)

engine.rollback_stack('foo')
engine.noop(12)
engine.call(verify, example_template)

engine.delete_stack('foo')
engine.noop(6)
engine.call(verify, Template({}))
