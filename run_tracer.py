import fnmatch, subprocess, os, json, sys, tempfile, shutil

def find_config(path):
    dir = os.path.dirname(path)
    while dir != '/' and dir != '':
        fn = dir + '/.thinkedit-instant'
        if os.path.exists(fn):
            return fn
        dir = os.path.dirname(dir)

    return None

def get_command_for_path(path):
    config_fn = find_config(os.path.realpath(path))
    if not config_fn:
        return None

    with open(config_fn) as f:
        config_data = json.load(f)

    relpath = os.path.relpath(path, os.path.dirname(config_fn))

    for action in config_data:
        if fnmatch.fnmatchcase(relpath, action['target']):
            return {
                'cwd': os.path.join(os.path.dirname(config_fn), action['cwd']),
                'run': action['run'],
            }

    return None

def sandboxed_cmd(cmd, shared_dir):
    assert cmd[0][0] != '-'
    return ['bwrap', '--die-with-parent', '--unshare-pid', '--unshare-net', '--ro-bind', '/', '/',
            '--tmpfs', '/tmp',
            '--bind', shared_dir, shared_dir,] + cmd

if __name__ == '__main__':
    shared_dir = sys.argv[1]
    path = os.path.realpath(sys.argv[2])
    info = get_command_for_path(path)
    if not info:
        sys.exit('configuration not found for %s' % path)

    output_file = shared_dir + '/trace.json'

    subprocess.call(sandboxed_cmd([
        'python3', 'tracer.py', *info['run']
    ], shared_dir=shared_dir),
                    env=dict(os.environ,
                             TRACER_OUTPUT_FILE=output_file,
                             TRACER_FILE=path,
                             TRACER_TIMEOUT='2',
                             TRACER_CWD=info['cwd']))
