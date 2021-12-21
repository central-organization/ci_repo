class XmlList(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDict(element))
                elif element[0].tag == element[1].tag:
                    self.append(XmlList(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class XmlDict(dict):
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDict(element)
                else:
                    aDict = {element[0].tag: XmlList(element)}
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag: aDict})
            elif element.items():
                self.update({element.tag: dict(element.items())})
            else:
                self.update({element.tag: element.text})
