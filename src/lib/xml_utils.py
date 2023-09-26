import xml.etree.ElementTree as ET


def dict_to_xml(d, parent=None):
	if parent is None:
		e = list(d.keys())[0]
		root = ET.Element(e)
		dict_to_xml(d[e], root)
		return ET.tostring(root)
	else:
		for key, value in d.items():
			if isinstance(value, dict):
				element = ET.Element(key)
				parent.append(element)
				dict_to_xml(value, element)
			elif isinstance(value, list):
				for item in value:
					element = ET.Element(key)
					parent.append(element)
					dict_to_xml(item, element)
			elif value is not None:
				element = ET.Element(key)
				element.text = str(value)
				parent.append(element)