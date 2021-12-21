import argparse
import logging
import requests
import subprocess
import sys

from pathlib import Path
from xml.etree import cElementTree as ElementTree

from xml_parser import XmlDict


DEFAULT_FILE_ENCODING = "utf-8"
GIT_DIFF_COMMAND = ["/bin/bash", "-c", "git -C {git_repo_path} diff --name-only origin/master"]
STORE_TO_WORKFLOW_VAR = "::set-output name={var_name}::{var_value}"

def parse_input_arguments():
    parser = argparse.ArgumentParser(description="Parse diff of integration PR, validate and download files")
    parser.add_argument("--github_repo_path", help="", required=True)
    parser.add_argument("--master_repo_path", help="", required=True)
    parser.add_argument("--artifact_output_path", help="", required=True)
    parser.add_argument("--artifactory_user", help="", required=True)
    parser.add_argument("--artifactory_pass", help="", required=True)
    return parser.parse_args()


def get_provider_paths(github_repo_path, master_repo_path):
    repo_name = github_repo_path.split("/")[-1]
    tree = ElementTree.parse(Path(master_repo_path) / 'Provider_submodules' / 'unit_providers.xml')
    root = tree.getroot()
    xmldict = None
    for child in root:
        for obj in child:
            if obj.tag == 'GitHub_repository_name' and obj.text == repo_name:
                xmldict = XmlDict(child)
                break
    if xmldict:
        output = {
            'unofficial': xmldict['Unofficial_Artifactory_repository_path'],
            'official': xmldict['Official_Artifactory_repository_path']
        }
        return output
    return None

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
    for file_name in git_diff_output:
        if file_name.endswith(".xml"):
            xml_config = file_name

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


def get_latest_provider_configuration(xml_config):
    tree = ElementTree.parse(xml_config)
    root = tree.getroot()
    versions = []
    for child in root:
        xmldict = XmlDict(child)
        versions.append(xmldict)
    return versions[0]


def download_pr_package(package_unofficial_path, artifactory_checksum, arti_user, arti_password, output_path):
    package_unofficial_path_response = get_contents_of(package_unofficial_path, arti_user, arti_password)
    if validate_downloaded_artifact(package_unofficial_path_response, artifactory_checksum):
        save_artifact(package_unofficial_path_response, output_path)
        return True
    else:
        logging.error("Checksum is not the same or status code is different than 200")
        return False


def validate_official_artifactory_location(artifactory_path, arti_user, arti_password):
    package_official_path_response = get_contents_of(artifactory_path, arti_user, arti_password)
    if package_official_path_response.status_code != 200:
        logging.error(f"Path {artifactory_path} not available on Artifactory")
        return False
    return True


def store_value_to_workflow_variable(var_name, var_value):
    logging.info(f"Setting workflow variable: VAR_NAME={var_name} VAR_VALUE={var_value}")
    print(STORE_TO_WORKFLOW_VAR.format(var_name=var_name, var_value=var_value))

def validate_pr_package(args):
    artifactory_paths = get_provider_paths(args.github_repo_path, args.master_repo_path)
    xml_config = get_xml_config_from_diff(args.github_repo_path)
    latest_provider_configuration = get_latest_provider_configuration(xml_config)
    package_file_name = latest_provider_configuration.get("Artifactory_archive", {}).get("File_name")
    package_directory_path = latest_provider_configuration.get("Artifactory_archive", {}).get("Directory_path")
    package_checksum = latest_provider_configuration.get("Artifactory_archive", {}).get("Checksum")

    output_path = Path(args.artifact_output_path) / package_file_name

    if artifactory_paths:
        package_unofficial_path = artifactory_paths["unofficial"] + package_directory_path + r"/" + package_file_name
        package_official_path_without_filename = artifactory_paths["official"] + package_directory_path
        package_official_path = package_official_path_without_filename + r"/" + package_file_name

        if download_pr_package(package_unofficial_path, package_checksum, args.artifactory_user, args.artifactory_pass, output_path):
            logging.info(f"Validated and downloaded: {package_unofficial_path} to location {output_path}")
            store_value_to_workflow_variable("unofficial_package_path", package_unofficial_path)
        else:
            return 1
        logging.info(f"Validated and downloaded: {package_unofficial_path} to location {output_path}")

        if validate_official_artifactory_location(package_official_path_without_filename, args.artifactory_user, args.artifactory_pass):
            logging.info(f"Validated existance of directory: {package_official_path_without_filename}")
            store_value_to_workflow_variable("official_package_path", package_official_path)
            return 0
    logging.error("Artifactory paths not parsed correctly.")
    return 1

if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, "INFO", None),
        format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    configuration = parse_input_arguments()
    result = validate_pr_package(configuration)
    sys.exit(result)
