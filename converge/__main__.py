try:
    from . import main
except ValueError:
    import sys
    sys.stderr.write('usage: `python -m %s`\n' % sys.path[0])
    sys.exit(1)

if __name__ == '__main__':
    main()
