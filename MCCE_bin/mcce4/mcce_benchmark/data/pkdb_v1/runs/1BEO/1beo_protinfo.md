---
# 1BEO :: Beta-Cryptogein
## PDB.Structure
### Function: FUNGAL TOXIC ELICITOR
### First Release: 02-AUG-96
### Method: X-RAY DIFFRACTION
### Resolution: 2.20 ANGSTROMS.
### Molecule: BETA-CRYPTOGEIN
### Seqres Species: Residues: A:98; Total: 98
### Total waters: 66
### Biounits: DIMERIC: A;
### Models: 1
### Chains: A
### Model 1 Residues:
  - A:
 'RESIDUES': ('ALA: 11, ASN: 7, ASP: 3, CYS: 6, GLN: 4, GLY: 3, ILE: 3, LEU: 10, LYS: 6, MET: 3, PHE: 2, PRO: 4, SER: 12, THR: 14, TYR: 5, VAL: 5', 'Total: 98', 'Ionizable: 20',
              'Ratio: 20.4%')

### Model 1 Free Cofactors & Waters:
  - A:
 'HOH': 66

### Disulfides:
  - CYS A  3 -- 2.01 Å --> CYS A  71
  - CYS A  27 -- 1.99 Å --> CYS A  56
  - CYS A  51 -- 2.02 Å --> CYS A  95

## MCCE.Step1
### Termini:
 - <strong>NTR</strong>: "THR A   1"
 - <strong>CTR</strong>: "LEU A  98"

### Free Cofactors:
  - NOTE: Include the '--wet' option at the command line to keep buried waters and cofactors. Alternatively, change the water SAS cutoff to a non-zero, positive number using the command line 'u' option:
  > protinfo 1fat.pdb -u H2O_SASCUTOFF=0.05
  - Total deleted cofactors = 66.

### Distance Clashes:
<details><summary>Clashes found</summary>

- d= 1.53: " CA  NTR A   1" to " CB  THR A   1"
- d= 1.99: " SG  CYS A  27" to " SG  CYS A  56"

</details>

