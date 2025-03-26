import json
import os
import csv
from colorama import Fore, Style, init

def parse_data(project_dir: str, dir_path: str, db_out_path: str, csv_out_path: str):
    """
    Parse the data from .json files and write to both JSON and CSV files.
    :param dir_path: the path of the .json files.
    :param db_out_path: the path of the output JSON file.
    :param csv_out_path: the path of the output CSV file.
    :return: None
    """
    # Create a list to store the extracted class data
    class_data_to_store = []

    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            if filename.endswith('.json'):
                with open(os.path.join(root, filename), "r") as f:
                    json_data = json.load(f)

                for class_data in json_data:
                    # Get class data
                    project_name = class_data['project_name']
                    class_name = class_data['class_name']
                    interfaces = class_data['interfaces']
                    class_path = class_data['class_path']
                    c_sig = class_data['c_sig']

                    method_data_to_store = []

                    if class_data['superclass']:
                        super_class = class_data['superclass'].split(' ')[1]
                    else:
                        super_class = ""

                    if class_data['imports']:
                        imports = "\n".join(class_data['imports'])
                    else:
                        imports = ""

                    if "package" in class_data:
                        package = class_data["package"]
                    else:
                        package = ""

                    has_constructor = class_data['has_constructor']
                    argument_list = class_data['argument_list']
                    contains_test = class_data['contains_test']

                    # Get field data
                    fields = []
                    # for field in class_data['fields']:
                    #     if field['original_string'] not in fields:
                    #         fields.append(field['original_string'])
                    # fields = "\n".join(fields)

                    for field in class_data['fields']:
                        field_string = field['type'] + " " + field['declarator']
                        if field_string not in fields:
                            fields.append(field_string)
                    fields = "\n".join(fields)

                    # Will append from all constructors
                    c_deps = {}

                    # Get method data
                    methods = class_data['methods']
                    focal_method_names = ''
                    
                    for method_data in methods:
                        m_sig = method_data['m_sig']
                        method_name = method_data['method_name']
                        source_code = method_data['source_code']
                        use_field = method_data['use_field']
                        parameters = method_data['parameters']
                        is_test_method = method_data['is_test_method']
                        dev_comments = method_data['documentation']

                        if is_test_method:
                            focal_method_names = method_data['focal_methods']
                        
                        if "public" in method_data['modifiers']:
                            is_public = True
                        else:
                            is_public = False
                        is_constructor = method_data['is_constructor']
                        is_get_set = method_data['is_get_set']
                        m_deps = method_data['m_deps']
                        return_type = method_data['return']

                        # Add dependencies from constructor
                        if is_constructor:
                            for dep_class in m_deps:
                                if dep_class not in c_deps:
                                    c_deps[dep_class] = []
                                c_deps[dep_class].append(m_deps[dep_class])
                        
                        # store method data into json
                        method_entry = {
                            "project_name": project_name,
                            "signature": m_sig,
                            "method_name": method_name,
                            "focal_methods": focal_method_names,
                            "parameters": parameters,
                            "source_code": source_code,
                            "source_code_with_placeholder": "",
                            "class_name": class_name,
                            "dependencies": str(m_deps),
                            "use_field": use_field,
                            "is_constructor": is_constructor,
                            "is_test_method": is_test_method,
                            "is_get_set": is_get_set,
                            "is_public": is_public,
                            "return_type": return_type,
                            "dev_comments": dev_comments,
                        }
                        
                        method_data_to_store.append(method_entry)

                    # store class data into json
                    class_entry = {
                        "project_name": project_name,
                        "class_name": class_name,
                        "class_path": class_path,
                        "signature": c_sig,
                        "super_class": super_class,
                        "interfaces": interfaces,
                        "package": package,
                        "imports": imports,
                        "fields": fields,
                        "argument_list": argument_list,
                        "methods": method_data_to_store,
                        "has_constructor": has_constructor,
                        "contains_test": contains_test,
                        "dependencies": str(c_deps)
                    }
                    
                    class_data_to_store.append(class_entry)

                    print(Fore.GREEN + "PROCESSED    :   ", Style.RESET_ALL + class_name)

    # Check if the file exists
    if os.path.exists(db_out_path):
        # If it exists, delete it
        os.remove(db_out_path)
    
    # Create the directory if it does not exist
    output_dir = os.path.dirname(db_out_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write the list of parsed data to a JSON file
    with open(db_out_path, "w") as json_output:
        json.dump(class_data_to_store, json_output, indent=4)

    export_all_csv = False

    # Write the data to a CSV file
    with open(csv_out_path, "w", newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        if export_all_csv:
            # Write the header
            header = [
                "project_name", "project_dir", "class_name", "class_path", "method_name", "dev_comments"
            ]
            csv_writer.writerow(header)
            
            # Write the data
            for class_entry in class_data_to_store:
                methods = class_entry.get('methods', [])
                
                dev_comment_flag = True
                for method in methods:
                    dev_comments = method.get('dev_comments', '')
                    if len(dev_comments) < 30:
                        dev_comment_flag=False
                        break

                if dev_comment_flag:
                    for method in methods:
                        dev_comments = method.get('dev_comments', '')
                        row = [
                            class_entry['project_name'],
                            project_dir,
                            class_entry['class_name'],
                            class_entry['class_path'],
                            class_entry['signature'],
                            class_entry['super_class'],
                            ', '.join(class_entry['interfaces']),
                            class_entry['package'],
                            class_entry['imports'],
                            class_entry['fields'],
                            class_entry['argument_list'],
                            class_entry['has_constructor'],
                            class_entry['contains_test'],
                            class_entry['dependencies'],
                            method.get('signature', ''),
                            method.get('method_name', ''),
                            method.get('focal_methods', ''),
                            method.get('parameters', ''),
                            method.get('source_code', ''),
                            method.get('source_code_with_placeholder', ''),
                            method.get('use_field', ''),
                            method.get('is_constructor', ''),
                            method.get('is_test_method', ''),
                            method.get('is_get_set', ''),
                            method.get('is_public', ''),
                            method.get('return_type', ''),
                            dev_comments
                        ]
                        csv_writer.writerow(row)
            
        else:
            # Write the header
            header = [
                "project_name", "project_dir", "class_name", "class_path", "method_name", "dev_comments"
            ]
            csv_writer.writerow(header)
            
            # Write the data
            for class_entry in class_data_to_store:
                methods = class_entry.get('methods', [])
                dev_comment_flag = True
                for method in methods:
                    dev_comments = method.get('dev_comments', '')
                    if len(dev_comments) < 30:
                        dev_comment_flag=False
                        break

                if dev_comment_flag:
                    for method in methods:
                        dev_comments = method.get('dev_comments', '')
                        row = [
                            class_entry['project_name'],
                            project_dir,
                            class_entry['class_name'],
                            class_entry['class_path'],
                            method.get('method_name', ''),
                            dev_comments
                        ]
                        csv_writer.writerow(row)        


        

if __name__ == '__main__':
    print("Used from other classes.")