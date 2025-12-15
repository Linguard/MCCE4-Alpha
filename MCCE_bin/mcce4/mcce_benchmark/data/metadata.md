
## Experimental pKas datasets

### pkdb_v1: 
Source: [Dr. Emil Axelov's pKa Database (1)](http://compbio.clemson.edu/lab/software/5/). 
The resulting file: `pkas.csv` contains the WT data most of pKas of the mutant proteins were measured by NMR, hence
yield pKa _ranges_ rather than values and may not have a pdb.
Revised in 2025 given information in newly curated 'PKAD_R'

### pkdb_vR:
Source: [Dr. Emil Axelov's pKa Database (R)](http://compbio.clemson.edu/PKAD-R/)
Description: PKAD-R: curated, expanded and redesigned database of experimental pKa values in proteins

### pkdb_snase:
Source: Pr. Gunner
Description:


#### pKa file header:
**'PDB ID', 'Res Name', 'Chain', 'Res ID', 'Expt. pKa', 'Expt. Uncertainty', '%SASA', 'Expt. method', 'Expt. salt conc','Expt. pH', 'Expt. temp', 'Reference'**

### File 'proteins.txt':
Comments out the excluded pdbs and gives the reason.

### File 'metadata.md':
Experimental data source details (this file); to be kept in data folder.

### Folder 'runs':
Holds the prepared pdb files which reside inside a folder with the same id in upper case.
This folder is re-used for every MCCE benchmarking job.

### File 'runs/book.txt':
The "queue book" (a.k.a. BOOK, Q_BOOK), is used to monitor the submitted batch
of MCCE simulations, and the submit script 'run.sh' is used to run MCCE in each subfolder.
