import yaml
from jinja2 import Template

import os 

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load the YAML
yaml_data = """
System:
  CurrrentDirectory: "./"
  Name: "c60"
  level_of_stdout: 1
  level_of_fileout: 1

Species:
    Number: 1
    Definition: |
        C   C5.0-s2p2   C_PBE19
    

Atoms:
  Number: 60
  SpeciesAndCoordinates:
    Unit: "Ang"
    Coordinates: |
      1  C -3.45975  0.71223 -4.17587  2.0 2.0
      2  C -4.63970  1.44078 -3.72814  2.0 2.0
      3  C -4.17340  2.64914 -3.01671  2.0 2.0
      4  C -2.71712  2.63783 -3.01734  2.0 2.0
      5  C -2.26803  1.42282 -3.72893  2.0 2.0
      # ... and so on for all 60 atoms
  UnitVectors:
    Unit: "Ang"
    Vectors: |
      12.0   0.0   0.0
      0.0  12.0   0.0
      0.0   0.0  12.0

scf:
  XcType: "GGA-PBE"
  SpinPolarization: "Off"
  ElectronicTemperature: 300.0
  EnergyCutoff: 150.0
  MaxIter: 70
  EigenvalueSolver: "cluster"
  Kgrid: "1 1 1"
  Mixing:
    Type: "rmm-diisk"
    Init:
      Mixing:
        Weight: 0.30
    Min:
      Mixing:
        Weight: 0.001
    Max:
      Mixing:
        Weight: 0.400
    History: 20
    StartPulay: 5
  Criterion: 1.0e-10

MD:
  Type: "nomd"
  MaxIter: 1
  TimeStep: 1.0
  Opt:
    Criterion: 1.0e-4
"""
data = yaml.safe_load(yaml_data)

# Define the template
template_str = """
#
#      File Name      
#

System.CurrrentDirectory         ./    # default=./
System.Name                      {{System.Name}}
level.of.stdout                   {{System.level_of_stdout}} # default=1 (0-2)
level.of.fileout                  {{System.level_of_fileout}} # default=1 (0-2)

#
# Definition of Atomic Species
#

Species.Number       {{Species.Number}}
<Definition.of.Atomic.Species
{{Species.Definition}}
Definition.of.Atomic.Species>

#
# Atoms
#

Atoms.Number        {{Atoms.Number}}
Atoms.SpeciesAndCoordinates.Unit   {{Atoms.SpeciesAndCoordinates.Unit}} # Ang|AU
<Atoms.SpeciesAndCoordinates       
{{Atoms.SpeciesAndCoordinates.Coordinates}}
Atoms.SpeciesAndCoordinates>
Atoms.UnitVectors.Unit             {{Atoms.UnitVectors.Unit}} # Ang|AU
<Atoms.UnitVectors                     # unit=Ang.
{{Atoms.UnitVectors.Vectors}}
Atoms.UnitVectors>

#
# SCF or Electronic System
#

scf.XcType                 {{Scf.XcType}} # LDA|LSDA-CA|LSDA-PW|GGA-PBE
scf.SpinPolarization       {{Scf.SpinPolarization}} # On|Off|NC
scf.ElectronicTemperature  {{Scf.ElectronicTemperature}} # default=300 (K)
scf.energycutoff           {{Scf.EnergyCutoff}}  # default=150 (Ry)      
scf.maxIter                {{Scf.MaxIter}}       # default=40
scf.EigenvalueSolver       {{Scf.EigenvalueSolver}} # DC|GDC|Cluster|Band
scf.Kgrid                  {{Scf.Kgrid}}         # means 4x4x4       
scf.Mixing.Type           {{Scf.Mixing.Type}}   # Simple|Rmm-Diis|Gr-Pulay|Kerker|Rmm-Diisk
scf.Init.Mixing.Weight     {{Scf.Mixing.Init.Mixing.Weight}} # default=0.30       
scf.Min.Mixing.Weight      {{Scf.Mixing.Min.Mixing.Weight}} # default=0.001        
scf.Max.Mixing.Weight      {{Scf.Mixing.Max.Mixing.Weight}} # default=0.40        
scf.Mixing.History          {{Scf.Mixing.History}} # default=5       
scf.Mixing.StartPulay       {{Scf.Mixing.StartPulay}} # default=6        
scf.criterion             {{Scf.Criterion}}     # default=1.0e-6 (Hartree)

#
# MD or Geometry Optimization
#

MD.Type                   {{MD.Type}} # Nomd|Opt|NVE|NVT_VS|NVT_NH       
MD.maxIter                  {{MD.MaxIter}} # default=1        
MD.TimeStep                {{MD.TimeStep}} # default=0.5 (fs)      
MD.Opt.criterion          {{MD.Opt.Criterion}} # default=1.0e-4 (Hartree/bohr)    
"""
template = Template(template_str)

# Render the template with the data
output = template.render(System=data['System'], Species=data['Species'], Atoms=data['Atoms'], Scf=data['scf'], MD=data['MD'])

print(output)