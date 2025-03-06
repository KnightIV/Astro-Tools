import os
import datetime
import gzip
import shutil
import multiprocessing as mp

import phoebe

LOCK = mp.Lock()

# region PHOEBE q-search
def printsync_log(msg: str, parent_dir: str, print_console=False):
    logPath = os.path.join(parent_dir, "q-solutions", ".log")
    with LOCK:
        with open(logPath, "a+") as logFile:
            logFile.write(f"[{datetime.datetime.now()}] {msg}\n")
        
        if print_console:
            print(f"[{os.getpid()}][{datetime.datetime.now()}] {msg}")
               
def load_bundle(path: str) -> phoebe.Bundle:
    print(f"Reading in bundle from {path}")

    b: phoebe.Bundle
    jsonBundlePath = path
    if path.endswith('.gz'):
        jsonBundlePath = path.replace('.gz', '')
        with gzip.open(path, 'rb') as f_in:
            with open(jsonBundlePath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    b = phoebe.load(jsonBundlePath)
    if jsonBundlePath != path: os.remove(jsonBundlePath) # used temp file
    return b

def optimize_q(b: phoebe.Bundle, q: float, solution_directory: str) -> str:
    """
    Runs the solver `opt_q_search` given the fixed `q` value. Places the resulting solution in `solution_directory/{q}.sol`.
    The solution's comments contains the given `q` value as well as the calculated `chi2` of the adopted solution's model.
    """
    solution = "opt_q_search_solution"
    exportSolPath = os.path.join(solution_directory, f"{q:.4f}.sol")
    if os.path.exists(exportSolPath):
        printsync_log(f"{q} already solved", print_console=True)
        return
    b.set_value(qualifier='q', value=q)
    b.run_solver(solver="opt_q_search", solution=solution, overwrite=True)
    b.adopt_solution(solution)
    b.run_compute(model='q_solution_model')
    b.set_value(qualifier='comments', solution=solution, value=f"{q}|{b.calculate_chi2(model='q_solution_model')}")
    return b.filter(context='solution', solution=solution, check_visible=False).save(exportSolPath, incl_uniqueid=True);
# endregion