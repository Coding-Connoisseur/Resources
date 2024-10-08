import os

def combine_files_in_directory(directory, output_file):
    with open(output_file, 'w') as outfile:
        # Traverse the directory recursively
        for root, dirs, files in os.walk(directory):
            # Ignore directories that start with '__' or are hidden (dot directories)
            dirs[:] = [d for d in dirs if not d.startswith('__') and not d.startswith('.')]
            
            for file in files:
                # Ignore dot files (hidden files)
                if file.startswith('.'):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)

                try:
                    with open(file_path, 'r') as infile:
                        # Write the relative file path as a header
                        outfile.write(f"\n\n--- File: {relative_path} ---\n\n")
                        outfile.write(infile.read())
                        outfile.write("\n")  # Add a newline after file content
                except Exception as e:
                    print(f"Could not read {file_path}: {e}")

if __name__ == "__main__":
    directory = input("Enter the directory to combine files from: ")
    output_file = "Project_Overview.txt"
    combine_files_in_directory(directory, output_file)
    print(f"All files have been combined into {output_file}.")
