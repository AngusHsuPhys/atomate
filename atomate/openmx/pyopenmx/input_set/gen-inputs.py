import yaml
from jinja2 import Template

import os 

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load the YAML
with open('input.yaml', 'r') as file:
  yaml_data = yaml.safe_load(file)

# Convert the YAML data to a dictionary
data = dict(yaml_data)

# Load the template
with open('template.dat', 'r') as file:
  template_str = file.read()

# Create the Jinja2 template object
template = Template(template_str)

# Render the template with the data
output = template.render(System=data['System'], Species=data['Species'], Atoms=data['Atoms'], Scf=data['scf'], MD=data['MD'])

print(output)

# Write the output to a file

with open('output.dat', 'w') as file:
  file.write(output)
  