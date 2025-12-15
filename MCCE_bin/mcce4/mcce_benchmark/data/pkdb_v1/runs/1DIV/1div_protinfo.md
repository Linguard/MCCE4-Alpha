---
# 1DIV :: Ribosomal Protein L9
## PDB.Structure
### Function: RIBOSOMAL PROTEIN
### First Release: 02-JUL-96
### Method: X-RAY DIFFRACTION
### Resolution: 2.60 ANGSTROMS.
### Molecule: RIBOSOMAL PROTEIN L9, PROKARYOTIC
### Seqres Species: Residues: A:149; Total: 149
### Biounits: DIMERIC: A;
### Models: 1
### Chains: A
### Model 1 Residues:
  - A:
 'RESIDUES': ('ALA: 19, ARG: 4, ASN: 6, ASP: 4, GLN: 10, GLU: 13, GLY: 11, HIS: 3, ILE: 8, LEU: 17, LYS: 23, MET: 1, PHE: 4, PRO: 4, SER: 3, THR: 8, TYR: 2, VAL: 9', 'Total: 149', 'Ionizable: 49',
              'Ratio: 32.9%')

## MCCE.Step1
### Termini:
 - <strong>NTR</strong>: "MET A   1"
 - <strong>CTR</strong>: "LYS A 149"

### Free Cofactors:
  - NOTE: Include the '--wet' option at the command line to keep buried waters and cofactors. Alternatively, change the water SAS cutoff to a non-zero, positive number using the command line 'u' option:
  > protinfo 1fat.pdb -u H2O_SASCUTOFF=0.05

### Missing Heavy Atoms:
  -    Missing heavy atoms for CTR01 in "CTR A 149":   OXT

### Distance Clashes:
<details><summary>Clashes found</summary>

- d= 1.53: " CA  NTR A   1" to " CB  MET A   1"

</details>

