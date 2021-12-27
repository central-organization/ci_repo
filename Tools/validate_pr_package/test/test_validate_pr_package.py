import unittest
from unittest.mock import MagicMock, patch
from validate_pr_package import *

class MockResponse():

    def __init__(self, status_code, checksum):
        self.status_code = status_code
        self.headers = {"X-Checksum-Sha256": checksum}


class MockTreeNode():

    def __init__(self, tag, text):
        self.tag = tag
        self.text = text


class MockElementTreeParse():

    def __init__(self, repo_name):
        self.root = [[MockTreeNode('GitHub_repository_name', repo_name),
                        MockTreeNode('Unofficial_Artifactory_repository_path', 'unoff'),
                        MockTreeNode('Official_Artifactory_repository_path', 'off')]]

    def getroot(self):
        return self.root


class MockSubprocessRun():

    def __init__(self, cmd):
        self.returncode = 0
        self.stdout = 'stdout'
        self.stderr = 'stderr'
        self.stdout = self.stdout.encode('utf-8')


class TestValidatePrPackage(unittest.TestCase):

    def test__get_provider_paths__when_master_repo_path_is_invalid__expect_error(self):

        with self.assertRaises(Exception):
            get_provider_paths('invalid', 'invalid')

    @patch('validate_pr_package.XmlDict', return_value = {'Unofficial_Artifactory_repository_path': 'unoff',
                                                                     'Official_Artifactory_repository_path': 'off'})
    @patch('validate_pr_package.ElementTree.parse', return_value = MockElementTreeParse('repo'))
    def test__get_provider_paths__when_both_arguments_are_valid__expect_dictionary_with_paths(self, mock_parse, mock_xmldict):

        actual_value = get_provider_paths('repo', 'random')
        self.assertEqual(actual_value, {'unofficial': 'unoff', 'official': 'off'})


    def test__validate_downloaded_artifact__when_status_code_is_not_200__expect_false(self):

        response = MockResponse(404, 105)
        actual_value = validate_downloaded_artifact(response, 105)
        self.assertFalse(actual_value, 'Test value is false')


    def test__validate_downloaded_artifact__when_status_code_is_200_and_checksum_matches__expect_true(self):

        response = MockResponse(200, 500)
        actual_value = validate_downloaded_artifact(response, 500)
        self.assertTrue(actual_value, 'Test value is true')


    def test__validate_downloaded_artifact__when_status_code_is_200_but_checksum_does_not_match_or_vice_versa__expect_false(self):

        response = MockResponse(200, 500)
        response_2 = MockResponse(201, 500)
        actual_value = validate_downloaded_artifact(response, 501)
        actual_value_2 = validate_downloaded_artifact(response_2, 500)
        self.assertFalse(actual_value, 'Test value is false')
        self.assertFalse(actual_value_2, 'Test value is false')


    def test__execute_git_diff_command__when_subprocess_return_code_is_not_0__expect_none(self):

        with patch('subprocess.run') as subprocess_run_mock:
            subprocess.run = MagicMock()
            subprocess.run.return_value.returncode = 5
            actual_value = execute_git_diff_command('random')
        self.assertIsNone(actual_value, 'Test value is None')


    @patch('validate_pr_package.subprocess.run', return_value = MockSubprocessRun('git command'))
    def test__execute_git_diff_command__when_there_is_diff__expect_diff(self, mock_subprocess_run):

        actual_value = execute_git_diff_command('path')
        self.assertEqual(actual_value, 'stdout')


if __name__ == '__main__':
    unittest.main()