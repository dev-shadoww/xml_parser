import sys
import json

xml_to_json_data = {}


def check_value(value):
    xml_arr = []

    if value.isdigit():
        value = int(value)
    elif "," in value and len(value.split(",")) == value.count(",") + 1:
        for element in value.split(","):
            if element.strip().isdigit():
                xml_arr.append(int(element.strip()))
            else:
                xml_arr.append(element)
        value = xml_arr
    else:
        try:
            value = float(value)
        except ValueError:
            pass
    return value


def get_tag_and_value(line):
    # Because the line starts with b"<?xml ....
    if "\\n\'" in line:
        line = line[2:-3]
    else:
        line = line[2:-1]

    xml_opening_tag = line.split(">")[0].split("<")[1]
    if " " in xml_opening_tag:
        xml_opening_tag = xml_opening_tag.split(" ")[0]

    xml_value = line.split(">")[1].split("<")[0]
    xml_closing_tag = line.split(">")[1].split("<")[-1]

    return [xml_opening_tag, xml_value, xml_closing_tag]


def insert_into_object(xml_object_list, tag_name):
    previous_object = xml_object_list[0]
    temp_object = xml_object_list.pop()
    for key_value in previous_object.keys():
        xml_object_temp_key = key_value
    temp_object[tag_name][xml_object_temp_key] = previous_object[xml_object_temp_key]
    xml_object_list.append(temp_object)
    del xml_object_list[0]


def insert_into_json(xml_object_list, xml_root_tag):
    global xml_to_json_data

    temp_object = xml_object_list.pop()
    for key_value in temp_object.keys():
        xml_object_temp_key = key_value
    xml_to_json_data[xml_root_tag][xml_object_temp_key] = temp_object[xml_object_temp_key]


def xml_to_json_parser(data):
    global xml_to_json_data

    xml_tags_and_values = ""
    xml_object_list = []
    xml_tag_stack = []
    xml_current_object = {}
    xml_root_tag = ""

    xml_multi_comment_found = False
    is_stack_updated = False

    for line in data:
        str_line = str(line)
        if "<?" in str_line:
            continue

        # Check for multi-line comments
        if "<!--" in str_line and "-->" in str_line:
            continue

        if "<!--" in str_line and "-->" not in str_line:
            xml_multi_comment_found = True
            continue

        if "-->" in str_line:
            xml_multi_comment_found = False
            continue

        if "<" in str_line and not xml_multi_comment_found:
            xml_opening_tag, xml_value, xml_closing_tag = get_tag_and_value(
                str_line)

            # Identify Root Tag
            if "/" not in xml_opening_tag and len(xml_closing_tag) == 0 and len(xml_value) == 0:
                xml_tag_stack.append(xml_opening_tag)
                is_stack_updated = True
                if is_stack_updated and len(xml_tag_stack) > 2:
                    # Add a placeholder "{["
                    # To separate tags from different nodes
                    xml_tags_and_values += "{["
                if len(xml_tag_stack) == 1:
                    xml_root_tag = xml_tag_stack[0]
                    xml_to_json_data[xml_root_tag] = {}

            # Identify Children Tags
            if len(xml_closing_tag) > 0 and "/" not in xml_opening_tag:
                is_stack_updated = False
                # Add placeholders "{[" and "____"
                # To separate different nodes and then their names and values
                xml_tags_and_values += f"{xml_opening_tag}____{xml_value}]]"

            # Identify Closing Tags
            if "/" in xml_opening_tag and len(xml_closing_tag) == 0:
                tag = xml_tag_stack.pop()
                xml_current_object[tag] = {}
                for item in xml_tags_and_values.split("{[")[-1].split("]]"):
                    if "____" in item:
                        # Check if the value is of different type
                        value = check_value(item.split("____")[1])
                        xml_current_object[tag][item.split("____")[
                            0]] = value
                xml_object_list.append(xml_current_object)

                if len(xml_object_list) > 1 and len(xml_tag_stack) > 1:
                    insert_into_object(xml_object_list, tag)

                elif len(xml_tag_stack) == 1:
                    if (len(xml_object_list) == 2):
                        insert_into_object(xml_object_list, tag)
                        insert_into_json(xml_object_list, xml_root_tag)
                    else:
                        insert_into_json(xml_object_list, xml_root_tag)

                xml_current_object = {}
                xml_tags_and_values = "{[".join(
                    xml_tags_and_values.split("{[")[:-1])
                continue

    return json.dumps(xml_to_json_data)
