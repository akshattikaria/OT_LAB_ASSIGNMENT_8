import ast
import copy
import json
import unittest

from selci.common import ROOT, SUBJECT, sha_file
from selci.mutations import classify, design, mutated_text


class MutationTests(unittest.TestCase):
    def test_seeded_design_and_one_ast_operator_change(self):
        first = design(SUBJECT)
        self.assertEqual(first, design(SUBJECT))
        self.assertEqual(first['count'], 20)
        self.assertEqual(len({(m['path'], m['line']) for m in first['mutants']}), 20)
        for mutant in first['mutants']:
            original = (SUBJECT / mutant['path']).read_text()
            expected = ast.parse(original)
            node = expected
            for component in mutant['route']:
                node = node[component] if isinstance(component, int) else getattr(node, component)
            if isinstance(node, ast.Compare):
                node.ops[0] = getattr(ast, mutant['new'])()
            else:
                node.op = getattr(ast, mutant['new'])()
            actual = ast.parse(mutated_text(original, mutant))
            self.assertEqual(ast.dump(expected), ast.dump(actual))
            self.assertNotEqual(ast.dump(ast.parse(original)), ast.dump(actual))

    def test_exact_official_distribution_files_unchanged(self):
        upstream = json.loads((ROOT / 'UPSTREAM.json').read_text())
        for name, digest in upstream['distribution_files_sha256'].items():
            self.assertEqual(sha_file(SUBJECT / name), digest, name)
        self.assertEqual(sha_file(ROOT / 'inputs/cachetools-7.2.8.tar.gz'), upstream['archive_sha256'])

    def test_timeout_and_invalid_are_not_counted_as_kills(self):
        for code, timeout, expected in [(0, False, 'survived'), (1, False, 'killed'),
                                        (-9, True, 'timeout'), (2, False, 'invalid'),
                                        (5, False, 'invalid')]:
            self.assertEqual(classify({'exit_code': code, 'timed_out': timeout}), expected)
