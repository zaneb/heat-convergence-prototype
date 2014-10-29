example_template = Template({
    'A': RsrcDef({}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({}, ['A', 'B']),
    'D': RsrcDef({'c': GetRes('C')}, []),
    'E': RsrcDef({'ca': GetAtt('C', 'a')}, []),
})
engine.create_stack('foo', example_template)
