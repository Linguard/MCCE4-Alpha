#!/usr/bin/env python3

"""
Module: __ini__.py

Init module of mcce_benchmark.
"""
from argparse import Namespace
from datetime import datetime
from enum import Enum
import getpass
from importlib import resources
import logging
from pathlib import Path
import pickle
from pprint import pformat
from shutil import move, which
import sys
from typing import Union

import pandas as pd


# TODO: To discuss whether this should rather be a setting in
# a scheduling script:
# # set virtual cores for NumExpr
# # 64 == default, max virtual cores in NumExpr:
# os.environ['NUMEXPR_MAX_THREADS'] = "64"
# os.environ['NUMEXPR_NUM_THREADS'] = "32"


APP_NAME = "mcce4.mcce_benchmark"
META = "meta_bench"   # for ancillary files


# fail fast:
USER_MCCE = which("mcce")
if USER_MCCE is None:
    #raise EnvironmentError(f"{APP_NAME}, init :: mcce executable not found.")
    sys.exit(f"EnvironmentError - {APP_NAME}, init :: mcce executable not found.")

USER_MCCE = Path(USER_MCCE).parent


def get_user_env() -> str:
    """Return the env name from sys.prefix.
    """
    user_prefix = sys.prefix
    if user_prefix == "/usr":
        # no conda env activated
        env = ""
    else:
        env = Path(user_prefix).name
        if "envs" not in user_prefix:
            if not env.endswith("conda3"):
                # /home/user/*conda3 if base
                raise EnvironmentError(
                    "You appear not to be using conda, which is required for scheduling."
                )
            else:
                env = "base"

    return env


def get_conda_paths() -> tuple:
    """Return the path to conda that is not in an env,
    which is what cron 'sees', presumably.
    Needed to build cmd 'source <conda_path>/activate <env>' in crontab.
    Try: need both bin and condabin to put in path?"""

    if which("conda") is None:
        print("WARNING: Conda is required for scheduling but not found.")
        return None, None
    
    conda_path = Path(which("conda")).parent
    if conda_path.name == "bin":
        # done
        return (str(conda_path),)
    # else, assume "condabin", reset:
    return str(conda_path.parent.joinpath("bin")), str(conda_path)


USER = getpass.getuser()
# user envir:
USER_ENV = get_user_env()
# CONDA_PATH = Path(shutil.which("conda")).parent
CONDA_PATHS = get_conda_paths()

info = {"DATE": datetime.now().strftime(format="%Y-%m-%d %H:%M:%S"),
        "USER": USER,
        "USER_MCCE": USER_MCCE,
        "USER_ENV": USER_ENV,
        "CONDA_PATHS": CONDA_PATHS,
}

ENTRY_POINTS = {
    "setup": "bench_setup",
    "launch": "bench_batch",  # used by crontab :: launch 1 batch of size 10
    "analyze": "bench_analyze",
    "compare": "bench_compare",
}


# bench_setup sub-commands; sub-commands SUB1, SUB2, SUB3 are the datasets folder names:
SUB0 = "pdbids"
SUB1 = "pkdb_v1"
SUB2 = "pkdb_vR"
SUB3 = "pkdb_snase"
SUB4 = "user_pdbs"
SUB5 = "launch" # :: crontab job scheduler step of setup.


# full path of the launch EP for scheduling:
LAUNCHJOB = which(ENTRY_POINTS[SUB5])
DELTA = "\u0394"


class FILES(Enum):
    """Output file names; _PKL => dict to .pickle"""
    SETUP_OPTIONS = "bench_setup_options.txt"
    # TODO: deprecate .pickle files
    # Next 2: bench setup cli args, saved at the same time;
    # if benchmark.log is deleted, the text file provides
    # the setup options in readeable form, while the pickle
    # file is used by analysis and comparison modules.
    CLI_ARGS_TXT = "cli_args.txt"
    PRERUN_RPT = "prerun_report.md"
    # Analysis files
    ALL_SUMCRG = "all_sum_crg.out"
    ALL_SUMCRG_TXT = "all_sum_crg.out.txt"
    ALL_SUMCRG_DIFF = "all_sumcrg_diff.txt"
    ALL_PKAS = "all_pK.out"
    ALL_PKAS_TXT = "all_pK.out.txt"
    ALL_PKAS_OOB = "all_pkas_oob.txt"  # out of bounds pKas
    JOB_PKAS_PKL = "job_pkas.pickle"    
    MATCHED_PKAS_TXT = "matched_pkas.txt"
    MATCHED_PKAS_STATS_PKL = "matched_pkas_stats.pickle"
    MATCHED_PKAS_STATS = "matched_pkas_stats.txt"  # saved pka_stats_dict["report"]
    RESIDUES_STATS = "residues_stats.txt"
    RESIDUES_STATS_PKL = "residues_stats.pickle"
    CONF_COUNTS = "conf_counts.txt"
    CONFS_PER_RES = "confs_per_res.txt"
    CONFS_THRUPUT = "confs_throughput.txt"
    RES_COUNTS = "res_counts.txt"
    RES_OUTLIER = "outlier_residues.txt"
    RESID_OUTLIER = "outlier_resids.txt"
    RUN_TIMES = "run_times.txt"
    FIG_CONFS_TP = "confs_throughput.png"
    FIG_FIT_ALLPKS = "pkas_fit.png"
    FIG_FIT_PER_RES = "res_analysis.png"
    VERSIONS = "versions.txt"


# dataset-specific pdb count is now in BenchResources
N_PDBS = 145   # : default value, size of the largest dataset, pkdb_vR 

RUNS_DIR = "runs"
ANALYZE_DIR = "analysis"
MCCE_EPS = 4  # default dielectric constant (epsilon) in MCCE
N_BATCH = 10  # number of jobs to maintain in the process queue
DEFAULT_JOB = "default_run"
DEFAULT_JOB_SH = f"{DEFAULT_JOB}.sh"
BOOK = "book.txt"
BENCH_DATA = resources.files(f"{APP_NAME}.data")


# Config for root logger:
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class BenchResources:
    """Class to store package data paths and main constants for a selected dataset."""

    def __init__(self, dataset: str, data_dir=BENCH_DATA):
        # # check given dataset corresponds to an existing folder:
        # if not data_dir.joinpath(dataset).is_dir():
        #     sys.exit(f"Dataset: {dataset!r} is not setup.")
        if dataset in [SUB1, SUB2, SUB3]:
            self.BENCH_DATA = data_dir
            self.BENCH_DB = self.BENCH_DATA.joinpath(dataset)
            self.BENCH_WT = self.BENCH_DB.joinpath("pkas.csv")
            self.BENCH_PROTS = self.BENCH_DB.joinpath("proteins.tsv")
            self.N_PDBS = self.proteins_df(return_excluded=False).shape[0]
            self.BENCH_PDBS = self.BENCH_DB.joinpath(RUNS_DIR)
            self.DEFAULT_JOB_SH = self.BENCH_DB.joinpath(DEFAULT_JOB_SH)        
            self.BENCH_Q_BOOK = self.BENCH_PDBS.joinpath(BOOK)
            if dataset == "pkdb_v1":
                self.BENCH_PH_REFS = self.BENCH_DB.joinpath("refsets")
                self.BENCH_PARSE_PHE4 = self.BENCH_PH_REFS.joinpath("parse.e4")
        return

    def proteins_df(self, return_excluded: bool = None) -> pd.DataFrame:
        """
        Load <pkadb>/proteins.tsv into a pandas.DataFrame.
        Args:
        return_excluded (bool, None):
          - If None: return entire set;
          - If True: return df of excluded proteins;
          - If False, return the active entries proteins
        """
        df = pd.read_csv(self.BENCH_PROTS, sep="\t")
        df.sort_values(by="PDB", inplace=True)
        if return_excluded is None:
            return df
        msk = df.PDB.str.startswith("#")
        if return_excluded:
            return df[msk]
        else:
            return df[~msk]

    def __str__(self):
        return f"""
        BENCH_DATA     = {str(self.BENCH_DATA)}
        BENCH_DB       = {str(self.BENCH_DB)}
        BENCH_WT       = {str(self.BENCH_WT)}
        BENCH_PROTS    = {str(self.BENCH_PROTS)}
        BENCH_PDBS     = {str(self.BENCH_PDBS)}
        DEFAULT_JOB_SH = {str(self.DEFAULT_JOB_SH)}
        BENCH_Q_BOOK   = {str(self.BENCH_Q_BOOK)}
        N_PDBS = {self.N_PDBS}
        """


datasets_dict = dict((d.name, d) for d in BENCH_DATA.glob("pkdb_*"))
datasets_size = dict((k, BenchResources(k).N_PDBS) for k in datasets_dict)


class Opts:
    def __init__(self, bench_dir: str = None, cli_name: str = None, d_args: dict = None):
        """Class Opts makes command line options available to all objects.
        Arguments:
        ---------
        bench_dir : str
           path of the benchmark directory
        cli_name : str
            name of the command line tool or subcommand.
        d_args : dict
            cli args (Namespace) given as vars(args).
        """
        self.bench_dir = Path(bench_dir) if bench_dir else Path.cwd()
        self.args_fp = self.get_args_fp()
        self.cli_name = cli_name
        self.info = None

        self.move_old_files()

        if d_args is None:
            # Load from existing arg file:
            self.all = self.load_args()
        else:
            self.all = d_args

        return

    def get_args_fp(self) -> Path:
        """To obtain the path to args_fp in case the bench_dir attribute is changed
        on an instance.
        """
        self.bench_dir.joinpath(META).mkdir(exist_ok=True)
        return self.bench_dir.joinpath(META, FILES.CLI_ARGS_TXT.value)

    def load_args(self) -> Union[dict, None]:
        """
        Load 'cli_args.txt' into a dict.
        """
        if not self.args_fp.exists():
            logger.info("No saved options file found.")
            return None
        
        d = {}
        # exclude comment on 1st line:
        args_lines = self.args_fp.read_text().splitlines()[1:]
        for line in args_lines:
            line = line.strip()
            if not line:
                continue
            k, v = line.split(":", maxsplit=1)
            k, v = k.strip(), v.strip()
            d[k] = v
            
        if not d:
            logger.error(f"Could not load {self.args_fp!s} into a dict.")
            d = None

        return d

    def move_old_files(self):
        # move these to META:
        fp = self.bench_dir.joinpath(FILES.CLI_ARGS_TXT.value)
        if fp.exists():
            dest = self.bench_dir.joinpath(META, fp.with_suffix(".old").name)
            move(fp, dest)

        existing = list(self.bench_dir.glob("PDBIDS_*"))
        if existing:
            # take 1st, there should only be one:
            move(existing[0], self.bench_dir.joinpath(META))

        return

    def extract_info(self) -> tuple:
        """
        Extract DATE, USER from line 4, USER_MCCE from line 7 of benchmark.info
        if found.
        Return a 3-tuple: date, user, user_mcce or None, None, None
        """
        info_fp = Path("benchmark.info")
        if not info_fp.exists():
            return None, None, None
 
        lines = info_fp.read_text().splitlines()[:7]
        date_str, user_str = lines[3].split(" - ")
        uname = user_str.split(" = ")[1].strip("'")
        umcce = lines[-1].split(" :: ")[0].split(" = ")[1][:-1].split("PosixPath(")[1].strip("'")
        info_fp.unlink()

        return date_str, uname, umcce
    
    def convert_pkl_args(self):
        """Convert the pickled argparse.Namespace to cli_args.txt new format.
        """
        pkl_fp = self.bench_dir.joinpath("cli_args.pickle")
        if not pkl_fp.exists():
            return
        try:
            obj = pickle.loads(pkl_fp.read_bytes())
        except pickle.UnpicklingError:
            logger.warning("Could not unpickle the cli args.")
            return
        setup_d = vars(obj)
        # perhaps add missing new key:
        if setup_d.get("no_runsdir") is None:
            val = f"{not pkl_fp.parent.joinpath(RUNS_DIR).is_dir()!s}"
            setup_d.update({'no_runsdir': val})
        
        info0 = {}
        run_date, run_user, run_mcce = self.extract_info()

        info0["DATE"] = run_date if run_date else info["DATE"]
        info0["USER"] = run_user if run_user else info["USER"]
        info0["USER_MCCE"] = run_mcce if run_mcce else info["USER_MCCE"]
        # from current call:
        info0["USER_ENV"] = USER_ENV
        info0["CONDA_PATHS"] = CONDA_PATHS

        self.info = info0

        given_all = None
        if self.all is None:
            self.all = setup_d
        else:
            # save
            given_all = self.all
            given_cli_name = self.cli_name
            self.all = setup_d

        self.to_file(self.args_fp)
        logger.info(f"Converted cli_args.pickle to {META}/cli_args.txt")
        if given_all is not None:
            # restore:
            self.all = given_all
            self.cli_name = given_cli_name
        # else:
        #     self.all = None
        #     self.cli_name = None
        self.info = None
        # move
        move(pkl_fp, self.bench_dir.joinpath(META, pkl_fp.with_suffix(".pickle.old")))
        
        return

    def to_file(self, fp: Path):
        fp.write_text(str(self))

        return

    def save_args(self, d: Union[dict, Namespace] = None):
        """
        Update self.all with dict if not None, then save to file.
        Note: d should be None when self.all was updated directly.
        """
        if d is not None:
            if isinstance(d, Namespace):
                d = vars(d)
            if self.all is None:
                self.all = d
            else:
                self.all.update(d)
        if self.all is None:
            return

        self.args_fp.write_text(str(self))

        return

    def __str__(self):
        if not self.all:
            return "# No options loaded!\n"
        if self.info is None:
            self.info = info
        if self.all.get("func") is not None:
            if not isinstance(self.all["func"], str):
                self.all["func"] = self.all["func"].__name__

        all_args = {**self.info, **self.all}
        clean = ""
        hdr = "# IMPORTANT: If modifications are made to this file, keep the dict format: key: value!\n"
        # exclude opening and closing curly braces:
        out = pformat(all_args, indent=0, sort_dicts=False, width=150)[1:-1]
        # remove trailing comma & quotes
        for line in out.splitlines():
            line = line[:-1] if line.endswith(",") else line
            line = line.replace("'", "").replace('"', "")
            clean = clean + line + "\n"
        out = hdr + clean

        return out


cli_opts = Opts()
# if done in class __init__: error due to circular import (?)
cli_opts.convert_pkl_args()


# LOG_HDR = f"""
# START\n{'-'*70}\n{datetime.now().strftime(format="%Y-%m-%d %H:%M:%S")} - {USER = }
# APP DEFAULTS:
# Globals:
# {USER_MCCE = } :: mcce executable in use
# {MCCE_EPS = } :: default protein epsilon
# {N_BATCH = } :: default batch size for job submission
# Saved setup options:
#   CLI_ARGS_TXT: {FILES.CLI_ARGS_TXT.value}
# Default analysis output file names (fixed):
#   VERSIONS: {FILES.VERSIONS.value}
#   RUN_TIMES: {FILES.RUN_TIMES.value}
#   ALL_PKAS: {FILES.ALL_PKAS.value}
#   ALL_SUMCRG: {FILES.ALL_SUMCRG.value}
#   ALL_SUMCRG_DIFF: {FILES.ALL_SUMCRG_DIFF.value}
#   ALL_PKAS_OOB: {FILES.ALL_PKAS_OOB.value}
#   CONF_COUNTS: {FILES.CONF_COUNTS.value}
#   RES_COUNTS: {FILES.RES_COUNTS.value}
#   CONFS_PER_RES: {FILES.CONFS_PER_RES.value}
#   CONFS_THRUPUT: {FILES.CONFS_THRUPUT.value}
#   FIG_CONFS_TP: {FILES.FIG_CONFS_TP.value}
#   JOB_PKAS_PKL: {FILES.JOB_PKAS_PKL.value}
#   MATCHED_PKAS_TXT: {FILES.MATCHED_PKAS_TXT.value}
#   MATCHED_PKAS_STATS_PKL: {FILES.MATCHED_PKAS_STATS_PKL.value}
#   MATCHED_PKAS_STATS: {FILES.MATCHED_PKAS_STATS.value}
#   RESIDUES_STATS: {FILES.RESIDUES_STATS.value}
#   RESIDUES_STATS_PKL: {FILES.RESIDUES_STATS_PKL.value}
#   RES_OUTLIER = {FILES.RES_OUTLIER.value}
#   RESID_OUTLIER = {FILES.RESID_OUTLIER.value}
#   FIG_FIT_ALLPKS = {FILES.FIG_FIT_ALLPKS .value}
#   FIG_FIT_PER_RES = {FILES.FIG_FIT_PER_RES.value}
# \n{'-'*70}\n
# """

# info_fp = Path("benchmark.info")
# if not info_fp.exists():
#     info_fp.write_text(LOG_HDR)
