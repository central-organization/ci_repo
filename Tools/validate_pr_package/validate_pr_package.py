import argparse
import logging
import subprocess
import json

from artifactory import ArtifactoryPath

from xml.etree import cElementTree as ElementTree
from pathlib import Path

import requests
from xml_parser import XmlDict
from requests_wrapper import requests_session


DEFAULT_FILE_ENCODING = "utf-8"
GIT_DIFF_COMMAND = ["/bin/bash", "-c", "git -C {git_repo_path} diff --name-only origin/master"]


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="Parse diff of integration PR")
    parser.add_argument("--github_repo_path", help="", required=True)
    parser.add_argument("--github_repository", help="", required=True)
    parser.add_argument("--artifact_output_path", help="", required=True)
    return parser.parse_args()


def execute_git_diff_command(git_repo_path):
    cmd = GIT_DIFF_COMMAND
    cmd[2] = cmd[2].format(git_repo_path=git_repo_path)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if proc.returncode != 0:
        if proc.stdout:
            print(proc.stdout)
        if proc.stderr:
            print(proc.stderr)
        return None

    stdout = proc.stdout
    git_diff_output = stdout.decode(DEFAULT_FILE_ENCODING, errors="replace")

    return git_diff_output


def get_xml_config_from_diff(github_repo_path):
    git_diff_output = execute_git_diff_command(github_repo_path)
    git_diff_output = git_diff_output.split("\n")
    for i in git_diff_output:
        if i.endswith(".xml"):
            xml_config = i

    return Path(github_repo_path) / xml_config


def validate_downloaded_artifact(checksum, headers):
    if checksum == headers["X-Checksum-Sha256"]:
        return True
    return False


def download_artifact(artifactory_url, output_path, checksum):
    r = requests.get(artifactory_url, auth=('tu_central_org', 'Ide_gas123'))
    status_code = r.status_code / 100
    headers = r.headers

    if validate_downloaded_artifact(checksum, headers):
        with open(output_path, "wb") as file:
            file.write(r.content)
    else:
        logging.error(f"File from URL {artifactory_url} is not downloaded. Checksums are not the same.")

    if status_code != 2:
        logging.error(f"File {artifactory_url} does not exist")
    return status_code


def validate_pr_package(args):
    # artifactory_paths = get_artifactory_paths(args.github_repository)
    artifactory_paths = {
        "official": "https://centralorg.jfrog.io/artifactory/Official_provider_name/",
        "unofficial": "https://centralorg.jfrog.io/artifactory/Unofficial_provider_name/",
    }

    xml_config = get_xml_config_from_diff(args.github_repo_path)
    tree = ElementTree.parse(xml_config)
    root = tree.getroot()
    versions = []
    for child in root:
        xmldict = XmlDict(child)
        versions.append(xmldict)

    latest_version = versions[0]
    artifactory_file_name = latest_version.get("Artifactory_archive", {}).get("File_name")
    artifactory_directory_path = latest_version.get("Artifactory_archive", {}).get("Directory_path")
    artifactory_checksum = latest_version.get("Artifactory_archive", {}).get("Checksum")

    output_path = Path(args.artifact_output_path) / artifactory_file_name

    package_unofficial_path = Path(artifactory_paths["unofficial"]) / artifactory_directory_path / artifactory_file_name
    package_official_path_without_filename = Path(artifactory_paths["official"]) / artifactory_directory_path
    package_official_path = Path(artifactory_paths["official"]) / artifactory_directory_path / artifactory_file_name

    unofficial_path_status_code = download_artifact("https://centralorg.jfrog.io/artifactory/Output_logs/build_logs_commit_timestamp.tar.gz", output_path, artifactory_checksum)
    if unofficial_path_status_code != 2:
        exit(1)

    # xml_file = "C:\Users\mdominovic\Desktop\expltf\supplier\provider_name_repo\Units\Unit-A-versions.xml"

if __name__ == "__main__":
    configuration = parse_input_arguments()
    validate_pr_package(configuration)
