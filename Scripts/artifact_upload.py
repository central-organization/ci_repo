import argparse
import hashlib
import sys

from requests_wrapper import requests_session


def parse_input_arguments():
    parser = argparse.ArgumentParser(description="Parse diff of integration PR")
    parser.add_argument("--file", help="", required=True)
    parser.add_argument("--artifactory_path", help="", required=True)
    parser.add_argument("--username", help="", required=True)
    parser.add_argument("--password", help="", required=True)
    return parser.parse_args()


def calculate_sha256(filePath):
    hash = hashlib.sha256()
    with open(filePath,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            hash.update(byte_block)
    return hash.hexdigest()


def calculate_sha1(filePath):
    hash = hashlib.sha1()
    with open(filePath,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            hash.update(byte_block)
    return hash.hexdigest()


def upload(configuration):
    sha256 = calculate_sha256(configuration.file)
    sha1 = calculate_sha1(configuration.file)
    uploaded_sha256 =""
    with open(configuration.file,'rb') as f:
        headers={"X-Checksum-Sha256":sha256,"X-Checksum-Sha1":sha1,}
        r= requests_session().put(configuration.artifactory_path,headers=headers, auth=(configuration.username,configuration.password),data=f)

        uploaded_sha256 = r.json()['checksums']['sha256']
        if sha256 != uploaded_sha256:
            sys.exit(1)
        else :
            print("Checksums equal. Code:",r.status_code)


def main(args):
    upload(args)


if __name__ == "__main__":
    configuration = parse_input_arguments()
    main(configuration)
