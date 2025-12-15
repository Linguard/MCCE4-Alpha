#!/usr/bin/env python3

"""
Module: cli.py

Command line interface for MCCE benchmarking.
Main entry point: "bench_setup"

+ 4 sub-commands:
 0. "pdbids"
    List the available pdbids from pkDBv1 & save as file.

 1. "pkdb_v1"
    Sub-command for setting up <bench_dir>/runs folder
    using the pdbs in pKaDBv1 & <job_name>.sh script.

 2. "user_pdbs"
    Sub-command for setting up <bench_dir>/runs folder
    using the user's pdbs & <job_name>.sh script.

 3. "launch"
    Sub-command for scheduling the processing of the set.
    Can be by-passed if 1. or 2. have the --launch flag, meaning 'launch now'.
"""
from argparse import ArgumentParser, RawDescriptionHelpFormatter, Namespace
import logging
import os

# # set virtual cores for NumExpr:: what should it be?
# # 64 == default, max virtual cores in NumExpr:
# os.environ['NUMEXPR_MAX_THREADS'] = "64"
# os.environ['NUMEXPR_NUM_THREADS'] = "32"

from pathlib import Path
import shutil
import sys

from mcce4.mcce_benchmark import BenchResources, BENCH_DATA, datasets_dict, datasets_size
from mcce4.mcce_benchmark import DEFAULT_JOB, META, RUNS_DIR
from mcce4.mcce_benchmark import ENTRY_POINTS, SUB0, SUB1, SUB2, SUB3, SUB4, SUB5
from mcce4.mcce_benchmark import FILES, BOOK, N_BATCH, N_PDBS, cli_opts
# modules:
from mcce4.mcce_benchmark import io_utils as iou
from mcce4.mcce_benchmark import cli_utils as cliu
from mcce4.mcce_benchmark import job_setup, scheduling, custom_sh
from mcce4.protinfo.cli import get_pdb_rpt


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# file handlers
flog_format = "[%(asctime)s - %(levelname)s]: %(name)s, %(funcName)s:\n\t%(message)s"
fh = logging.FileHandler("benchmark.log", encoding="utf-8")
fh.setLevel(logging.INFO)
fh_formatter = logging.Formatter(flog_format)
fh.setFormatter(fh_formatter)
# add to logger
logger.addHandler(fh)


datasets_size_str = f"; ".join(f"{k}: {v}" for k, v in datasets_size.items())


CLI_NAME = ENTRY_POINTS["setup"]


# help as empty f-strings: interpolated only if called
HELP_0 = """
Sub-command for listing & saving the available pdbids:
> {} {} -kind <dataset name> # valid dataset names start with 'pkdb_'.
"""

HELP_1 = """
Sub-command for setting up bench_dir[/runs] proteins folders & run.sh script, e.g.:
> {} {} -bench_dir <folder name> -n_pdbs 5  # max/default = {}
"""
HELP_2 = HELP_1
HELP_3 = HELP_1
HELP_4 = """
Sub-command for setting up bench_dir[/runs] proteins folders using user's pdb_list
& job_name_run.sh script, e.g.:
> {} {} -bench_dir <folder name>
"""

HELP_5 = """Sub-command for scheduling the processing of the set in batches; e.g.:
> {} {} -bench_dir <folder name> -n_batch 15
Note: if provided, the -job_name option value must match the one used in the `bench_setup [pkdb_X, user_pdbs]` command.
"""

DESC = """
Description:
Setup or launch a MCCE benchmarking job using either a dataset's curated structures
or the user's pdbs list.
"""


def in_dir_ok(bench_dir: Path):
    if bench_dir.name != Path.cwd().name:
        sys.exit("Please, rerun your command inside the bench_dir.")
    return


def get_usage() -> str:
    u = f"""
    Examples (cd to bench_dir, first):
    0. {SUB0}: Show & save the list of available pdbids:
    - Minimal input:
        > {CLI_NAME} {SUB0} -kind pkdb_vR

    1. {SUB1}: Data & script setup using pdbs from pkdb_v1 (the runs use --dry by default):
    - Minimal input: -bench_dir option:
        > {CLI_NAME} {SUB1} -bench_dir .

    - Using non-default option(s) (then job_name is required!):
        > {CLI_NAME} {SUB1} -bench_dir . --wet -job_name <wet_run>
        > {CLI_NAME} {SUB1} -bench_dir . -d 8 -job_name <job_e8>
    2. & 3. {SUB2}, {SUB3}:
      > {CLI_NAME} {SUB2} -bench_dir . 
      > {CLI_NAME} {SUB3} -bench_dir . 

    4. {SUB4}: Data & script setup using user's pdb list:
    - Minimal input: value for -bench_dir option, -pdb_list:
        >{CLI_NAME} {SUB4} -bench_dir . -pdb_list <path to dir with pdb files OR file listing pdbs paths>

    - Using non-default option(s) (then job_name is required! ):
        >{CLI_NAME} {SUB4} -bench_dir . -pdb_list <path> -d 8 -job_name <job_e8>

    5. {SUB5}: Launch the scheduled processing:
    - Minimal input: value for -bench_dir option: IFF no non-default job_name & sentinel_file were passed in {SUB1}
        >{CLI_NAME} {SUB5} -bench_dir .

    - Using non-default option(s):
        >{CLI_NAME} {SUB5} -bench_dir . -n_batch <jobs to maintain>

        Note: if changing the default sentinel_file="pk.out" to, e.g. step2_out.pdb,
            then the 'norun' script parameters for step 3 & 4 must be set accordingly:
            >{CLI_NAME} {SUB5} -bench_dir . -sentinel_file step2_out.pdb --s3_norun --s4_norun
    """
    return u


def do_pdbids(args: Namespace):
    """
    Get the list of available pdbs from an experimental data file;
    CHANGELOG (7-15-25): args.kind now refers to a dataset folder name.
    """
    if args.kind not in datasets_dict.keys():
        logger.error(f"This dataset kind: {args.kind!r} does not exists or is not yet setup.")
        sys.exit(1)

    out_fp = job_setup.get_pkdb_list(args.kind, n_pdbs=args.n_pdbs)
    # show
    if out_fp.exists():
        logger.info(f"Displaying the PDBIDs list saved as: {str(out_fp)!r}\n")
        print(out_fp.read_text())

    return


def do_prerun(args: Namespace):
    """Iterate over the runs/ subfolders to run step1 and produce a prerun report."""
    skipped = []
    if args.no_runsdir:
        runs_dir = args.bench_dir
    else:
        runs_dir = args.bench_dir.joinpath(RUNS_DIR)

    # preset with available data:
    info_args = {
        "pdb": None,
        "d": args.d,
        "u": args.u,
        "wet": args.wet,
        "noter": args.noter,
        "fetch": False,
        "save_dicts": True,
    }
    # use local book file, as per setup:
    all_pdbs = runs_dir.joinpath(BOOK).read_text().splitlines()
    # previously used globbing: does not preserve order; problem with debugging
    for dirname in all_pdbs:
        d = dirname.split()[0]

        # use the linked prot.pdb to get the actual pdb name
        prot = runs_dir.joinpath(d, "prot.pdb")
        if not prot.is_symlink():
            logger.error(f"Error: prot.pdb should be a link to the input pdb. Skipping {prot.parent!s}.")
            skipped.append(prot.parent)
            continue

        #pre_dir = runs_dir.joinpath(d, "prerun")
        if not args.redo_prerun and prot.parent.joinpath(f"{prot.readlink().stem}_protinfo.md").exists():
            logger.info(f"Not redoing: report found in {d!s} but redo_prerun is False.")
            continue

        # enter prot folder to run protinfo main fn:
        os.chdir(prot.parent)

        pdb = Path("prot.pdb").readlink()
        # run step1 and write prot report (from run1.log):
        info_args["pdb"] = pdb
        # ?? partial not working?
        # get_pdb_rpt creates the 'prerun' output subfolder in the current run:
        get_pdb_rpt(Namespace(**info_args)) #, do_checks=False, do_fetch=False)
        info_args["pdb"] = None

        os.chdir("../")

    if skipped:
        msg ="""
    ### NOTE: 'prot.pdb' in {runs_dir!s} subfolders is expected to be a link.
    Folder(s) skipped because 'prot.pdb' does not link to its parent: {skipped}
    """
        logger.info(msg)

    return


def populate_prerun_folder(bench_dir: Path, clear_folder: bool = False):
    """Soft-link all available runs subfolders *_protinfo.md files 
    in bench_dir/prerun folder.
    """
    rpt_dir = bench_dir.joinpath("prerun")
    if not rpt_dir.exists():
        rpt_dir.mkdir()
    else:
        if clear_folder:
            shutil.rmtree(rpt_dir)
            rpt_dir.mkdir()

    if bench_dir.joinpath(RUNS_DIR).exists():
        pdbs_dir = bench_dir.joinpath(RUNS_DIR)
    else:
        pdbs_dir = bench_dir

    for rpt in pdbs_dir.glob("*/*_protinfo.md"):
        md_fp = rpt_dir.joinpath(rpt.name)
        try:
            md_fp.symlink_to(rpt)
        except FileExistsError:
            continue

    return


def bench_job_setup(args: Namespace) -> None:
    """Benchmark cli function for sub-commands 1,2,3,4.
    Processing steps:
     - Create args.bench_dir/[runs/] subfolders.
     - Write fresh book file
     - Write script for args.job_name
    """
    in_dir_ok(args.bench_dir)

    if args.conf_making_level == 3:
        logger.warning(
            """
            The conformer-making level 3 ('full', 'comprehensive'), may lead to a segmentation
            fault if no other mcce options are tuned along.
            These other options are to be determined and are possibly protein specific.
            """
        )

    # Determine sentinel_file from sX_norun cli options;
    # default 'pK.out' may not be correct:
    sentinel_file = iou.sentinel_from_args(args)
    if sentinel_file is None:
        logger.critical("Could not determine sentinel_file from args :: batching or scheduling won't work.")
        sys.exit(1)
    
    # update
    args.sentinel_file = sentinel_file
    cli_opts.all["sentinel_file"] = sentinel_file

    if args.s.upper() == "ZAP":
        if float(args.salt) >= 0.05:
            args.salt = 0.05
            cli_opts.all["salt"] = 0.05
            logger.warning("Reset args.salt to 0.05 due to ZAP instability at a higher concentration.")

    if args.subparser_name == SUB4:
        job_setup.setup_user_runs(args)
    else:
        if args.pdbids_file:
            logger.info("Using args.pdbids_file.")
        # note: args.n_pdbs will stay set to default N_PDBS even with pdbids_file
        job_setup.setup_pkdb_runs(args.bench_dir, args.n_pdbs, args.pdbids_file,
                                  args.subparser_name, args.no_runsdir)

    # maybe link customized files into the prot subfolders:
    if args.load_runprm or args.u:
        args = job_setup.setup_customized_files(args)
        # reset saved args:
        cli_opts.all.update(vars(args))
        logger.info(f"Options after 'setup_customized_files':\n{cli_opts.all}")

    # determine if args are all defaults
    use_default_sh = custom_sh.all_opts_are_defaults(args)
    if use_default_sh:
        job_setup.write_default_run_script(args.bench_dir, subcmd=args.subparser_name,
                                           job_name=args.job_name, no_runsdir=args.no_runsdir)
    else:
        custom_sh.write_run_script_from_template(
            args.bench_dir, args.job_name, job_args=args
        )
        if args.no_runsdir:
            script_fp = args.bench_dir.joinpath(f"{args.job_name}.sh")
        else:
            script_fp = args.bench_dir.joinpath(RUNS_DIR, f"{args.job_name}.sh")
        sentinel_file = iou.get_sentinel(script_fp)
        # update
        args.sentinel_file = sentinel_file

    logger.info("Setup over.")

    if not args.launch:
        # write only once
        cli_opts.save_args(args)

    if not args.s1_norun:
        # run protinfo only if step1.py is to be run:
        logger.info("Starting prerun (time needed: 2 to 4 second/prot).")
        do_prerun(args)  # individual reports

        # collate all pdb reports:
        os.chdir(args.bench_dir)
        rpt_fp = Path(FILES.PRERUN_RPT.value)
        rpt_fp.write_text(f"---\n{cli_opts.all}")
        # collate with cat command:
        if args.no_runsdir:
            iou.subprocess_run(f"cat */*_protinfo.md > {rpt_fp!s}")
        else:
            iou.subprocess_run(f"cat {RUNS_DIR}/*/*_protinfo.md > {rpt_fp!s}")
        logger.info(
        f"""
        Prerun over.
        An individual report path is: '{args.bench_dir.name}/[runs/]<prot_dir>/<protid>_protinfo.md'.
        To display the collated report, run:
            cat {rpt_fp!s}
        """
        )
        os.chdir("../")
        # move prerun reports to bench_dir/prerun folder
        populate_prerun_folder(args.bench_dir, args.redo_prerun)

    if args.launch:
        logger.info("Launch flag on: Doing cron job scheduling now.")
        # need to add n_batch to the Namespace as if passed by launch cli:
        if not hasattr(args, "n_batch"):
            setattr(args, "n_batch", N_BATCH)
        cli_opts.save_args(args)

        bench_launch_batch(args)
    else:
        # create exceutable bash scripts to launch & analyze the runs:
        job_setup.create_next_commands(args)

    return


def bench_launch_batch(args: Namespace) -> None:
    """Benchmark cli function for 'launch' sub-command.
    PRE-REQS:
    args.bench_dir & subfolders, and script for args.job_name exist
    as previously created via 'bench_setup' command.
    """
    in_dir_ok(args.bench_dir)
    logger.info(cli_opts)

    # log script text again in case it was manualy modified.
    sh_name = f"{args.job_name}.sh"
    if args.no_runsdir:
        sh_path = iou.Pathok(args.bench_dir.joinpath(sh_name))
    else:
        sh_path = iou.Pathok(args.bench_dir.joinpath(RUNS_DIR, sh_name))

    if args.job_name != DEFAULT_JOB:
        steps_noruns = iou.sh_steps(sh_path)
        if all(steps_noruns.values()):
            msg = f"This script: {sh_path!s} has no 'stepx.py' command to run."
            logger.citical(msg)
            sys.exit(1)

        # update saved args in case script was modified:
        # get the sentinel file from the sX_noruns flags:
        sentinel = iou.get_sentinel(sh_path)
        if sentinel != args.sentinel_file:
            cli_opts.all.update({"prev_sentinel_file": args.sentinel_file,
                                 "sentinel_file": sentinel})
            cli_opts.all.update(steps_noruns)
            cli_opts.save_args()  # save cli_opts.all dict to file
            # update current:
            args.sentinel_file = sentinel
        
    logger.info(f"Script contents prior to launch:\n{sh_path.read_text()}\n")

    scheduling.schedule_job(args)

    return


def bench_parser():
    """Command line arguments parser with sub-commands for use in benchmarking."""
    npdbs_help = f"To return this number of smallest pdbs; Datasets size: {datasets_size_str}; default: {N_PDBS}"

    p = ArgumentParser(
        description=DESC,
        formatter_class=RawDescriptionHelpFormatter,
        fromfile_prefix_chars="@",
        epilog="""
        Post an issue for all errors and feature requests at:
        https://github.com/GunnerLab/MCCE4/issues
        """,
    )
    p.convert_arg_line_to_args = cliu.sh_split

    # COMMON parser: for SUB1:pkdb_pdbs and SUB2:user_pdbs subcmds
    cp = ArgumentParser(add_help=False)
    cp.add_argument(
        "-bench_dir",
        #required=True,
        default=".",
        type=cliu.arg_valid_dirpath,
        help="""The directory for setting up the benchmarking job(s); default: %(default)s""",
    )
    cp.add_argument(
        "-job_name",
        type=str,
        default=DEFAULT_JOB,
        help="""The descriptive name, without spaces, for the current job; required.
        This job_name is used to identify the shell script in 'bench_dir' that launches the MCCE simulation
        in 'bench_dir'/runs subfolders; default: %(default)s.
        """,
    )
    # sentinel_file (e.g. pK.out) is part of script setup to ensure it is deleted prior to using launch sub-command.
    cp.add_argument(
        "-sentinel_file",
        type=cliu.icase,
        default="pK.out",
        help="""File whose existence signals a completed step; When running all 4 MCCE steps (default),
        this file is 'pK.out', while when running only the first 2, this file is 'step2_out.pdb'; default: %(default)s.
        """,
    )
    # step1.py prot.pdb {wet}{noter}{d}{s1_norun}{u}{e}
    cp.add_argument(
        "--wet",
        default=False,
        action="store_true",
        help="Keep water molecules; %(default)s.",
    )
    cp.add_argument(
        "--noter",
        default=False,
        action="store_true",
        help="Do not label terminal residues (for making ftpl); %(default)s.",
    )
    # TODO Add warning if other keys are set & no load_runprm -> custom run.prm created
    # Common to all mcce steps: used for relinking customized EXTRA and RENAME_RULE files.
    # steps 1-3:
    cp.add_argument(
        "-d",
        metavar="epsilon",
        type=int,
        default=4,
        help="Protein dielectric constant; %(default)s.",
    )
    cp.add_argument(
        "-u",
        metavar="Key=Value",
        type=str,
        default="",
        help="""User selected, comma-separated KEY=var pairs from run.prm; e.g.: 
        -u H2O_SASCUTOFF=0.05,EXTRA=./extra.tpl; default: %(default)s.""",
    )
    # norun option for each steps:
    cp.add_argument(
        "--s1_norun",
        default=False,
        action="store_true",
        help="Create run.prm without running step 1; %(default)s.",
    )
    cp.add_argument(
        "--s2_norun",
        default=False,
        action="store_true",
        help="Create run.prm without running step 2; %(default)s.",
    )
    cp.add_argument(
        "--s3_norun",
        default=False,
        action="store_true",
        help="Create run.prm without running step 3; %(default)s.",
    )
    cp.add_argument(
        "--s4_norun",
        default=False,
        action="store_true",
        help="Create run.prm without running step 4; %(default)s.",
    )
    cp.add_argument(
        "-load_runprm",
        metavar="prm_file",
        default="",
        help="Load additional run.prm file, overwrite default values."
    )
    # step2.py {conf_making_level}{ftpl}{d}{s2_norun}{u}{load_runprm}
    cp.add_argument(
        "-conf_making_level",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Conformer level, 1: quick, 2: medium, 3: comprehensive; default: %(default)s.",
    )
    # steps 2 & 3:
    cp.add_argument(
        "-ftpl",
        metavar="ftpl folder",
        type=str,
        default="",
        help="Folder of ftpl topology files; default: <mcce exec>/param/.",
    )
    # {pound}step3.py {d}{c}{s}{t}{p}{ftpl}{salt}{refresh}{vdw_relax}{fly}
    #                 {skip_pb}{debug}{l}{u}{load_runprm}
    cp.add_argument(
        "-c",
        metavar=("start", "end"),
        type=int,
        default=[1, 99999],
        nargs=2,
        help="Starting and ending conformer; default: %(default)s.",
    )
    cp.add_argument(
        "-s",
        metavar="pbe_solver",
        type=str,
        choices=["delphi", "ngpb", "apbs", "zap", "template"],
        default="ngpb",
        help="PBE solver; default: %(default)s.",
    )
    cp.add_argument(
        "-t",
        metavar="tmp folder",
        default="/tmp",
        help="PBE solver temporary folder; default: %(default)s.",
    )
    cp.add_argument(
        "-p",
        metavar="processes",
        type=int,
        default=1,
        help="Number of processes to use; default: %(default)s.",
    )
    cp.add_argument(
        "-salt",
        metavar="salt concentration",
        type=float,
        default=0.15,
        help="Salt concentration in moles/L. Can be omitted with ZAP (automatically reset to 0.05); default: %(default)s.",
    )
    cp.add_argument(
        "-l",
        metavar="options file path",
        type=str,
        default="",
        help="Load command line options from a file; default: %(default)s.",
    )
    cp.add_argument(
        "-vdw_relax",
        metavar="vdw_R_relaxation",
        default=0,
        type=float,
        help="Relax vdw R parameter by +- specified value; default: %(default)s.",
        )
    cp.add_argument(
        "--skip_pb",
        default=False,
        action="store_true",
        help="Run vdw and torsion calculation only; default: %(default)s.",
    )
    cp.add_argument(
        "--refresh",
        default=False,
        action="store_true",
        help="Recreate *.opp and head3.lst from step2_out.pdb and *.raw files; default: %(default)s.",
    )
    cp.add_argument(
        "--fly",
        default=False,
        action="store_true",
        help="Do on-the-fly rxn0 calculation; default: %(default)s.",
    )
    cp.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Log debug information and keep pb solver tmp/ folder; default: %(default)s.",
    )
    # step4.py --xts {titr_type}{i}{interval}{n}{ms}{s4_norun}{e}{u}
    cp.add_argument(
        "-titr_type",
        metavar="ph or eh",
        type=str,
        default="ph",
        help="Titration type, pH or Eh; default: %(default)s.",
    )
    cp.add_argument(
        "-i",
        metavar="initial ph/eh",
        type=float,
        default=0.0,
        help="Initial pH/Eh of titration; default: %(default)s.",
    )
    cp.add_argument(
        "-interval",
        metavar="interval",
        type=float,
        default=1.0,
        help="Titration interval in pJ or mV; default: %(default)s.",
    )
    cp.add_argument(
        "-n",
        metavar="steps",
        type=int,
        default=15,
        help="number of steps of titration; default: %(default)s.",
    )
    cp.add_argument(
        "--ms",
        default=False,
        action="store_true",
        help="Enable microstates output, ms_out; default: %(default)s.",
    )
    cp.add_argument(
        "--launch",
        default=False,
        action="store_true",
        help="""Schedule the job right away with default n_batch 
        (no chance of inspecting <job_name>.sh!); default: %(default)s.""",
    )
    cp.add_argument(
        "--no_runsdir",
        default=False,
        action="store_true",
        help="""Setup proteins folder in bench_dir not in bench_dir/runs; default: %(default)s.""",
    )

    subparsers = p.add_subparsers(
        required=True,
        title=f"{CLI_NAME} sub-commands",
        dest="subparser_name",
        description="Sub-commands of MCCE benchmarking cli.",
    )

    # show pdbids
    sub0 = subparsers.add_parser(
        SUB0,
        help=HELP_0.format(CLI_NAME, SUB0),
        formatter_class=RawDescriptionHelpFormatter,
    )
    sub0.add_argument(
        "-kind",
        type=str,
        help=f"""The name the experimental dataset whose PDBIDs are to be listed;
        One of: [{', '.join(datasets_dict.keys())}].
        """,
    )
    sub0.add_argument(
        "-n_pdbs",
        default=N_PDBS,  # largest dataset
        type=int,
        help=npdbs_help,
    )
    sub0.set_defaults(func=do_pdbids)

    # pkdb_v1
    N1 = datasets_size[SUB1]
    sub1 = subparsers.add_parser(
        SUB1,
        help=HELP_1.format(CLI_NAME, SUB1, N1),
        formatter_class=RawDescriptionHelpFormatter,
        parents=[cp],
    )
    mutex1 = sub1.add_mutually_exclusive_group()
    mutex1.add_argument(
        "-n_pdbs",
        default=N1,
        type=int,
        help="The number of curated pdbs to setup for the benchmarking job; max=default: %(default)s.",
    )
    mutex1.add_argument(
        "-pdbids_file",
        default="",
        type=str,
        help="Use this file of pkDB pdbids as a dataset; default: %(default)s.",
    )
    sub1.add_argument(
        "--redo_prerun",
        default=False,
        action="store_true",
        help="Redo the pre-run report even if ProtInfo.md exists; default: %(default)s.",
    )
    sub1.set_defaults(func=bench_job_setup)

    # pkdb_vR
    N2 = datasets_size[SUB2]
    sub2 = subparsers.add_parser(
        SUB2,
        help=HELP_2.format(CLI_NAME, SUB2, N2),
        formatter_class=RawDescriptionHelpFormatter,
        parents=[cp],
    )
    mutex2 = sub2.add_mutually_exclusive_group()
    mutex2.add_argument(
        "-n_pdbs",
        default=N2,
        type=int,
        help="The number of curated pdbs to setup for the benchmarking job; max=default: %(default)s.",
    )
    mutex2.add_argument(
        "-pdbids_file",
        default="",
        type=str,
        help="Use this file of pkDB pdbids as a dataset; default: %(default)s.",
    )
    sub2.add_argument(
        "--redo_prerun",
        default=False,
        action="store_true",
        help="Redo the pre-run report even if ProtInfo.md exists; default: %(default)s.",
    )
    sub2.set_defaults(func=bench_job_setup)

    # pkdb_snase
    N3 = datasets_size[SUB3]
    sub3 = subparsers.add_parser(
        SUB3,
        help=HELP_3.format(CLI_NAME, SUB3, N3),
        formatter_class=RawDescriptionHelpFormatter,
        parents=[cp],
    )
    mutex3 = sub3.add_mutually_exclusive_group()
    mutex3.add_argument(
        "-n_pdbs",
        default=N3,
        type=int,
        help="The number of curated pdbs to setup for the benchmarking job; max=default: %(default)s.",
    )
    mutex3.add_argument(
        "-pdbids_file",
        default="",
        type=str,
        help="Use this file of pkDB pdbids as a dataset; default: %(default)s.",
    )
    sub3.add_argument(
        "--redo_prerun",
        default=False,
        action="store_true",
        help="Redo the pre-run report even if ProtInfo.md exists; default: %(default)s.",
    )
    sub3.set_defaults(func=bench_job_setup)

    # user_pdbs
    sub4 = subparsers.add_parser(
        SUB4,
        help=HELP_4.format(CLI_NAME, SUB4),
        formatter_class=RawDescriptionHelpFormatter,
        parents=[cp],
    )
    sub4.add_argument(
        "-pdbs_list",
        type=cliu.arg_valid_dir_or_file,
        help="""The path to a dir containing pdb files OR the path to a file listing 
        the pdbs file paths.""",
    )
    sub4.add_argument(
        "--redo_prerun",
        default=False,
        action="store_true",
        help="Redo the pre-run report even if ProtInfo.md exists; default: %(default)s.",
    )
    sub4.set_defaults(func=bench_job_setup)

    # launch
    sub5 = subparsers.add_parser(
        SUB5,
        help=HELP_5.format(CLI_NAME, SUB5),
        formatter_class=RawDescriptionHelpFormatter,
    )
    sub5.add_argument(
        "-bench_dir",
        required=True,
        type=cliu.arg_valid_dirpath,
        help="""The user's choice of directory for setting up the benchmarking job(s);
        The directory is created if it does not exists unless this cli is called within that directory.""",
    )
    sub5.add_argument(
        "-job_name",
        type=str,
        default=DEFAULT_JOB,
        help="""The descriptive name, devoid of spaces, for the current job (don't make it too long!); required.
        This job_name is used to identify the shell script in 'bench_dir' that launches the MCCE simulation
        in 'bench_dir'/RUNS_DIR subfolders; default: %(default)s.
        """,
    )
    sub5.add_argument(
        "-n_batch",
        type=int,
        default=N_BATCH,
        help="The number of jobs to keep launching; default: %(default)s.",
    )
    sub5.add_argument(
        "-sentinel_file",
        type=str,
        default="pK.out",
        help="""File whose existence signals a completed step; default: %(default)s.
        Note: Can be ignored: it is set/reset by the cli options or the script prior to launch.
        """,
    )
    sub5.add_argument(
        "--no_runsdir",
        default=False,
        action="store_true",
        help="""If proteins folders in bench_dir not in bench_dir/runs; default: %(default)s.""",
    )
    sub5.set_defaults(func=bench_launch_batch)

    return p


def bench_cli(argv=None):
    """
    Command line interface for MCCE benchmarking entry point 'bench_setup'.
    """
    cli_parser = bench_parser()
    args = cli_parser.parse_args(argv)
    
    in_dir_ok(args.bench_dir)

    cliu.write_default_setup_options_file(Path(META, FILES.SETUP_OPTIONS.value))

    cli_opts.all = vars(args)

    args.func(args)

    return


if __name__ == "__main__":
    bench_cli(sys.argv[:1])
