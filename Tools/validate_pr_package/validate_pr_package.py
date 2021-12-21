import argparse
import logging
import subprocess
import sys

from artifactory import ArtifactoryPath

from xml.etree import cElementTree as ElementTree
from pathlib import Path

import requests
from xml_parser import XmlDict


DEFAULT_FILE_ENCODING = "utf-8"
GIT_DIFF_COMMAND = ["/bin/bash", "-c", "git -C {git_repo_path} diff --name-only origin/master"]


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="Parse diff of integration PR")
    parser.add_argument("--github_repo_path", help="", required=True)
    parser.add_argument("--master_repo_path", help="", required=True)
    parser.add_argument("--artifact_output_path", help="", required=True)
    parser.add_argument("--arty_user", help="", required=True)
    parser.add_argument("--arty_pass", help="", required=True)
    return parser.parse_args()


def get_provider_paths(github_repo_path, master_repo_path):
    repo_name = github_repo_path.split("/")[-1]
    tree = ElementTree.parse(Path(master_repo_path) / 'Provider_submodules' / 'unit_providers.xml')
    root = tree.getroot()
    for child in root:
        for obj in child:
            if obj.tag == 'GitHub_repository_name' and obj.text == repo_name:
                xmldict = XmlDict(child)
                break
    output = {
        'unofficial': xmldict['Unofficial_Artifactory_repository_path'],
        'official': xmldict['Official_Artifactory_repository_path']
    }
    return output

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


def get_contents_of(artifactory_url, username, password):
    response = requests.get(artifactory_url, auth=(username, password))
    return response

def validate_downloaded_artifact(response, checksum):
    if response.status_code == 200 and checksum == response.headers["X-Checksum-Sha256"]:
        return True
    return False


def save_artifact(response, output_path):
    try:
        with open(output_path, "wb") as file:
            file.write(response.content)
    except:
        logging.error(f"File could not be saved to: {output_path}")

def validate_pr_package(args):
    artifactory_paths = get_provider_paths(args.github_repo_path, args.master_repo_path)
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

    package_unofficial_path_response = get_contents_of(package_unofficial_path, args.arty_user, args.arty_pass)
    if validate_downloaded_artifact(package_unofficial_path_response, artifactory_checksum):
        save_artifact(package_unofficial_path_response, output_path)
    else:
        logging.error("Checksum is not the same or status code is different than 200")
        return 1

    package_official_path_response = get_contents_of(package_official_path_without_filename)
    if package_official_path_response.status_code != 200:
        logging.error("Path not available on Artifactory")
        return 1
    return 0

if __name__ == "__main__":
    configuration = parse_input_arguments()
    result = validate_pr_package(configuration)
    sys.exit(result)
