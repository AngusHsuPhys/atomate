import yaml

import os 

os.chdir(os.path.dirname(os.path.abspath(__file__)))


# Read the data from the .dat file
with open('PAO-raw.dat', 'r') as file:
    lines = file.readlines()

# Skip the header line
lines = lines[1:]

# Parse the data into a list of dictionaries
data = []
for line in lines:
    vps, valence, quick, standard, precise = line.strip().split('\t')
    data.append({
        'VPS': vps,
        'Valence electrons': float(valence),
        'Quick': quick,
        'Standard': standard,
        'Precise': precise
    })

# Write the data to a .yaml file
with open('PAO-table.yaml', 'w') as file:
    yaml.dump(data, file)