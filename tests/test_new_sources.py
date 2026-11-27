import json
import unittest
from unittest.mock import patch
import collect


class NewSourceTests(unittest.TestCase):
    @patch('collect.get')
    def test_electramod_does_not_execute_and_skips_comments(self, get):
        get.return_value = '''/* {name: "Ignored", code: "bad.js"} */
            export default [{name: "Test", description: "Hello", code: "user/test.js", creator: "user", isGitHub: true}];'''
        result = collect.fetch_electramod()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['url'], 'https://electramod-extensions-gallery.vercel.app/extensions/user/test.js')
        self.assertEqual(result[0]['author_link'], 'https://github.com/user')

    @patch('collect.get')
    def test_gaia_filters_platform_and_hidden(self, get):
        get.return_value = json.dumps([
            {'id': 'valid', 'name': 'Valid', 'canBeUsedOn': {'tw': True}},
            {'id': 'penguin', 'name': 'Penguin', 'canBeUsedOn': {'tw': False}},
            {'id': 'hidden', 'name': 'Hidden', 'hidden': True, 'canBeUsedOn': {'tw': True}},
        ])
        result = collect.fetch_gaia()
        self.assertEqual([r['name'] for r in result], ['Valid'])
        self.assertTrue(result[0]['url'].endswith('/code/valid.js'))

    @patch('collect.get')
    def test_gaia_rejects_invalid_paths(self, get):
        get.return_value = json.dumps([{'id': '../bad', 'name': 'Bad', 'canBeUsedOn': {'tw': True}}])
        with self.assertRaises(ValueError):
            collect.fetch_gaia()


if __name__ == '__main__':
    unittest.main()
