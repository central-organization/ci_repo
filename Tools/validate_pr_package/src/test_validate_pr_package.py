import unittest
from unittest.mock import MagicMock, patch
import sys
sys.path.append('../src')
from validate_pr_package import *

class MockResponse():

    def __init__(self, status_code, checksum):
        self.status_code = status_code
        self.headers = {"X-Checksum-Sha256": checksum}


class MockSubprocessRun():

    def __init__(self, return_code):
        self.return_code = return_code


class TestValidatePrPackage(unittest.TestCase):

    def test__get_provider_paths__when_master_repo_path_is_invalid__expect_error(self):
        with self.assertRaises(Exception):
            get_provider_paths('invalid', 'invalid')

    #@patch('src.validate_pr_package.requests.get', return_value = MagicMock(MockResponse(404, 105)))
    def test__validate_downloaded_artifact__when_status_code_is_not_200__expect_false(self):

        #Arrange
        response = MockResponse(404, 105)

        #Act
        actual_value = validate_downloaded_artifact(response, 105)

        #Assert
        self.assertFalse(actual_value, 'Test value is false')

    def test__validate_downloaded_artifact__when_status_code_is_200_and_checksum_matches__expect_true(self):

        #Arrange
        response = MockResponse(200, 500)

        #Act
        actual_value = validate_downloaded_artifact(response, 500)

        #Assert
        self.assertTrue(actual_value, 'Test value is true')

    def test__validate_downloaded_artifact__when_status_code_is_200_but_checksum_does_not_match_or_vice_versa__expect_false(self):

        #Arrange
        response = MockResponse(200, 500)
        response_2 = MockResponse(201, 500)

        #Act
        actual_value = validate_downloaded_artifact(response, 501)
        actual_value_2 = validate_downloaded_artifact(response_2, 500)

        #Assert
        self.assertFalse(actual_value, 'Test value is false')
        self.assertFalse(actual_value_2, 'Test value is false')

    def test__execute_git_diff_command__when_subprocess_return_code_is_not_0__expect_none(self):

        #Arrange
        with patch('subprocess.run') as subprocess_run_mock:
            subprocess.run = MagicMock()
            subprocess.run.return_value.returncode = 5

        #Act
            actual_value = execute_git_diff_command('random')

        #Assert
        self.assertIsNone(actual_value, 'Test value is None')

    """def test__execute_git_diff_command__when_there_is_diff__expect_none(self):

        #Arrange
        with patch("subprocess.run") as subproc_run_mock:
            subprocess.run = MagicMock()
            subprocess.run.return_value.returncode = 0
    """


if __name__ == '__main__':
    unittest.main()