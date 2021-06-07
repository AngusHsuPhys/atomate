from atomate.common.firetasks.glue_tasks import DeleteFiles
from atomate.utils.utils import get_meta_from_structure, get_fws_and_tasks
from atomate.vasp.config import (
    ADD_NAMEFILE,
    SCRATCH_DIR,
    ADD_MODIFY_INCAR,
    GAMMA_VASP_CMD,
    VDW_KERNEL_DIR
)

from atomate.vasp.firetasks.jcustom import JFileTransferTask, JWriteInputsFromDB
from atomate.vasp.firetasks.glue_tasks import CheckStability, CheckBandgap, CopyFiles
from atomate.vasp.firetasks.lobster_tasks import RunLobsterFake
from atomate.vasp.firetasks.neb_tasks import RunNEBVaspFake
from atomate.vasp.firetasks.parse_outputs import JsonToDb
from atomate.vasp.firetasks.run_calc import (
    RunVaspCustodian,
    RunVaspFake,
    RunVaspDirect,
    RunNoVasp,
)
from atomate.vasp.firetasks.write_inputs import ModifyIncar, ModifyPotcar, ModifyKpoints, WriteVaspFromPMGObjects

from fireworks import Workflow, FileWriteTask
from fireworks.core.firework import Tracker
from fireworks.utilities.fw_utilities import get_slug
from pymatgen import Structure
from pymatgen.io.vasp.inputs import Kpoints
from pymatgen.io.vasp.sets import MPRelaxSet
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.symmetry.bandstructure import HighSymmKpath



import os

__author__ = "Jeng-Yuan Tsai"
__email__ = "tsaie79@gmail.com"


def scp_files(
        original_wf,
        dest,
        fw_name_constraint=None,
        task_name_constraint="VaspToDb",
):
    """
    SCP ALL files to local computer

    Args:
        original_wf (Workflow)
        dest (str): "/home/jengyuantsai/test_scp_fw/defect_db/binary_vac_AB/" (make sure every folder exists)
        fw_name_constraint (str): pattern for fireworks to clean up files after
        task_name_constraint (str): pattern for firetask to clean up files

    Returns:
       Workflow
    """
    idx_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint=task_name_constraint,
    )
    for idx_fw, idx_t in idx_list:
        original_wf.fws[idx_fw].tasks.insert(idx_t + 1, JFileTransferTask(
            mode="rtransfer",
            files=["all"],
            dest=dest,
            server="localhost",
            user="jengyuantsai"
        ))

    return original_wf

def write_inputs_from_db(original_wf, db_file, task_id, modify_incar, write_chgcar=True, fw_name_constraint=None):

    idx_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="RunVasp",
    )
    for idx_fw, idx_t in idx_list:
        original_wf.fws[idx_fw].tasks.insert(idx_t - 1, JWriteInputsFromDB(db_file=db_file, task_id=task_id,
                                                                           write_chgcar=write_chgcar,
                                                                           modify_incar=modify_incar))
    return original_wf

def jmodify_to_soc(
            original_wf,
            structure,
            nbands=None,
            saxis=[0,0,1],
            magmom=None,
            modify_incar_params=None,
            fw_name_constraint=None,
    ):
    """
    Takes a regular workflow and transforms its VASP fireworkers that are
    specified with fw_name_constraints to non-collinear calculations taking spin
    orbit coupling into account.
    Args:
        original_wf (Workflow): The original workflow.
        nbands (int): number of bands selected by the user (for now)
        structure (Structure)
        modify_incar_params ({}): a dictionary containing the setting for
            modifying the INCAR (e.g. {"ICHARG": 11})
        fw_name_constraint (string): name of the fireworks to be modified (all
            if None is passed)
    Returns:
        Workflow: modified with SOC
    """

    if structure is None:
        try:
            sid = get_fws_and_tasks(
                original_wf,
                fw_name_constraint="structure optimization",
                task_name_constraint="WriteVasp",
            )
            fw_id = sid[0][0]
            task_id = sid[0][1]
            structure = (
                original_wf.fws[fw_id].tasks[task_id]["vasp_input_set"].structure
            )
        except:
            raise ValueError(
                "modify_to_soc powerup requires the structure in vasp_input_set"
            )

    if not magmom:
        magmom = [[0,0,mag_z] for mag_z in MPRelaxSet(structure).incar.get("MAGMOM", None)]

    modify_incar_soc = {
        "incar_update": {
            "LSORBIT": "T",
            "SAXIS": saxis,
            "MAGMOM": magmom,
            "ISPIN": 2,
            "ICHARG":11,
            # "LMAXMIX": 4,
            "ISYM": 0,
        }
    }
    if nbands:
        modify_incar_soc["incar_update"].update({"NBANDS": nbands})

    if modify_incar_params:
        modify_incar_soc["incar_update"].update(modify_incar_params)

    run_vasp_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="RunVasp",
    )
    for idx_fw, idx_t in run_vasp_list:
        original_wf.fws[idx_fw].tasks[idx_t]["vasp_cmd"] = ">>vasp_ncl<<"
        original_wf.fws[idx_fw].tasks.insert(idx_t, ModifyIncar(**modify_incar_soc))

        original_wf.fws[idx_fw].name += "_soc"

    run_boltztrap_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="RunBoltztrap",
    )
    for idx_fw, idx_t in run_boltztrap_list:
        original_wf.fws[idx_fw].name += "_soc"

    # revise task_label to xxx_soc in db
    to_db_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="VaspToDb",
    )
    for idx_fw, idx_t in to_db_list:
        original_wf.fws[idx_fw].tasks[idx_t]["additional_fields"].update({"task_label": original_wf.fws[idx_fw].name})

    return original_wf

def remove_todb(original_wf, fw_name_constraint=None):
    """
    Simple powerup that clears the VaspToDb to a workflow.
    Args:
        original_wf (Workflow): The original workflow.
        fw_name_constraint (str): name constraint for fireworks to
            have their modification tasks removed
    """
    idx_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="VaspToDb",
    )
    idx_list.reverse()
    for idx_fw, idx_t in idx_list:
        original_wf.fws[idx_fw].tasks.pop(idx_t)
    return original_wf

def write_PMGObjects(original_wf, pmg_objs, fw_name_constraint=None):

    idx_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="RunVasp",
    )

    for idx_fw, idx_t in idx_list:
        original_wf.fws[idx_fw].tasks.insert(
            idx_t, WriteVaspFromPMGObjects(**pmg_objs)
        )
    return original_wf

def cp_vdw_file(original_wf, fw_name_constraint=None):

    idx_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="RunVasp",
    )

    for idx_fw, idx_t in idx_list:
        original_wf.fws[idx_fw].tasks.insert(
            idx_t-1, CopyFiles(from_dir=VDW_KERNEL_DIR)
        )
    return original_wf

def cp_vasp_from_prev(original_wf, vasp_io, fw_name_constraint=None):
    idx_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="CopyVaspOutputs",
    )
    for idx_fw, idx_t in idx_list:
        if original_wf.fws[idx_fw].tasks[idx_t]["additional_files"]:
            original_wf.fws[idx_fw].tasks[idx_t]["additional_files"].extend(vasp_io)
        else:
            original_wf.fws[idx_fw].tasks[idx_t].update({"additional_files": vasp_io})
    return original_wf

def add_modify_twod_bs_kpoints(
        original_wf, modify_kpoints_params=None, fw_name_constraint=None
):
    """
    Every FireWork that runs VASP has a ModifyKpoints task just beforehand. For
    example, allows you to modify the KPOINTS based on the Worker using env_chk
    or using hard-coded changes.

    Args:
        original_wf (Workflow)
        modify_kpoints_params (dict): dict of parameters for ModifyKpoints.
        fw_name_constraint (str): Only apply changes to FWs where fw_name
        contains this substring.

    Returns:
       Workflow
    """
    def twod_bs_kpoints(structure, added_kpoints=None, reciprocal_density=50, kpoints_line_density=20, mode="line"):
        """
        :return: Kpoints
        """
        added_kpoints = added_kpoints if added_kpoints is not None else []
        kpts = []
        weights = []
        all_labels = []

        # for both modes, include the Uniform mesh w/standard weights
        grid = Kpoints.automatic_density_by_vol(structure, reciprocal_density).kpts
        ir_kpts = SpacegroupAnalyzer(structure, symprec=0.1).get_ir_reciprocal_mesh(
            grid[0]
        )
        for k in ir_kpts:
            if round(k[0][2], 1) != 0:
                continue
            kpts.append(k[0])
            weights.append(int(k[1]))
            all_labels.append(None)

        # for both modes, include any user-added kpoints w/zero weight
        for k in added_kpoints:
            kpts.append(k)
            weights.append(0.0)
            all_labels.append("user-defined")

        # for line mode only, add the symmetry lines w/zero weight
        if mode.lower() == "line":
            kpath = HighSymmKpath(structure)
            frac_k_points, labels = kpath.get_kpoints(
                line_density=kpoints_line_density, coords_are_cartesian=False
            )

            two_d_kpt, two_d_kpt_label = [], []
            for kpt, klabel in zip(frac_k_points, labels):
                if round(kpt[2], 1) == 0:
                    two_d_kpt.append(kpt)
                    two_d_kpt_label.append(klabel)
            frac_k_points, labels = two_d_kpt, two_d_kpt_label

            for k, f in enumerate(frac_k_points):
                kpts.append(f)
                weights.append(0.0)
                all_labels.append(labels[k])

        comment = (
            "HSE run along symmetry lines"
            if mode.lower() == "line"
            else "HSE run on uniform grid"
        )

        return Kpoints(
            comment=comment,
            style=Kpoints.supported_modes.Reciprocal,
            num_kpts=len(kpts),
            kpts=kpts,
            kpts_weights=weights,
            labels=all_labels,
        )


    modify_kpoints_params = modify_kpoints_params or {
        "twod_kpoints_update": ">>twod_kpoints_update<<"
    }

    added_kpoints = modify_kpoints_params.get("added_kpoints", None)
    reciprocal_density = modify_kpoints_params.get("reciprocal_density", 50)
    kpoints_line_density = modify_kpoints_params.get("kpoints_line_density", 20)
    mode = modify_kpoints_params.get("mode", "line")

    kpoints = twod_bs_kpoints(
        structure=Structure.from_file("POSCAR"),
        added_kpoints=added_kpoints,
        reciprocal_density=reciprocal_density,
        kpoints_line_density=kpoints_line_density,
        mode=mode
    )

    idx_list = get_fws_and_tasks(
        original_wf,
        fw_name_constraint=fw_name_constraint,
        task_name_constraint="RunVasp",
    )
    for idx_fw, idx_t in idx_list:
        original_wf.fws[idx_fw].tasks.insert(
            idx_t, WriteVaspFromPMGObjects(kpints=kpoints)
        )
    return original_wf
