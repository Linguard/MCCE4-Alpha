#!/usr/bin/env python3

"""Module: job_setup.py

Contains functions to prepare a user's benchmarking folder using user-provided options
(from cli args if cli is used).

Functions:
----------
* setup_pdbs_folder(bench_dir:str) -> None:
    Replicate current setup.
    - Create a copy of BENCH_PDBS (packaged data) in user_pdbs_folder = `bench_dir`/runs,
      or in user_pdbs_folder = `./runs` if called from within `bench_dir`;
    - Soft-link the relevant pdb as "prot.pdb";
    - Copy the "queue book" and default script files (BenchResources.BENCH_Q_BOOK,
      BenchResources.DEFAULT_JOB_SH, respectively) in `user_pdbs_folder`;
    - Copy ancillary files BenchResources.BENCH_WT, BenchResources.BENCH_PROTS `bench_dir`.

* write_run_script(job_name, steps_options_dict)
    Beta Phase : job_name = "default_run" (or soft link to 'default_run.sh' if 
    given name is different but script is still default).
    Write a shell script in user_job_folder similar to RUN_SH_DEFAULTS.

    Current default template: (BenchResources.DEFAULT_JOB_SH, "default_run.sh"):
     ```
     #!/bin/bash

     step1.py prot.pdb --dry
     step2.py
     step3.py
     step4.py --xts

     sleep 10
     ```
"""
from argparse import Namespace
import logging
import os
import pandas as pd
from pathlib import Path
import shutil
import sys
from typing import Union
from mcce4.mcce_benchmark import BenchResources, META, BOOK, DEFAULT_JOB, DEFAULT_JOB_SH
from mcce4.mcce_benchmark import SUB1, SUB2, SUB4, RUNS_DIR, N_BATCH
from mcce4.mcce_benchmark import audit
from mcce4.mcce_benchmark.io_utils import make_executable


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


CREATED_PRM_MSG = """
# custom.prm created by bench app to store user key(s) in -u options.
# Note: The -u option in the bench app is used for relinking customized name.txt or extra.tpl files ONLY;
#       Additional options must be given in a customized run.prm file passed to -load_runprm.
#
"""
# partial message, ending is dynamically determined:
NEW_NPDBS = """There is an existing PDBIDS file from a previous setup: %s with %s pdbs.
Your new call is asking for %s pdbs. Existing folders will not be removed, but the book file will
be re-written. If this is correct, delete the existing file and rerun your command, else """


def check_differing_setup(existing_fp: Path, out_fp: Path, dataset: str):
    """PDBIDS files should have the same name, if not abort & give user  a fix
    if current call is asking for a different number of pdbs.
    """
    # if existing_fp.parent.name != "META":
    #     shutil.move(existing_fp, out_fp.parent)
    #     existing_fp = out_fp.parent.joinpath(existing_fp)
    
    if existing_fp.name == out_fp.name:
        return

    n1, n2 = "all", "all"
    if existing_fp.name.endswith("_smallest"):
        n1 = int(existing_fp.name.removeprefix(f"PDBIDS_{dataset}_").split("_")[0])
    if out_fp.name.endswith("_smallest"):
        n2 = int(out_fp.name.removeprefix(f"PDBIDS_{dataset}_").split("_")[0])
    if n1 == "all":
        msg = NEW_NPDBS + "rerun your command without the -n_pdbs option."
        logger.critical(msg, str(existing_fp), n1, n2)
    else:
        msg = NEW_NPDBS + "match the value of option -n_pdbs to %s."
        logger.critical(msg, str(existing_fp), n1, n2, n1)

    sys.exit(1)


def get_pkdb_list(dataset:str,
                  return_df: bool = False,
                  n_pdbs: int = None) -> Union[pd.DataFrame, Path]:
    """Write non-excluded 'PDBIDS' file to enable selection by file.
    If n_pdbs is not None, creates 'PDBIDS_<n_pdbs>_smallest'.
    - n_pdbs: To save & return a list of n smaller pdbids.
    File is sorted ascendingly by number of residues, Res#.
    """
    dsbr = BenchResources(dataset)

    if n_pdbs is None or n_pdbs >= dsbr.N_PDBS:
        out_fp = Path(META, f"PDBIDS_{dataset}")
    else:
        out_fp = Path(META, f"PDBIDS_{dataset}_{n_pdbs}_smallest")

    existing = list(Path(META).glob("PDBIDS_*"))
    if existing:
        # take 1st, there should only be one:
        check_differing_setup(existing[0], out_fp, dataset)
    
    df = pd.read_csv(dsbr.BENCH_PROTS, sep="\t")
    cols = "PDB Res# Method Function Biounits Resolution".split()
    df = df[cols]
    # filter out commented rows
    msk = df.PDB.str.startswith("#")
    df = df[~msk]
    df.sort_values(by="Res#", ascending=True, inplace=True)

    if n_pdbs is not None and n_pdbs < dsbr.N_PDBS:
        df = df[:n_pdbs]

    out_fp.write_text(df.to_string(index=False) + "\n")
    logger.info(f"Saved pkDB pdbs list in: {out_fp!s}")

    if return_df:
        return df
    return out_fp


def create_next_commands(args: Namespace):
    """Create scripts 'launch.sh' and 'analyse.sh' with the pre-populated commands.
    The launch command uses the scheduler (bench_setup launch).
    """
    if not hasattr(args, "n_batch"):
        setattr(args, "n_batch", N_BATCH)
    n_batch = args.n_batch

    cmd = ("#!/bin/bash\n\n"
           "# command to launch runs with the scheduler:\n\n"
           "bench_setup launch -bench_dir . -job_name "
           f"{args.job_name} -n_batch {n_batch} -sentinel_file {args.sentinel_file}\n\n"
    )
    
    launch_sh = Path(args.bench_dir).joinpath("launch.sh")
    if launch_sh.exists():
        launch_sh.unlink()
    launch_sh.write_text(cmd)
    make_executable(launch_sh)
    logger.info("Use launch.sh to submit the jobs to the scheduler.")

    cmd = ("#!/bin/bash\n\n"
           "# command to run the analysis when the runs have completed.\n\n"
           f"bench_analyze {args.subparser_name} -bench_dir . \n\n"
    )
    ana_sh = Path(args.bench_dir).joinpath("analyze.sh")
    if ana_sh.exists():
        ana_sh.unlink()
    ana_sh.write_text(cmd)
    make_executable(ana_sh)
    logger.info("Use analyze.sh to run the analysis when all jobs have completed.")

    return


def relink_files(bench_dir: Path, custom_files: dict, no_runsdir: bool=False):
    """
    custom_files (dict): key=filename local to prot folder, value=source
    """
    if no_runsdir:
        runs_dir = ""
    else:
        runs_dir = RUNS_DIR

    for d in bench_dir.joinpath(runs_dir).glob("*/"):
        if not d.is_dir():
            continue

        os.chdir(d)
        for fname, src_path in custom_files.items():
                #local file:
                fp = d.joinpath(fname)
                try:
                    fp.symlink_to(src_path)
                except FileExistsError:
                    if not fp.is_symlink() or (fp.resolve().name != src_path.name):
                        fp.unlink()
                        fp.symlink_to(src_path)
                        logger.info(f"Soft-linked {src_path} as {fname} in {d.name}.")
        os.chdir("../")

    return


def setup_customized_files(args: Namespace) -> Namespace:
    """Soft-link the file paths given to the '-u' or '-load_runprm command line options into
    each of the proteins folders.
    1) If `args.u` contains other keys besides EXTRA and RENAME_RULES, a custom runprm is created
       to pass the additional keys.
    2) `args.u` is reset to its default value ("").
    3) `args.load_runprm` is reset to the linked filename in the protein folders: 'run.prm.user'.
    
    * Expected, but not checked: Entries that must appear in customized runprm (args.load_runprm)
      if the corresponding key is given in args.u:
        name.txt     (RENAME_RULES)
        extra.tpl    (EXTRA)

    Arguments:
      - args (argparse.Namespace) :: arguments parsed from the cli.
    Returns:
      - the input args (argparse.Namespace) with the reset -u option and updated -load_runprm option
        to match the linked files in the prot folders.
    """
    # case 0: function was called without prior checks:
    if not args.load_runprm and not args.u:
        logger.info("No customized files to soft-link.")
        return args
    
    bdir = Path(args.bench_dir)
    user_prm = args.load_runprm != ""

    # other cases: user prm or -u data (or both)
    if user_prm:
        customprm = bdir.joinpath(args.load_runprm)
        if not customprm.exists():
            logger.info(f"Customized run.prm not found: {customprm!s}")
            sys.exit(1)

        # simplest case, customized run.prm, but no u option:
        if not args.u:
            relink_files(bdir, {"run.prm.user": customprm})
            args.load_runprm = "run.prm.user"
            return args

    if args.u:
        u_info = {}
        # read keys, values into dict:
        for field in args.u.split(","):
            try:
                key, value = field.split("=")
                u_info[key] = value
            except ValueError:
                logger.critical(f"Each component format is 'KEY=VALUE'. Unrecognized: {field}.")
                sys.exit(1)

        to_relink = {}   # will only hold the EXTRA or RENAME_RULES data
        custom_found = False

        k = "EXTRA" 
        if u_info.get(k) is not None:
            custom_found = True
            # save the info:
            to_relink["extra.tpl"] = bdir.joinpath(u_info[k])
            # remove
            _ = u_info.pop(k)

        k = "RENAME_RULES"
        if u_info.get(k) is not None:
            custom_found = True
            # save the info:
            to_relink["name.txt"] = bdir.joinpath(u_info[k])
            # remove
            _ = u_info.pop(k)

        if len(u_info):   # not empty: there were more than 2 keys in the -u option
            if not user_prm:
                # create a user run.prm file:
                customprm = bdir.joinpath("custom.prm")
                customprm.touch()
                customprm.write_text(CREATED_PRM_MSG)
                to_relink["run.prm.user"] = customprm
                user_prm = True
                args.load_runprm = "run.prm.user"

            # update with additional entries:
            with open(customprm, "a") as fp:
                for k,v in u_info.items():
                    fp.write(f"{v:30s}    ({k})\n")
    
        if custom_found:
            if not user_prm:
                # create a user run.prm file:
                customprm = bdir.joinpath("custom.prm")
                customprm.touch()
                customprm.write_text(CREATED_PRM_MSG)
                # update with customized files info:
                with open(customprm, "a") as fp:
                    k = "name.txt"
                    if to_relink.get(k) is not None:
                        fp.write(f"{k:30s}    (RENAME_RULES)\n")
                    k = "extra.tpl"
                    if to_relink.get(k) is not None:
                        fp.write(f"{k:30s}    (EXTRA)\n")

                to_relink["run.prm.user"] = customprm
                args.load_runprm = "run.prm.user"
            else:
                # assume custom prm properly setup (has customized filenames local to prot folders)
                to_relink["run.prm.user"] = customprm
                args.load_runprm = "run.prm.user"  # reset to filename local to prot folder
        
    args.u = ""  # reset to default

    # finally perform the relinking:
    relink_files(bdir, to_relink)
    logger.info("All files relinked into the proteins run folders.")

    return args


def amend_book_file(book_fp: Path, valid_pdbs: list):
    """Future:
    If new call with differing n_pdbs amend book.txt accordingly:
    if book entry not in valid_pdbs: comment out;
    add new entries from vali_pdbs.
    """
    pass

    
def setup_ancillaries(bench_dir: Path, subcmd: str=SUB1, no_runsdir: bool= False,
                      valid_pdbs: list = None):
    """Install a copy of the book.txt and default script files in <bench_dir>/runs.
    """
    if no_runsdir:
        runs_dir = ""
    else:
        runs_dir = RUNS_DIR

    runs_d = bench_dir.joinpath(runs_dir)
    if runs_d.name != bench_dir.name and not runs_d.exists():
        sys.exit(f"The 'runs' subfolder should have been setup prior to installing the book and default script files!")
    
    if subcmd == SUB4:
        bench = BenchResources(SUB2)
    else:
        bench = BenchResources(subcmd)

    # copy script file:
    dest = runs_d.joinpath(DEFAULT_JOB_SH)
    if not dest.exists():
        shutil.copy(bench.DEFAULT_JOB_SH, dest)
        logger.info(f"Setup default script: {dest!s}")

    book_fp = runs_d.joinpath(BOOK)
    #if not book_fp.exists():
    audit.rewrite_book_file(book_fp, subcmd=subcmd)
    logger.info(f"Setup bookkeeping file: {book_fp!s}")
    #else:
    #   #PDBIDS_fp = list(bench_dir.joinpath(META).glob("PDBIDS_*"))[0]
    #   amend_book_file(book_fp, valid_pdbs)

    return


def setup_user_runs(args: Namespace) -> None:
    """
    - Create subfolders for the pdbs found in args.pdbs_list, which is a file or dir path,
      in bench_dir[/runs];
    - Soft-link the relevant pdb as "prot.pdb";
    - Create a "queue book" and default script files in <bench_dir>/runs;
    """
    bench_dir = Path(args.bench_dir)
    if args.no_runsdir:
        runs_dir = bench_dir
    else:
        runs_dir = bench_dir.joinpath(RUNS_DIR)
        runs_dir.mkdir(exist_ok=True)

    pdbs_in_file = False
    pdbs_lst = []
    # args.pdbs_list: from file or dir
    p = Path(args.pdbs_list)
    if p.is_dir():
        pdbs_lst = list(p.glob("*.pdb"))
        if not pdbs_lst:
            logger.error(f"No pdbs in {p}.")
            sys.exit(1)
    else:
        pdbs_in_file = True
        with open(p) as f:
            for lx, lin in enumerate(f, start=1):
                if lx > args.n_pdbs:
                    break
                line = lin.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    continue
                pdb_fp = Path(line)
                if pdb_fp.exists():
                    if pdb_fp.is_symlink():
                        logger.error(f"Cannot use a linked file as pdb source: {pdb_fp!s}")
                        continue
                    pdbs_lst.append(pdb_fp)

        if not pdbs_lst:
            logger.error(f"None of the pdbs in {p!s} were found.")
            sys.exit(1)

    if args.no_runsdir:
        runs_dir = bench_dir
    else:
        runs_dir = bench_dir.joinpath(RUNS_DIR)
        if not runs_dir.exists():
            runs_dir.mkdir()

    for i, fp in enumerate(pdbs_lst):
        if pdbs_in_file:
            # use parent folder name as prot folder:
            pname = fp.parent.name
        else:
            pname = fp.stem
        # create pdb dir:
        pd = runs_dir.joinpath(pname.upper())
        if not pd.is_dir():
            pd.mkdir()

        fp_dest = pd.joinpath(fp.name)
        if not fp_dest.exists():
            shutil.copy(fp, fp_dest, follow_symlinks=False)

        # cd to avoid links with long names:
        os.chdir(pd)
        prot = Path("prot.pdb")
        try:
            prot.symlink_to(fp.name)
        except FileExistsError:
            if not prot.is_symlink() or (prot.resolve().name != fp.name):
                prot.unlink()
                prot.symlink_to(fp.name)
                logger.info(f"Reset soft-linked pdb to prot.pdb for {pd.name}")
        os.chdir("../")  # pd.parent: runs_dir)

    os.chdir(bench_dir)
    
    setup_ancillaries(bench_dir, subcmd=args.subparser_name, no_runsdir=args.no_runsdir,
                      valid_pdbs=pdbs_lst)
    logger.info(f"The data setup in {runs_dir!s} went beautifully!")

    return


def list_user_pdbids(pdbids_file: str) -> list:
    """Extract the PDB from user-supplied file, which
    is presumed to be a modification of the file created by
    mcce_benchmark.cli.get_pkdb_list. The PDB ids are assumed to
    be in the first column, named 'PDB'.
    """
    return pd.read_fwf(Path(pdbids_file)).PDB.to_list()


def setup_pkdb_runs(bench_dir: str, n_pdbs: int, pdbids_file: str, subcmd: str, no_runsdir: bool=False) -> None:
    """
    Replicate current setup.
    - Create a copy of BENCH_PDBS (packaged data) in <bench_dir>/runs, or a subset
      of size (1, n_pdbs) if n_pdbs < dataset.N_PDBS.
    - Soft-link the relevant pdb as "prot.pdb";
    - Copy the "queue book" and default script files (BenchResources.BENCH_Q_BOOK,
      BenchResources.DEFAULT_JOB_SH) in <bench_dir>/runs;
    """
    bench_dir = Path(bench_dir)

    if pdbids_file:
        logger.info(f"Loading pdbids from user file {pdbids_file}.")
        PDBIDS = list_user_pdbids(pdbids_file)
        if not PDBIDS:
            logger.error("Empty pdbids list.")
            sys.exit(1)
    else:
        # create pdbids file with n_pdbs smallest or all pdbs:
        pdbids_file = get_pkdb_list(subcmd, n_pdbs=n_pdbs)
        PDBIDS = list_user_pdbids(pdbids_file)
        if not PDBIDS:
            logger.error("Empty pdbids list.")
            sys.exit(1)

    if no_runsdir:
        runs_dir = bench_dir
    else:
        runs_dir = bench_dir.joinpath(RUNS_DIR)
        runs_dir.mkdir(exist_ok=True)    

    bench = BenchResources(subcmd)
    try:
        valid = [f"{d.name}/{d.name.lower()}.pdb"
                    for d in list(bench.BENCH_PDBS.glob("./*"))
                    if (d.is_dir() and d.name in PDBIDS)]
    except UnboundLocalError:
        # likely there is a mismatch between an existing PDBIDS file name due to differing
        # command line options
        print("UnboundLocalError on PDBIDS file var.")
        sys.exit(1)

    for i, v in enumerate(valid):
        if i == n_pdbs:
            break
        # v :: PDBID/pdbid.pdb
        p = runs_dir.joinpath(v)
        d = p.parent
        if not d.is_dir():
            logger.info(f"Creating {d!s}.")
            d.mkdir()

        if not p.exists():
            shutil.copy(bench.BENCH_PDBS.joinpath(v), p)

        # cd to avoid links with long names:
        os.chdir(d)

        prot = Path("prot.pdb")
        try:
            prot.symlink_to(p.name)
        except FileExistsError:
            if not prot.is_symlink() or (prot.resolve().name != p.name):
                prot.unlink()
                prot.symlink_to(p.name)
                logger.info(f"Reset soft-linked pdb to prot.pdb for {d.name}")

        os.chdir("../")  # d.parent)

    os.chdir(bench_dir)

    setup_ancillaries(bench_dir, subcmd=subcmd, no_runsdir=no_runsdir, valid_pdbs=valid)
    logger.info(f"The data setup in {runs_dir!s} went beautifully!")

    return


def get_default_script(pdbs_dir: str, subcmd:str) -> Path:
    """Re-install BENCH_DATA/DEFAULT_JOB_SH in pdb_dir if not found.
    Return its path.
    """
    pdbs_dir = Path(pdbs_dir)
    sh_path = pdbs_dir.joinpath(DEFAULT_JOB_SH)
    if not sh_path.exists():
        shutil.copy(BenchResources(subcmd).DEFAULT_JOB_SH, sh_path)
        logger.info(f"Re-installed {DEFAULT_JOB_SH}")

    return sh_path


def write_default_run_script(bench_dir: str, subcmd: str = SUB1, job_name: str = DEFAULT_JOB, no_runsdir: bool=False) -> None:
    """
    To use when cli args are all default.
    If job_name is different from "default_run", the default script is soft-linked to it
    as <job_name>.sh
    """
    bench_dir = Path(bench_dir)
    curr = Path.cwd()
    in_benchmarks = curr.name == bench_dir.name
    if in_benchmarks:
        bench_dir = curr

    if no_runsdir:
        user_pdbs = bench_dir
    else:
        user_pdbs = bench_dir.joinpath(RUNS_DIR)

    # reinstall the default script if not found:
    default_sh = get_default_script(user_pdbs, subcmd)

    sh_name = f"{job_name}.sh"
    if job_name == DEFAULT_JOB:
        sh_path = default_sh
    else:
        # soft-link default_sh to sh_name
        if not in_benchmarks:
            os.chdir(bench_dir)

        os.chdir(user_pdbs)

        sh_path = Path(sh_name)
        try:
            sh_path.symlink_to(default_sh)
        except FileExistsError:
            sh_path.unlink()
            sh_path.symlink_to(default_sh)

        logger.info(f"Soft-linked {default_sh} as {sh_name}")

        # reset path:
        sh_path = user_pdbs.joinpath(sh_name)

    logger.info(f"Script contents:\n{sh_path.read_text()}\n")
    os.chdir(curr)

    return
