import json

class ResourceManager:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.data = self.load_json()

    def load_json(self):
        with open(self.json_file_path, 'r') as json_file:
            return json.load(json_file)

    def get_class_details_from_projectname_classname(self, project_name, class_name):
        filtered_entries = []
        for entry in self.data:
            if entry.get('project_name') == project_name and entry.get('class_name') == class_name:
                return entry
        return filtered_entries
    
    def get_classes_with_contains_test(self, project_name):
        filtered_entries = []
        for entry in self.data:
            if entry.get('project_name') == project_name and entry.get('contains_test'):
                filtered_entries.append(entry)
        return filtered_entries

    def get_entries_without_contains_test(self, project_name):
        filtered_entries = []
        for entry in self.data:
            if entry.get('project_name') == project_name and not entry.get('contains_test'):
                filtered_entries.append(entry)
        return filtered_entries
    
    def get_methods_by_project_and_class(self, project_name, class_name):
        methods = []
        for entry in self.data:
            if entry.get('project_name') == project_name and entry.get('class_name') == class_name:
                methods.extend(entry.get('methods', []))
        return methods
    
    def get_details_by_project_class_and_method(self, project_name, class_name, method_name, onlyEssentials):
        for entry in self.data:
            if (
                entry.get('project_name') == project_name
                and entry.get('class_name') == class_name
            ):
                class_methods = entry.get('methods', [])
                for method in class_methods:
                    if method.get('method_name') == method_name:
                        if onlyEssentials:
                            # get only the essentials
                            details = {
                                "signature": method.get("signature"),
                                "parameters": method.get("parameters"),
                                "dependencies": method.get("dependencies"),
                                "return_type": method.get("return_type"),
                                "developer_comments": method.get("dev_comments"),
                            }
                            return details
                        else:
                            # get all details
                            return method
                
                # If method was not found, it will arrive here
                # print(method_name + Fore.YELLOW + " : NOT FOUND ", Style.RESET_ALL + " in " + class_name)
                # Let's check if the method is available in Super class
                super_class = entry.get('super_class')
                if super_class:
                    # print(method_name + ": SUPER CLASS: ", Fore.YELLOW + super_class, Style.RESET_ALL)
                    return ResourceManager.get_details_by_project_class_and_method(self, project_name, super_class, method_name, onlyEssentials)
                # else:
                #     print(method_name + Fore.YELLOW + ": NO SUPER CLASS FOUND", Style.RESET_ALL)
        return None

    def get_package_by_project_and_class(self, project_name, class_name):
        for entry in self.data:
            if (
                entry.get('project_name') == project_name
                and entry.get('class_name') == class_name
                and 'package' in entry
            ):
                package_declaration = entry['package']
                package_name = package_declaration.split(' ')[1].strip(';')
                return package_name
        return None