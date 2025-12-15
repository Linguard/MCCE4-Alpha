---
# 1ERT :: Human Thioredoxin (Reduced Form)
## PDB.Structure
### Function: OXIDOREDUCTASE
### First Release: 07-FEB-96
### Method: X-RAY DIFFRACTION
### Resolution: 1.70 ANGSTROMS.
### Molecule: THIOREDOXIN, ACTIVE SITE CYSTEINES 32 AND 35 IN THE REDUCED FORM
### Seqres Species: Residues: A:105; Total: 105
### Total waters: 46
### Biounits: DIMERIC: A;
### Models: 1
### Chains: A
### Model 1 Residues:
  - A:
 'RESIDUES': ('ALA: 8, ASN: 3, ASP: 7, CYS: 5, GLN: 5, GLU: 10, GLY: 5, HIS: 1, ILE: 4, LEU: 6, LYS: 12, MET: 3, PHE: 9, PRO: 3, SER: 7, THR: 4, TRP: 1, TYR: 1, VAL: 11', 'Total: 105', 'Ionizable: 36',
              'Ratio: 34.3%')

### Model 1 Free Cofactors & Waters:
  - A:
 'HOH': 46

### Disulfides:
  - CYS A  73 -- 2.05 Å --> CYS A  73

## MCCE.Step1
### Termini:
 - <strong>NTR</strong>: "MET A   1"
 - <strong>CTR</strong>: "VAL A 105"

### Free Cofactors:
  - NOTE: Include the '--wet' option at the command line to keep buried waters and cofactors. Alternatively, change the water SAS cutoff to a non-zero, positive number using the command line 'u' option:
  > protinfo 1fat.pdb -u H2O_SASCUTOFF=0.05
  - Total deleted cofactors = 46.

### Distance Clashes:
<details><summary>Clashes found</summary>

- d= 1.55: " CA  NTR A   1" to " CB  MET A   1"

</details>

