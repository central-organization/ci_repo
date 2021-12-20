import argparse
import subprocess
import re


DEFAULT_FILE_ENCODING = "utf-8"
GIT_DIFF_COMMAND = ["/bin/bash", "-c", "git -C {git_repo_path} diff {pr_base_sha} {pr_head_sha}"]
PARSE_DIFF_RE = '\+\s*<Artifactory_archive>\n\+\s*<File_name>(.*)<\/File_name>\n\+\s*<Directory_path>(.*)<\/Directory_path>\n\+\s*<Checksum>(.*)<\/Checksum>'

def parse_input_arguments():
    parser = argparse.ArgumentParser(description="Parse diff of integration PR")
    parser.add_argument("--git_repo_path", help="", required=True)
    parser.add_argument("--pr_base_sha", help="", required=True)
    parser.add_argument("--pr_head_sha", help="", required=True)
    return parser.parse_args()

def execute_git_diff_command(git_repo_path, pr_base_sha, pr_head_sha):
    cmd = GIT_DIFF_COMMAND
    cmd[2] = cmd[2].format(git_repo_path=git_repo_path, pr_base_sha=pr_base_sha, pr_head_sha=pr_head_sha)
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

def main(args):
    git_diff_output = execute_git_diff_command(args.git_repo_path, args.pr_base_sha, args.pr_head_sha)
    print(git_diff_output)

    # TODO: parse git_diff_output and validate url

def parse_git_diff():
    with open('diff_master.txt', 'r') as file:
        data = file.read()
    match = re.search(PARSE_DIFF_RE, data)
    if match is not None:
        print(match.group(1))

if __name__ == "__main__":
    configuration = parse_input_arguments()
    main(configuration)
