import re

def remove_parentheses_text(input_string):
    """
    Removes all text between parentheses, including the parentheses, from the input string.

    :param input_string: str, the input string
    :return: str, the modified string with text between parentheses removed
    """
    # Use regex to find and remove text between parentheses (including the parentheses themselves)
    modified_string = re.sub(r'\([^)]*\)', '', input_string)
    return modified_string

def update_file(file_path):
    """
    Reads a file, removes all text between parentheses from its content, and updates the file.

    :param file_path: str, the path to the file to update
    """
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Remove parentheses text
        updated_content = remove_parentheses_text(content)
        
        # Write updated content back to the file
        with open(file_path, 'w') as file:
            file.write(updated_content)
        print(f"File '{file_path}' has been updated.")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
if __name__ == "__main__":
    import os

    print("Select the file to update:")
    file_path = input("Enter the file path: ").strip()

    if os.path.isfile(file_path):
        update_file(file_path)
    else:
        print("The specified path is not a valid file.")