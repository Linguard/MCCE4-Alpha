#!/usr/bin/env python3

"""
Module: io_utils

Module with generic (enough) functions related to loading and saving files.
"""
import argparse
import logging
from pathlib import Path
import pickle
from typing import Any, List, Tuple, Union
import shutil
from subprocess import Popen, PIPE

import pandas as pd

from mcce4.mcce_benchmark import RUNS_DIR, USER, Opts
from mcce4.io_utils import subprocess_run, CalledProcessError
from mcce4.mcce_benchmark import FILES


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


# delimiter of one cron job:
CRON_ID0 = "#>>>{}\n"
CRON_ID1 = "#<<<{}\n"


def excise_delimited_content(text: str, tag1: str, tag2: str) -> Union[str, None]:
    """Excise the content between two string tags in a text.
    Args:
      text: A text.
      tag1: The first tag.
      tag2: The second tag.

    Returns:
      None if tag1 or tag2 is not found.
      A string without the tags and the content between them if both found;
    """
    try:
        pos1 = text.find(tag1)
        if pos1 == -1:
            return None
    except (AttributeError, ValueError):
        return None

    try:
        pos2 = text.find(tag2, pos1)
        if pos2 == -1:
            return None
    except (AttributeError, ValueError):
        return None
  
    end_pos = pos2 + len(tag2)
    return text[:pos1] + text[end_pos:]


def clear_crontab(cron_id: str):
    """Remove existing crontab with given cron_id.
    """
    start = CRON_ID0.format(cron_id)
    end = CRON_ID1.format(cron_id)

    cron_in = Popen(["crontab", "-l"], stdout=PIPE)
    cur_crontab, _ = cron_in.communicate()
    cur_crontab_txt = cur_crontab.decode('utf-8')
    if cur_crontab_txt.startswith("no crontab"):
        return
    
    # remove portion of txt from start to end delimiters:
    excised_txt = excise_delimited_content(cur_crontab_txt, start, end)
    if excised_txt is None:
        logger.info("Could not find a cron job with id '%s' to remove.", cron_id)
        return

    excised_txt = excised_txt.strip()
    if not excised_txt:
        # there was only 1 cron job: nothing to save, just remove:    
        out = subprocess_run(f"crontab -u {USER} -r")
        if isinstance(out, CalledProcessError):
            logger.error(f"Error clearing crontab cmd: {out}")
        return

    cron_out = Popen(["crontab", "-"], stdin=PIPE)
    cron_out.communicate(input=bytes(excised_txt, "utf-8"))

    return


def get_book_entries(book_fp: Path) -> list:
    """Extract the pdbs ids in book_fp into a list.
    """
    pdbs = []
    with open(book_fp) as fh:
        for line in fh:
            rawtxt = line.strip().split("#")[0]
            if not rawtxt:
                continue
            pdbs.append(rawtxt.split()[0])

    return pdbs


def Pathok(
    pathname: str, check_fn: str = "exists", raise_err=True
) -> Union[Path, bool]:
    """Return path if check passed, else raise error.
    check_fn: one of 'exists', 'is_dir', 'is_file'.
    if raise_err=False, return False instead of err.
    """

    pathname = Path(pathname)
    if check_fn not in ["exists", "is_dir", "is_file"]:
        check_fn = "exists"

    # failure msg:
    if check_fn == "exists":
        msg = f"Path not found: {pathname}"
    elif check_fn == "is_dir":
        msg = f"Directory not found: {pathname}"
    elif check_fn == "is_file":
        msg = f"Path is not a file: {pathname}"

    if not pathname.__getattribute__(check_fn)():
        if not raise_err:
            return False
        raise FileNotFoundError(msg)

    return pathname


def pct_completed(book_fpath: str) -> Union[float, None]:
    """Return the pct of runs that are completed or finished with error."""
    book_fp = Pathok(book_fpath)
    # 2 cmds: n processed; total count => 2 lines, e.g.:
    # 1
    # 6
    cmd = f"grep '[ce]' {book_fp} | wc -l; cat {book_fp} | wc -l"
    logger.info(f"{cmd = }")
    data = subprocess_run(cmd)

    if isinstance(data, CalledProcessError):
        logger.error("Error fetching pct completed.")
        return None

    if not data.stdout.strip():
        logger.error("No data from book file.")
        return None

    logger.info(f"{data.stdout = }")

    out = data.stdout.splitlines()
    logger.info(f"out = data.stdout.splitlines() :: {out = }")
    try:
        n = int(out[0])
        logger.info(f"{n = }")
    except ValueError:
        logger.error("No completed count from book file.")
        return None
    try:
        tot = int(out[1])
        logger.info(f"{tot = }")
    except ValueError:
        logger.error("No line count from book file.")
        return None

    pct = n / tot
    logger.info(f"pct processed: {pct:.1%}")

    return pct


def make_executable(sh_path: str) -> None:
    """Alternative to os.chmod(sh_path, stat.S_IXUSR): permission denied."""

    sh_path = Pathok(sh_path)
    cmd = f"chmod +x {str(sh_path)}"

    p = subprocess_run(cmd, capture_output=False, check=True)
    if isinstance(p, CalledProcessError):
        logger.exception(f"Error in subprocess cmd 'chmod +x':\nException: {p}")
        raise

    return


def df_to_txt(df: pd.DataFrame, fpath: str, replace: bool = True):
    """Save a pandas.DataFrame as a text file."""
    fp = Path(fpath)
    if fp.exists():
        if not replace:
            logger.error(f"File already exists: {fp}; {replace = }")
            return None
        fp.unlink()
    fp.write_text(df.to_string(index=False) + "\n")


def txt_to_df(fp: Path, header=None) -> pd.DataFrame:
    """Load a fixed-width file into a pandas.DataFrame."""
    return pd.read_fwf(fp, header=header)


# aliases
df2txt = df_to_txt
txt2df = txt_to_df


def get_file_header(fp: str) -> str:
    hdr = ""
    with open(fp) as f:
        for i, line in enumerate(f):
            if i > 0:
                break
            hdr = line

    return hdr


def get_book_dirs_for_status(book_fpath: str, status: str = "c") -> list:
    """Return a list of folder names from book_fp, the BOOK file path,
    if their status codes match a 'completion status', i.e. completed ('c', default),
    or errorneous ('e').
    """

    status = status.lower()
    if not status or status not in ["c", "e"]:
        logger.error("Invalid 'status'; choices are 'c' or 'e'.")
        raise ValueError("Invalid 'status'; choices are 'c' or 'e'.")

    book_fp = Pathok(book_fpath)
    book_dirs = []
    with open(book_fp) as book:
        for line in book:
            # select the portion preceding any appended comment
            rawtxt = line.strip().split("#")[0]
            fields = rawtxt.split()
            if len(fields) == 2:
                if fields[1].lower() == status:
                    book_dirs.append(fields[0])

    return book_dirs


def to_pickle(obj: Any, fp: str):
    pickle.dump(obj, open(fp, "wb"))
    return


def from_pickle(fp: str) -> Any:
    obj = pickle.load(open(fp, "rb"))
    return obj


def matched_pks_to_df(matched_fp: str) -> pd.DataFrame:
    """
    Load MATCHED_PKAS file into a pandas DataFrame.
    PRE: file MATCHED_PKAS file created via mcce_benchmark.pkanalysis.
    Columns: resid; <set1 pk>; <set2 pk>. The last 2 columns are
    dynamically named.
    """
    fp = Path(matched_fp)
    fname = FILES.MATCHED_PKAS_TXT.value
    if fp.name != fname:
        logger.error(f"Only {fname} is a valid file name.")
        raise ValueError(f"Only {fname} is a valid file name.")

    if not fp.exists():
        logger.error(f"Not found: {fp}; run pkanalysis to create.")
        raise FileNotFoundError(f"Not found: {fp}; run pkanalysis to create.")

    return txt2df(fp, header=0)


# 1 :: aka quick
levels2names = {1: "isosteric", 2: "medium", 3: "comprehensive"}


def get_level_tup(level: Union[int, Tuple[int, int]] = None) -> Tuple:
    """
    Returns one 2-tuple for bench_analyze, two 2-tuples for bench_compare.
    """
    if level is None:
        return (None, "unknown")

    if isinstance(level, int):
        lev = levels2names.get(level)
        return (None, "unknown") if lev is None else (level, lev)

    if isinstance(level, tuple):
        l1, l2 = level
        lev1 = levels2names.get(l1)
        lt1 = (None, "unknown") if lev1 is None else (l1, lev1)
        lev2 = levels2names.get(l2)
        lt2 = (None, "unknown") if lev2 is None else (l2, lev2)
        return lt1, lt2


def sentinel_from_args(args: Union[argparse.Namespace, dict]) -> Union[str, None]:
    if isinstance(args, dict):
        args = argparse.Namespace(**args)

    if args.s4_norun:
        if args.s3_norun:
            if args.s2_norun:
                if args.s1_norun:
                    # cannot have args.s1_norun as there is no sentinel_file
                    # associated with "run no steps":
                    sentinel = None
                else:
                    sentinel = "step1_out.pdb"
            else:
                sentinel = "step2_out.pdb"
        else:
            sentinel = "head3.lst"
    else:
        sentinel = "pK.out"

    return sentinel


def sh_steps(script_fp: Path) -> dict:
    """Recover the values for the --sx_norun options for each steps in the run script.
    Only mcce steps 1 through 4 are considered.
    """
    sh_lines = [
    line.strip()
    for line in script_fp.read_text().splitlines()[1:-1]
    if line.strip()
    ]
    sh_d = {}  # will need to have 4 keys
    seen = set()
    for line in sh_lines:
        try:
            str1, str2 = line.split("#")
            commented = True
        except ValueError:
            # No hash in line:
            str2 = line
            commented = False
        finally:
            idx = str2.find("step")
            if idx == -1:  # not a step line
                continue

            s = str2[idx : idx + 5][-1]
            if s not in "1234":
                continue
            seen.add(s)
            if "norun" in line or commented:
                sh_d[f"s{s}_norun"] = True
            else:
                sh_d[f"s{s}_norun"] = False

    if len(seen) != 4:
        missing = set("1234").difference(seen)
        for m in missing:
            print("missing, m:", m)
            sh_d[f"s{m}_norun"] = True

    return sh_d


def get_sentinel(script_fp: Path) -> Union[str, None]:
    """Return the name of the sentinel_file from the custom script path.
    """
    runsh_steps = sh_steps(script_fp)
    sentinel = sentinel_from_args(runsh_steps)

    return sentinel


MCCE_OUTPUTS = [
    "acc.atm",
    "acc.res",
    "entropy.out",
    "fort.38",
    "head1.lst",
    "head2.lst",
    "head3.lst",
    "mc_out",
    "new.tpl",
    "null",
    "pK.out",
    "progress.log",
    "respair.lst",
    "rot_stat",
    "run.log",
    #"run.prm",
    #"run.prm.record",
    "step0_out.pdb",
    "step1_out.pdb",
    "step2_out.pdb",
    "sum_crg.out",
    "vdw0.lst",
]

def get_setup_args_vals(dirpath: Path, option: Union[str, List[str]]) -> list:
    """Retrieve one or more values from the saved cli args.
    Args:
     - dirpath (Path): benchmark dir path
     - option (str, list): A single cli option, if type is string, or multiple options to get
       from the file.
    """
    out = []
    is_string = isinstance(option, str)

    # get val from saved setup args:
    cliopts = Opts(dirpath)
    # setup_args_fp = Path(dirpath).joinpath(FILES.CLI_ARGS_PKL.value)
    # if not setup_args_fp.exists():
    #     logger.warning("Saved setup args file not found.")
    #     return out

    # # unpickle the Namespace instance:
    # setup_d = vars(from_pickle(setup_args_fp))
    if is_string:
        # out = [setup_d.get(option)]
        out = [cliopts.all.get(option)]
    elif isinstance(option, list):
        # out = [setup_d.get(opt) for opt in option]
        out = [cliopts.all.get(opt) for opt in option]

    return out


def delete_mcce_outputs(
    mcce_dir: str, files_to_keep: list = None, del_original_pdb: bool = True
) -> None:
    """Delete all MCCE output files or folders from a MCCE run folder;
    Only keep files in files_to_keep if not None.
    Note: All subfolders within `mcce_dir` are automatically deleted.
    """
    folder = Path(mcce_dir)
    if not folder.is_dir():
        print(f"{folder = } does not exist.")
        return

    if files_to_keep is None:
        check_list = MCCE_OUTPUTS
    else:
        # deletion list:
        check_list = list(
            set(files_to_keep).symmetric_difference(set(MCCE_OUTPUTS + ["prot.pdb"]))
        )

    for fp in folder.iterdir():
        if fp.is_dir():
            shutil.rmtree(fp)
        else:
            if fp.name in check_list:
                fp.unlink()
            else:
                if del_original_pdb:
                    # delete original pdb file:
                    if (
                        fp.name == f"{folder.name.lower()}.pdb"
                        or (fp.name.startswith(f"{folder.name.lower()}_")
                            and fp.suffix == ".pdb"
                            )
                        ):
                        fp.unlink()
    return


def prep_refset(
    bench_dir: str, keep_files: list = None, del_original_pdb: bool = True
) -> None:
    """
    ASSUME 'standard' structure: <bench_dir>/RUNS_DIR, which is a folder of folders
    named after the pdb id they contain, i.e. <bench_dir>/runs/.
    Delete all MCCE output files that are not in the 'keep_files' list.
    Delete all mcce subfolders.
    """
    pdbs = Path(bench_dir) / RUNS_DIR
    if not pdbs.exists():
        raise FileNotFoundError(f"Not found: {pdbs}")

    for fp in pdbs.iterdir():
        if fp.is_dir():
            delete_mcce_outputs(
                fp, files_to_keep=keep_files, del_original_pdb=del_original_pdb
            )
        else:
            print(f"{fp = }: remaining")

    return


def clean_job_folder(job_dir: str) -> None:
    """Delete all MCCE output files and folders from a directory `job_dir`,
    which is a folder of folders named after the pdb id they contain, i.e. like runs/.
    """
    pdbs_dir = Path(job_dir)
    for fp in pdbs_dir.iterdir():
        if fp.is_dir():
            delete_mcce_outputs(fp)
        else:
            print(f"{fp = }: remaining")

    return


def clear_folder(
    dir_path: str,
    file_type: str = None,
    del_subdir: bool = False,
    del_subdir_begin: str = None,
) -> None:
    """Delete all files in folder.
    Only delete subfolders if `del_subdir` is True and the subdir
    name starts with `del_subdir_begin` if non-zero length str.
    Note: `del_subdir_begin` must neither be None or "" if `del_subdir`
    is True.
    """
    # validate del_subdir_begin:
    if del_subdir:
        if del_subdir_begin is None or not del_subdir_begin == 0:
            del_subdir = False

    p = Path(dir_path)
    if not p.is_dir():
        # no folder, nothing to clear
        return

    if file_type is None:
        for f in p.iterdir():
            if not f.is_dir():
                f.unlink()
            else:
                if del_subdir and f.name.startswith(del_subdir_begin):
                    shutil.rmtree(str(f))
    else:
        if file_type.startswith("."):
            fname = f"*{file_type}"
        else:
            fname = f"*.{file_type}"

        for f in p.glob(fname):
            f.unlink()
    return
