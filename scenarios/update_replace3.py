def check_resources_exist(*res_names):
    for res_name in res_names:
        test.assertEqual(1, len(reality.resources_by_logical_name(res_name)))

example_template = Template({
    'A': RsrcDef({'a': 'initial'}, []),
    'B': RsrcDef({}, []),
    'C': RsrcDef({'!a': GetAtt('A', 'a')}, ['B', 'A']),
    'D': RsrcDef({'c': GetRes('C')}, ['C']),
    'E': RsrcDef({'ca': GetAtt('C', '!a')}, ['C']),
})
engine.create_stack('update_replace', example_template)
engine.noop(10)
engine.call(verify, example_template)

example_template_replaced = Template({
    'A': RsrcDef({'a': 'updated'}, []),
    'B': RsrcDef({}, []),
    'C2': RsrcDef({'!a': GetAtt('A', 'a')}, ['B', 'A']), # , replacement_of='C'
    'D': RsrcDef({'c': GetRes('C2')}, ['C2']),
    'E': RsrcDef({'ca': GetAtt('C2', '!a')}, ['C2']),
})
engine.update_stack('update_replace', example_template_replaced)

engine.noop(1)
engine.call(check_resources_exist('C', 'C2'))

engine.noop(10)

engine.validate(validate_update)
engine.call(verify, example_template_replaced)
engine.delete_stack('update_replace')
