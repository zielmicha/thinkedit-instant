import json, sys, functools, collections, argparse

SINGLE_VALUE_LENGTH = 40
MULTIPLE_VALUES_LENGTH = 70

def ellipsize(text, length):
    text = text.replace('\n', '⁋')
    if len(text) > length:
        return text[:length-1] + '…'
    else:
        return text

def dedup(v):
    r: list = []
    added: set = set()
    for i in v:
        if i not in added:
            added.add(i)
            r.append(i)

    return r

def render(data):
    var_by_lineno: collections.defaultdict = collections.defaultdict(lambda: collections.defaultdict(list))
    exc_by_lineno: dict = {}

    for lineno, values in data:
        for ev in values:
            lineno = ev[0]
            if ev[1] == 'v':
                name = ev[2]
                type_ = ev[4]
                value = ev[3]
                var_by_lineno[lineno][name].append((type_, value))
            elif ev[1] == 'exc':
                exc_by_lineno[lineno] = (ev[2], ev[3])

    rendered = {}
    for lineno, v in var_by_lineno.items():
        if lineno in exc_by_lineno:
            exc, exc_type = exc_by_lineno[lineno]
            rendered[lineno] = '! %s: %s' % (exc_type, exc)
            continue

        result = []
        for name, info in v.items():
            types = set( type_ for type_, _ in info )
            values = '┇'.join(dedup([ ellipsize(v, SINGLE_VALUE_LENGTH) for _, v in info ]))
            result.append('%s:%s=%s' % (name, '|'.join(types), ellipsize(values, MULTIPLE_VALUES_LENGTH)))

        header = ''
        if v:
            count = max(map(len, v.values()))
            header += '[%d] ' % count

        rendered[lineno] = header + ' ┃ '.join(result)

    return rendered

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    ns = parser.parse_args()

    data = json.load(open(ns.input))

    rendered = render(data)

    with open(ns.output, 'w') as f:
        f.write(json.dumps(list(rendered.items())))
