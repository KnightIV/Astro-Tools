import os
import multiprocessing as mp

import tqdm

import phoebe
from phoebe import u
phoebe.progressbars_off()
logger = phoebe.logger(clevel='WARNING')
logger.setLevel(200)

import utils

import argparse
parser = argparse.ArgumentParser("q-search", 
                                description="Run a q-search for given PHOEBE bundle.",
								usage="q-search [options]")
parser.add_argument("--path", required=True, help="Bundle path; supports JSON and gzipped JSON")
parser.add_argument("--q-min", type=float, required=True, help="Min for q-grid")
parser.add_argument("--q-max", type=float, required=True, help="Max for q-grid")
parser.add_argument("--q-step", type=float, required=True, help="Interval step for q-grid")

parser.add_argument("--incl", type=float, required=False,  action='append',
                                help="(Optional) Fixed orbital inclination angles to test for every q value given (in degrees); "\
                                        "treated as a fixed parameter for optimization; can be specified multiple times for each value")
parser.add_argument("--n-procs", type=int, required=False, default=os.cpu_count()//2,
                                    help="(Optional) Number of parallel processes to use; defaults to (cpus//2)")
parser.add_argument("--nm-maxiter", type=int, required=False, default=250,
                                    help="(Optional) Max number of iterations for NM optimizer for each fixed q-value; defaults to 250")
parser.add_argument("--solution-dir", required=False, default=os.getcwd(),
                                    help="(Optional) Parent directory path to place solution directory 'q-solutions'; defaults to cwd")

BUNDLE: phoebe.Bundle
SOLUTION_DIRECTORY: str

def optimize_q(q: float) -> str | None:
    with utils.LOCK:
        b = BUNDLE.copy()
    try:
        return utils.optimize_q(b, q, SOLUTION_DIRECTORY)
    except Exception as e:
        utils.printsync_log(f"Could not solve for q={q:.4f} | {e}", SOLUTION_DIRECTORY)
        return None

def solve(n_procs: int, q_grid: list[float]):
    os.makedirs(SOLUTION_DIRECTORY, exist_ok=True)
    with mp.Pool(n_procs) as pool:
        list(tqdm.tqdm(pool.imap(optimize_q, q_grid), total=len(q_grid)))

def search_fixed_incl(incls: list[float], q_grid: list[float], solution_directory: str, n_procs: int):
    global SOLUTION_DIRECTORY

    for incl in incls:
        print(f"Testing inclination {incl*u.degree}")
        BUNDLE.set_value(qualifier='incl', component='binary', value=incl*u.degree)
        SOLUTION_DIRECTORY = os.path.join(solution_directory, f"incl-{incl}")
        solve(n_procs, q_grid)

def q_search(args: argparse.Namespace):
    global BUNDLE
    global SOLUTION_DIRECTORY

    qGrid = phoebe.arange(args.q_min, args.q_max + args.q_step, args.q_step)

    BUNDLE = utils.load_bundle(args.path)

    fitParameters: list[str]
    if 'contact_envelope' in BUNDLE.components:
        print("Configuring solver for contact binary")
        fitParameters = ['incl@binary', 'teffratio', 'fillout_factor']
    else:
        print("Configuring solver for detached/semidetached case; "
                    "assumes eccentricity and argument of periastron (ecc and per0) are constrained by 'esinw' and 'ecosw' "
                    "as well as 'requivratio' and 'requivsumfrac' are unconstrained" )
        # assumes eccentricity and per0 are constrained
        fitParameters = ['teffratio@binary@orbit@component', 'requivsumfrac@binary@orbit@component', 'requivratio',
                         'esinw@binary@orbit@component', 'ecosw@binary@orbit@component', 'incl@binary']
    if args.incl:
        fitParameters.remove('incl@binary')

    BUNDLE.set_value_all(qualifier='enabled', dataset=BUNDLE.datasets, value=True) # enable all datasets to use
    BUNDLE.disable_dataset('mesh01')
    BUNDLE.add_solver('optimizer.nelder_mead', solver="opt_q_search", maxiter=args.nm_maxiter, fit_parameters=fitParameters)
    BUNDLE.run_all_constraints()
    
    SOLUTION_DIRECTORY = os.path.join(args.solution_dir, "q-solutions")
    if args.incl:
        search_fixed_incl(args.incl, qGrid, SOLUTION_DIRECTORY, args.n_procs)
    else:
        solve(args.n_procs, qGrid)

def run():
    args = parser.parse_args()
    if not os.path.exists(args.path):
        raise FileExistsError(f"{args.path} does not exist")
    if not (args.path.endswith('.gz') or args.path.endswith('.json')):
        raise ValueError(f"{args.path} does not point to valid PHOEBE bundle")

    solutionDir = os.path.join(args.solution_dir, "q-solutions")
    if not os.path.exists(solutionDir):
        os.makedirs(solutionDir, exist_ok=True)

    q_search(args)

if __name__ == "__main__":
    run()