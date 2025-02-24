import os
import ccdproc
import subprocess
import datetime
import numpy as np

from multiprocessing import Pool, Lock
from tqdm import tqdm

from ccdproc import wcs_project
from astropy.wcs import WCS
from astropy.io import fits

from astropy import log
log.setLevel('ERROR')

import argparse
parser = argparse.ArgumentParser("align-images", description="Command-line tool for aligning science FITS images using WCS projections.")
parser.add_argument("--images-dir", required=True, help="Directory with science images. Ideally, these are already calibrated (bias-, dark-, and flat-subtracted).")

parser.add_argument("--n-procs", type=int, required=False, default=os.cpu_count()//2,
                                    help="(Optional) Number of parallel processes to use; defaults to (cpus//2).")
parser.add_argument("--output-parent-dir", required=False, default=None,
											help="(Optional) Parent directory where to place the plate-solved FITS images directory and the aligned images. Defaults to --images-dir.")

SOLVE_CMD_TEMPLATE = ('solve-field --fits-image --no-plots --timestamp --new-fits "{solvedOutPath}" --cpulimit 180 -D "{tempFiles}" "{inputPath}" --overwrite')
CCD_KWARGS = {'unit': 'adu'}

LOCK = Lock()
def print_to_log(msg: str):
	global LOCK

	with LOCK:
		with open(f"shifter.log", "a+") as logFile:
			logFile.write(f"[{datetime.datetime.now()}] {msg}\n")

def plate_solve_file(input_file: str, output_parent_dir: str):
	solvedFitsDir = os.path.join(output_parent_dir, "solved-fits")
	os.makedirs(solvedFitsDir, exist_ok=True)

	fileName = os.path.basename(input_file)

	plateSolveCmd = SOLVE_CMD_TEMPLATE.format(inputPath=input_file, 
											solvedOutPath=os.path.join(solvedFitsDir, fileName),
											tempFiles=os.path.join(output_parent_dir, "solved"))
	# print(plateSolveCmd)
	result = subprocess.run(plateSolveCmd, shell=True, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
	if result.returncode != 0:
		print_to_log(f"Failed to plate solve {input_file}")

def plate_solve(corrected_files: list[str], output_parent_dir: str, pos: int):
	print_to_log(f"[{os.getpid()}] Begin plate solving")
	for cFile in tqdm(corrected_files, position=pos):
		plate_solve_file(cFile, output_parent_dir)
	print_to_log(f"[{os.getpid()}] Finished plate solving")

class SolveCaller:
	def __init__(self, images_dir: str, output_parent_dir: str) -> None:
		self.images_dir = images_dir
		self.output_parent_dir = output_parent_dir
		self.pos = 0

	def __call__(self, imagesChunks):
		global LOCK

		pos: int
		with LOCK:
			pos = self.pos
			self.pos + 1
		plate_solve(imagesChunks, self.output_parent_dir, pos)

def solve_parallel(images_dir: str, output_parent_dir: str, n_procs: int):
	imagesChunks = np.array_split([os.path.join(images_dir, f) for f in os.listdir(images_dir)], n_procs)
	with Pool(n_procs) as pool:
		pool.map(SolveCaller(images_dir, output_parent_dir), imagesChunks)

def align_images(output_parent_dir: str):
	# Shift plate solved images. Will also only take the first header from the FITS file to allow them to work in IRAF. 
	targetWcs: WCS = None
	solvedFitsDir = os.path.join(output_parent_dir, "solved-fits")
	shiftedDir = os.path.join(output_parent_dir, "aligned-fits")
	os.makedirs(shiftedDir, exist_ok=True)

	rawImages = ccdproc.ImageFileCollection(solvedFitsDir)
	for img, img_fname in rawImages.ccds(ccd_kwargs=CCD_KWARGS, return_fname=True):
		shiftedResultPath = os.path.join(shiftedDir, f"s_{img_fname}")
		if not targetWcs:
			targetWcs = WCS(img.header)
			with fits.open(os.path.join(solvedFitsDir, img_fname)) as fitsImg:
				targetWcs = WCS(fitsImg.pop())
			img.write(shiftedResultPath, overwrite=True)
		else:
			shiftedImg = wcs_project(img, targetWcs)
			primaryImg = shiftedImg.to_hdu()[0] # Takes only the science image from the HDU list, ignoring the mask, for use in IRAF
			primaryImg.writeto(shiftedResultPath, overwrite=True)

def run():
	args = parser.parse_args()
	if not os.path.exists(args.images_dir):
		raise FileExistsError(f"{args.images_dir} does not exist")
	print(args)
	
	outputParentDir = args.output_parent_dir if args.output_parent_dir is not None else args.images_dir
	os.makedirs(outputParentDir, exist_ok=True)

	solve_parallel(args.images_dir, outputParentDir, args.n_procs)
	align_images(outputParentDir)

if __name__ == '__main__':
	run()