#!/usr/bin/env python3

"""
Module: scheduling.py

For automating the crontab creation for scheduling batch_submit every minute.
"""
from argparse import Namespace
from datetime import datetime
import logging
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Union

from mcce4.mcce_benchmark import USER_MCCE, CONDA_PATHS, USER_ENV, LAUNCHJOB, cli_opts
from mcce4.mcce_benchmark.io_utils import CRON_ID0, CRON_ID1
from mcce4.mcce_benchmark import mcce_env as mcenv


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


cron_id = datetime.now().strftime(format="%Y-%m-%d %H:%M:%S")


def create_single_crontab(args: Namespace, debug: bool = False) -> Union[None, str]:
    """
    Create a crontab entry without external 'cron.sh script'.
    The user env detected in __init__ is used: the conda env
    is activated in crontab.
    If debug: return crontab_text w/o creating the crontab.
    """
    if cli_opts.all is None:
        cli_opts.bench_dir = args.bench_dir
        cli_opts.args_fp = cli_opts.get_args_fp()
        cli_opts.all = cli_opts.load_args()

    pbes = cli_opts.all.get("s")
    if pbes is not None:
        pbes = pbes.upper()
    
    PATH_1 = (
        "PATH={}:{}:{}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
    )
    PATH_2 = (
        "PATH={}:{}:{}:{}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
    )
    SCHED = "* * * * * . {} && conda activate {} && {} -bench_dir {} -job_name {} -n_batch {} -sentinel_file {}"
    
    tools_dir = str(Path(LAUNCHJOB).parent)  # MCCE_bin/
    bdir = str(args.bench_dir)
 
    if pbes is None or pbes != "ZAP":
        conda_exe = mcenv.get_conda_exe(raise_err=True)
        conda_sh = mcenv.get_conda_sh(conda_exe)
        
        if len(CONDA_PATHS) == 1:
            conda = CONDA_PATHS[0]
            ct_text = PATH_1.format(conda, USER_MCCE, tools_dir)
        else:
            conda, conda_env = CONDA_PATHS
            ct_text = PATH_2.format(conda, conda_env, USER_MCCE, tools_dir)

        ct_text = ct_text + SCHED.format(
            conda_sh,  # for activate
            USER_ENV,
            LAUNCHJOB,
            bdir,
            args.job_name,
            args.n_batch,
            args.sentinel_file,
        )
    else:
        # zap
        conda_exe, conda_env_bin, conda_sh, oe_licence, oe_env = mcenv.get_zap_env()
        conda_path = str(Path(conda_exe).parent)
        zap_license = f"OE_LICENSE={oe_licence}\n"

        PATH = "PATH={}:{}:{}:{}:/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
        ct_text = zap_license + PATH.format(
            USER_MCCE, tools_dir, conda_path, conda_env_bin
        )

        SCHED = "* * * * * . {} && conda activate {} && {} -bench_dir {} -job_name {} -n_batch {} -sentinel_file {}"
        ct_text = ct_text + SCHED.format(
            conda_sh,
            oe_env,  # for activate
            LAUNCHJOB,
            bdir,
            args.job_name,
            args.n_batch,
            args.sentinel_file,
        )

    # cron.log has threading msg from mcce and with cron err if any; other log empty:
    # cron.log wiped out when all runs are complete with 2>, persists with 2>>
    crontab_txt = CRON_ID0.format(cron_id) \
                  + f"{ct_text} 2>> {bdir}/cron.log\n" \
                  + CRON_ID1.format(cron_id)

    logger.info(f"Crontab text:\n```\n{crontab_txt}```")

    if not debug:
        cron_in = Popen(["crontab", "-l"], stdout=PIPE)
        cur_crontab, _ = cron_in.communicate()

        if len(cur_crontab) and "PATH" in cur_crontab.decode('utf-8'):
            # add new
            crontab_txt = cur_crontab + "\n" + crontab_txt

        cron_out = Popen(["crontab", "-"], stdin=PIPE)
        cron_out.communicate(input=bytes(crontab_txt, "utf-8"))

        cli_opts.all.update({"cron_id": cron_id})
        cli_opts.save_args()

        return

    return crontab_txt


def schedule_job(launch_args: Namespace) -> None:
    """Create a contab entry for batch_submit.py with args from the
    `bench_setup launch` command.
    """
    create_single_crontab(launch_args)
    logger.info("Scheduled batch submission with crontab every minute.")

    return
