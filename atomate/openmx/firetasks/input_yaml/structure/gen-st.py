import yaml
import re
import os

# set the default path to the directory of this package atomate
os.chdir("/workspaces/openmx-wf/Atomate/atomate/atomate/openmx/firetasks/input_yaml/structure")

# Load the yaml file
with open('input-set.yaml', 'r') as yaml_file:
    data = yaml.safe_load(yaml_file)

# Open the template file
with open('structure_template.dat', 'r') as file:  # changed from 'structure_template.dat'
    content = file.read()

# Replace placeholders with corresponding values from the yaml file
for key, value in data['Atoms'].items():  # changed from data.items()
    # Remove trailing newline from value
    value = str(value).rstrip('\n')
    content = re.sub(f'\(\({key}\)\)', value, content)

# Write the a new file with the replaced content
with open('st.dat', 'w') as file:
    file.write(content)