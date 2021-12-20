from xml.etree import cElementTree as ElementTree
from xml_parser import XmlDict, XmlList

def get_provider_paths(repo_name):
    tree = ElementTree.parse('unit_providers.xml')
    root = tree.getroot()
    for child in root:
        for obj in child:
            if obj.tag == 'GitHub_repository_name' and obj.text == repo_name:
                xmldict = XmlDict(child)
                break
    output = {
        'Unofficial_path': xmldict['Unofficial_Artifactory_repository_path'],
        'Official_path': xmldict['Official_Artifactory_repository_path']
    }
    return output

if __name__ == '__main__':
    get_provider_paths('temp')