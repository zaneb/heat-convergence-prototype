def check_resource_counts(count_map):
    for name, count in count_map.items():
        test.assertEqual(count,
                         len(list(reality.resources_by_logical_name(name))))


example_template = Template({
    'A': RsrcDef({'!a': 'initial'}, []),
    'B': RsrcDef({'!b': 'first'}, ['A']),
})
engine.create_stack('foo', example_template)
engine.noop(4)
engine.call(verify, example_template)

example_template_inverted = Template({
    'A': RsrcDef({'!a': 'updated'}, ['B']),
    'B': RsrcDef({'!b': 'second'}, []),
})
engine.update_stack('foo', example_template_inverted)
engine.noop(4)
engine.call(check_resource_counts, {'A': 2, 'B': 1})
engine.noop(2)
engine.call(verify, example_template_inverted)
engine.call(check_resource_counts, {'A': 1, 'B': 1})

engine.delete_stack('foo')
engine.noop(3)
engine.call(verify, Template({}))
