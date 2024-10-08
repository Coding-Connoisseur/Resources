import os

def generate_readme(directory, output_file="../STRUCTURE.md"):
    with open(output_file, 'w') as outfile:
        outfile.write("# Project Directory Structure\n\n")
        outfile.write("This README contains the file structure of the project.\n\n")
        outfile.write("```\n")
        
        for root, dirs, files in os.walk(directory):
            # Ignore directories that start with '__' or are hidden (dot directories)
            dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.')]
            
            # Calculate indentation level based on directory depth
            level = root.replace(directory, '').count(os.sep)
            indent = ' ' * 4 * level
            relative_root = os.path.relpath(root, directory)
            
            if relative_root != '.':
                outfile.write(f"{indent}{os.path.basename(root)}/\n")

            for file in files:
                # Ignore dot files (hidden files)
                if file.startswith('.'):
                    continue
                outfile.write(f"{indent}    {file}\n")

        outfile.write("```\n")

if __name__ == "__main__":
    directory = os.getcwd()  # Set directory to the root directory the script is run from
    generate_readme(directory)
    print("README.md has been created with the directory structure.")
