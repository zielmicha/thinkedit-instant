import json, sys, functools

class Value:
    def __init__(self, line_no, value):
        self.line_no = line_no
        self.value = value
        self.branches = []

    def __repr__(self):
        return '<%s, %s>' % (self.value, self.branches)

def make_tree(values):
    current = Value(-1, None)
    stack = [current]

    for v in values:
        line_no = v[1]

        while line_no < current.line_no:
            current = stack.pop()

        current = Value(line_no, v)
        stack[-1].branches.append(current)
        stack.append(current)

    return stack[0]

branch_limit = 2

class Node:
    def __init__(self, values, branches):
        self.values = values
        self.branches = branches

    def width(self):
        w = 0
        for b in self.branches[:branch_limit]:
            w += b.width()
        w += len(self.branches[:branch_limit]) - 1

        if len(self.branches) > branch_limit:
            w += 1

        return max(w, 30)

    def render(self, render_value):
        result: dict = {}
        width = self.width()

        for value in self.values:
            if value is None: continue

            line_no = value[1]
            if line_no in result:
                result[line_no] += ', '
            else:
                result[line_no] = ''
            result[line_no] += render_value(value)

        for k in result:
            result[k] = ellipsize(result[k], width).ljust(width, ' ')

        branch_line_no: set = set()
        branches_rendered = []

        for b in self.branches[:branch_limit]:
            rendered = b.render(render_value)
            branch_line_no |= rendered.keys()
            branches_rendered.append((b.width(), rendered))

        for line_no in branch_line_no:
            columns = []
            for width, rendered in branches_rendered:
                columns.append(rendered.get(line_no, ' ' * width))

            # TODO
            #assert line_no not in result
            result[line_no] = '│'.join(columns)

            if len(self.branches) > branch_limit:
                result[line_no] += '…'

        return result

    def __repr__(self):
        return '<\n  %s\n  %s>' % (self.values, repr(self.branches).replace('\n', '\n  '))

def flatten(value: Value):
    branches = [ flatten(b) for b in value.branches ]
    if len(branches) == 1:
        return Node([value.value] + branches[0].values, branches[0].branches)
    else:
        return Node([value.value], branches)

def ellipsize(text, length):
    text = text.replace('\n', '⁋')
    if len(text) > length:
        return text[:length-1] + '…'
    else:
        return text

if __name__ == '__main__':
    print(sys.argv)
    v = json.load(open(sys.argv[1]))
    by_method = {}
    for lineno, inner_values in v:
        by_method.setdefault(lineno, []).append(
            flatten(make_tree(inner_values)))

    values = []
    rendered = {}
    for lineno, inner_values in sorted(by_method.items()):
        node = Node([], inner_values)

        rendered.update( node.render(lambda v: '%s=%s' % (v[0], v[2])) )

    original_lines = open(sys.argv[2]).read().splitlines()

    max_line_length = max(map(len, original_lines))

    for i, line in enumerate(original_lines):
        annotation = rendered.get(i+1, '')
        print(line.ljust(max_line_length + 1), '│', annotation[:100])
