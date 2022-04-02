import sys
import os
import settings
import input_reader as inread
import re

"""
TEST FILES
	- file must be named "in{number}".txt
	- output files will be written to /output/"out{number}".txt

	- input format: see in01.txt
"""
def main():
	dirpath = os.path.dirname(__file__)
	testdir = os.path.join(dirpath,"tests")
	outdir = outpath(dirpath)

	"""
	f is not a full path but relative to the current dir. (os.listdir(testdir))
	would give [test1.txt, test2.txt] et
	"""
	patt_infile = r"in[\d]+.txt"
	test_files = [os.path.join(testdir,f) for f in os.listdir(testdir) if os.path.isfile(os.path.join(testdir,f)) and re.search(patt_infile,f)]
	# iterate through test folder
	for file in test_files:
		# edit outpath here btw
		inread.Read(file,outdir=outdir)
	return

def outpath(dirpath):
	outdir = os.path.join(dirpath,"output")
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	return outdir
if __name__ == "__main__":
	main()