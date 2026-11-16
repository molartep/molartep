import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('profile', Path(__file__).parents[1] / 'scripts/build_profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class ProfileTests(unittest.TestCase):
    def test_pagination(self):
        with patch.object(profile, 'api', side_effect=[[{}] * 100, [{}]]) as api:
            self.assertEqual(len(profile.pages('repos/example/project/commits?author=example')), 101)
        self.assertIn('page=2', api.call_args.args[0])

    def test_stats_deduplicate_commits_and_exclude_forks(self):
        repos = [{'name': 'one', 'fork': False, 'default_branch': 'main'},
                 {'name': 'two', 'fork': False, 'default_branch': 'main'},
                 {'name': 'forked', 'fork': True}]
        with patch.object(profile, 'pages', side_effect=[repos, [{'sha': 'a'}, {'sha': 'b'}], [{'sha': 'b'}, {'sha': 'c'}]]), patch.object(profile, 'count_lines', side_effect=[(100, 20), (30, 5)]) as count:
            stats = profile.fetch_stats()
        self.assertEqual(stats['public_repos'], 3)
        self.assertEqual(stats['commits'], 3)
        self.assertEqual(stats['lines_of_code'], 105)
        self.assertEqual(stats['lines_of_code'], stats['added'] - stats['deleted'])
        self.assertEqual(count.call_args.args[1], {'c'})

    def test_failed_refresh_preserves_last_generated_files(self):
        paths = [profile.ROOT / p for p in ('assets/stats.json', 'dark_mode.svg', 'light_mode.svg')]
        before = [p.read_bytes() for p in paths]
        with patch('sys.argv', ['build_profile.py', '--refresh']), patch.object(profile, 'pages', side_effect=OSError('offline')):
            with self.assertRaises(OSError):
                profile.main()
        self.assertEqual(before, [p.read_bytes() for p in paths])

    def test_both_themes_are_valid_svg_with_ascii_portrait(self):
        import json
        stats = json.loads((profile.ROOT / 'assets/stats.json').read_text())
        portrait = (profile.ROOT / 'assets/portrait.txt').read_text()
        self.assertTrue(portrait.isascii())
        self.assertEqual(len(portrait.splitlines()), 56)
        for theme in ('dark', 'light'):
            svg = ET.fromstring(profile.render(theme, stats))
            self.assertTrue(svg.tag.endswith('svg'))
            self.assertIn('Martin Olarte', ''.join(svg.itertext()))


if __name__ == '__main__':
    unittest.main()
