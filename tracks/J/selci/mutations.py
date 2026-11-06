"""Seeded single-AST-operator mutations, independent of all selection outcomes."""
import ast
import copy
from pathlib import Path
import random
import shutil

from .common import sha_file, source_digest


REPLACEMENTS = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.LtE,
                ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
                ast.Add: ast.Sub, ast.Sub: ast.Add}


def candidates(subject):
    found = []
    for path in sorted((Path(subject) / 'src/cachetools').glob('*.py')):
        tree = ast.parse(path.read_text())

        def visit(node, route=(), function=False, in_while=False):
            function = function or isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            in_while = in_while or isinstance(node, ast.While)
            operator = None
            if isinstance(node, ast.Compare) and len(node.ops) == 1:
                operator = node.ops[0]
            elif isinstance(node, ast.BinOp):
                operator = node.op
            if function and not in_while and type(operator) in REPLACEMENTS:
                found.append({'path': str(path.relative_to(subject)),
                              'route': list(route), 'node_type': type(node).__name__,
                              'line': node.lineno, 'column': node.col_offset,
                              'old': type(operator).__name__,
                              'new': REPLACEMENTS[type(operator)].__name__,
                              'original_sha256': sha_file(path)})
            for field, value in ast.iter_fields(node):
                if isinstance(value, ast.AST):
                    visit(value, route + (field,), function, in_while)
                elif isinstance(value, list):
                    for index, child in enumerate(value):
                        if isinstance(child, ast.AST):
                            visit(child, route + (field, index), function, in_while)
        visit(tree)
    return found


def design(subject, count=20, seed=241070005):
    pool = candidates(subject)
    shuffled = pool.copy()
    random.Random(seed).shuffle(shuffled)
    selected, used = [], set()
    for candidate in shuffled:
        key = candidate['path'], candidate['line']
        if key in used:
            continue
        used.add(key)
        selected.append(dict(candidate, id=f'M{len(selected)+1:02}'))
        if len(selected) == count:
            break
    if len(selected) != count:
        raise ValueError('Not enough distinct mutation sites')
    return {'seed': seed, 'candidate_count': len(pool), 'count': count,
            'policy': 'Single comparison-boundary/equality or +/− AST operator inside functions; skip while descendants; distinct source lines; seeded shuffle before any mutation execution. No outcome-based filtering.',
            'source_digest': source_digest(subject), 'mutants': selected}


def mutated_text(source, descriptor):
    tree = ast.parse(source)
    node = tree
    for component in descriptor['route']:
        node = node[component] if isinstance(component, int) else getattr(node, component)
    operator = node.ops[0] if isinstance(node, ast.Compare) else node.op
    if type(operator).__name__ != descriptor['old']:
        raise AssertionError('Mutation target changed')
    replacement = getattr(ast, descriptor['new'])()
    if isinstance(node, ast.Compare):
        node.ops[0] = replacement
    else:
        node.op = replacement
    ast.fix_missing_locations(tree)
    result = ast.unparse(tree) + '\n'
    compile(result, descriptor['path'], 'exec')
    return result


def materialize(subject, destination, descriptor):
    subject, destination = Path(subject), Path(destination)
    shutil.copytree(subject, destination)
    target = destination / descriptor['path']
    if sha_file(target) != descriptor['original_sha256']:
        raise AssertionError('Upstream source changed')
    target.write_text(mutated_text(target.read_text(), descriptor))
    return destination


def classify(process):
    if process['timed_out']:
        return 'timeout'
    return {0: 'survived', 1: 'killed'}.get(process['exit_code'], 'invalid')
