from collections import defaultdict
import sys, ast, runpy, pickle, traceback, json, os, os.path, functools, resource, signal, random

trace_vars = {}
trace_result = []
traced_filename = None

@functools.lru_cache(maxsize=10000)
def realpath(path):
    return os.path.realpath(path)

class LineTracer:
    def __init__(self, first_lineno):
        self.first_lineno = first_lineno
        self.last_line = first_lineno
        self.result = []

    def __call__(self, frame, event, arg):
        lineno = frame.f_lineno
        if self.last_line != lineno or event in ('return', 'exception'):
            for name in trace_vars.get(self.last_line, []):
                if name in frame.f_locals:
                    value = frame.f_locals[name]
                    repr_value = repr(value)
                    repr_type = type(value).__name__
                    self.result.append((self.last_line, "v", name, repr_value, repr_type))

            if event == 'exception':
                exc = arg[1]
                if not isinstance(exc, (GeneratorExit, StopIteration)):
                    self.result.append((lineno, "exc", str(exc), type(exc).__name__))

            if event == 'return':
                repr_value = repr(arg)
                repr_type = type(arg).__name__
                self.result.append((lineno, "v", "return", repr_value, repr_type))

            self.last_line = lineno

    def to_json(self):
        return [self.first_lineno, self.result]

def tracer(frame, event, arg):
    code = frame.f_code
    if realpath(code.co_filename) != traced_filename: return

    tracer = LineTracer(frame.f_lineno)
    trace_result.append(tracer)

    return tracer

def find_declared_variables(root_node):
    vars: defaultdict = defaultdict(set)
    for node in ast.walk(root_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            vars[node.lineno].add(node.id)

    return vars

def setup_tracer(traced_filename_):
    global trace_vars, traced_filename

    traced_filename = traced_filename_
    with open(traced_filename) as f: text = f.read()
    node = ast.parse(text)
    trace_vars = find_declared_variables(node)

    sys.settrace(tracer)

def alrm_handler(*_):
    raise KeyboardInterrupt('execution timed out')

if __name__ == '__main__':
    os.chdir(os.environ['TRACER_CWD'])
    random.seed(42)

    mem_limit = 3 * 1024 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))

    signal.signal(signal.SIGALRM, alrm_handler)
    signal.alarm(int(os.environ['TRACER_TIMEOUT']))

    output_file = os.environ['TRACER_OUTPUT_FILE']
    target = realpath(os.environ['TRACER_FILE'])
    setup_tracer(target)
    del sys.argv[0:1]
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except:
        traceback.print_exc()
    finally:
        sys.settrace(None)

    with open(output_file, 'w') as f:
        json.dump([ t.to_json() for t in trace_result ], f)
