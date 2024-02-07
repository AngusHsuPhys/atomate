"""
Defines standardized Fireworks that can be chained easily to perform various
sequences of VASP calculations.
"""
from __future__ import annotations

import warnings
from typing import Any

from fireworks import Firework

from atomate.common.firetasks.glue_tasks import (
    CopyFiles,
    DeleteFiles,
    GzipDir,
    PassCalcLocs,
)
from atomate.openmx.config import (
    DB_FILE,
    HALF_KPOINTS_FIRST_RELAX,
    VASP_CMD,
    VDW_KERNEL_DIR,
)
from atomate.openmx.firetasks.glue_tasks import CopyVaspOutputs, pass_vasp_result

from atomate.openmx.firetasks.parse_outputs import OpenmxToDb
from atomate.openmx.firetasks.run_calc import RunOpenmx
from atomate.openmx.firetasks.write_inputs import (
    ModifyIncar,
    WriteNormalmodeDisplacedPoscar,
    WriteScanRelaxFromPrev,
    WriteTransmutedStructureIOSet,
    WriteVaspFromIOSet,
    WriteVaspFromIOSetFromInterpolatedPOSCAR,
    WriteVaspHSEBSFromPrev,
    WriteVaspNSCFFromPrev,
    WriteVaspSOCFromPrev,
    WriteVaspStaticFromPrev,
)

from ase.calculators.openmx import OpenMX
from ase import Atoms

from pymatgen.io.ase import AseAtomsAdaptor
from pymatgen.io.vasp.inputs import Structure
from pymatgen.io.openmx.sets import ScfInputSet

class OptimizeFW(Firework):
    def __init__(
        self,
        structure,
        name="structure optimization",
        openmx_input_set=None,
        openmx_dft_data_path=">>openmx_dft_data_path<<",
        override_default_openmx_params=None,
        potcar_spec=None,
        magmoms=None,
        
        openmx_cmd=">>openmx_cmd<<",
        input_file=">>input_file<<",
        output_file=">>output_file<<",

        db_file=DB_FILE,
        parents=None,
        **kwargs,
    ):
        """
        Optimize the given structure.

        Args:
            structure (Structure): Input structure.
            name (str): Name for the Firework.
            vasp_input_set (VaspInputSet): input set to use. Defaults to MPRelaxSet() if None.
            override_default_vasp_params (dict): If this is not None, these params are passed to
                the default vasp_input_set, i.e., MPRelaxSet. This allows one to easily override
                some settings, e.g., user_incar_settings, etc.
            vasp_cmd (str): Command to run vasp.
            ediffg (float): Shortcut to set ediffg in certain jobs
            db_file (str): Path to file specifying db credentials to place output parsing.
            force_gamma (bool): Force gamma centered kpoint generation
            job_type (str): custodian job type (default "double_relaxation_run")
            auto_npar (bool or str): whether to set auto_npar. defaults to env_chk: ">>auto_npar<<"
            half_kpts_first_relax (bool): whether to use half the kpoints for the first relaxation
            parents ([Firework]): Parents of this particular Firework.
            **kwargs: Other kwargs that are passed to Firework.__init__.
        """
        override_default_openmx_params = override_default_openmx_params or {}


        t = []
        t.append(WriteVaspFromIOSet(
            structure=structure,
            openmx_input_set=openmx_input_set, 
            openmx_dft_data_path=openmx_dft_data_path,
            openmx_input_params=override_default_openmx_params,
            potcar_spec=potcar_spec,
            magmoms=magmoms,
        ))

        t.append(
            RunOpenmx(
                openmx_cmd=openmx_cmd,
                input_file=input_file,
                output_file=output_file,            
            )
        )
        t.append(PassCalcLocs(name=name))
        t.append(OpenmxToDb(db_file=db_file, additional_fields={"task_label": name}))
        super().__init__(
            t,
            parents=parents,
            name=f"{structure.composition.reduced_formula}-{name}",
            **kwargs,
        )