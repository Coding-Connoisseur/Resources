import os

# Function to parse the Project_Overview.txt file and extract the structure
def parse_project_overview(file_path):
    project_structure = {}
    current_path = []
    
    with open(file_path, 'r') as file:
        for line in file:
            # Skip empty lines
            if line.strip() == "":
                continue
            
            # Detect file header and extract file name correctly
            if line.startswith("--- File: "):
                # Extract and clean file name
                file_name = line.split("--- File: ")[1].strip().strip("-")
                file_parts = file_name.split("/")
                current_path = file_parts[:-1]
                current_file = file_parts[-1]
                
                # Traverse into the path and initialize structure
                current_dir = project_structure
                for folder in current_path:
                    current_dir = current_dir.setdefault(folder, {})
                current_dir[current_file] = ""
            
            # Otherwise, it's content of the current file
            else:
                # Append content to the current file
                current_dir[current_file] += line

    return project_structure

# Function to create directories and files based on the parsed structure
def create_project_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            # Create directory if it's a dictionary
            os.makedirs(path, exist_ok=True)
            create_project_structure(path, content)
        else:
            # Create and write to file if it's not a dictionary
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)

# Main function to process the Project_Overview.txt and create the project
def main(project_overview_path, base_path="./project"):
    # Parse the project structure from Project_Overview.txt
    project_structure = parse_project_overview(project_overview_path)
    
    # Create directories and files according to the parsed structure
    create_project_structure(base_path, project_structure)
    
    print(f"Project structure created at '{base_path}' based on '{project_overview_path}'.")

# Example usage
main("Project_Overview.txt", ".")
