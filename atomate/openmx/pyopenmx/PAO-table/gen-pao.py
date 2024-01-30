import yaml

import os 
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def parse_raw_data():
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



def generate_string(vps, option):
    # this function should give me "O O6.0-s2p2 O_PBE19" for example based on the yaml file "- Precise: O6.0-s3p2d2
# - Standard: O6.0-s3p2d2
# - Quick: O6.0-s2p2
# - VPS: O_PBE19
# and the vps and option input arguments (e.g. vps = "O_PBE19" and option = "Quick") 
    
    # Read the data from the .yaml file
    with open('PAO-table.yaml', 'r') as file:
        data = yaml.safe_load(file)

    # if option is not in the list of ["Quick", "Standard", "Precise"], raise ValueError
    if option not in ["Quick", "Standard", "Precise"]:
        raise ValueError(f"Option {option} not in list of options")
    
    # Find the dictionary with the matching VPS
    for d in data:
        if d['VPS'] == vps:
            element = vps.split('_')[0]
            pao_string = f"{element} {d[option]} {vps}"
            return pao_string

    # If we get here, we didn't find a match
    raise ValueError(f"VPS {vps} not found in PAO-table.yaml")



if __name__ == "__main__":
    print(generate_string("O_PBE19", "Quick"))
    print(generate_string("O_PBE19", "Standard"))
    print(generate_string("O_PBE19", "Precise"))
    print(generate_string("O_PBE19", "Valence electrons"))

