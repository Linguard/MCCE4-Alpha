---
# 1HHO :: Structure Of Human Oxyhaemoglobin At 2.1 Angstroms Resolution
## PDB.Structure
### Function: OXYGEN TRANSPORT
### First Release: 10-JUN-83
### Method: X-RAY DIFFRACTION
### Resolution: 2.10 ANGSTROMS.
### Molecule: HEMOGLOBIN A (OXY) (ALPHA CHAIN), HEMOGLOBIN A (OXY) (BETA CHAIN)
### Seqres Species: Residues: A:141, B:146; Total: 287
### Cofactors:
  - PO4:
 'PHOSPHATE ION', 1
  - HEM:
 'HEME', 2
  - OXY:
 'OXYGEN MOLECULE', 2

### Total cofactors: 5
### Total waters: 109
### Biounits: TETRAMERIC: A, B;
### Models: 1
### Chains: A, B
### Model 1 Residues:
  - A:
 'RESIDUES': ('ALA: 21, ARG: 3, ASN: 4, ASP: 8, CYS: 1, GLN: 1, GLU: 4, GLY: 7, HIS: 10, LEU: 18, LYS: 11, MET: 2, PHE: 7, PRO: 7, SER: 11, THR: 9, TRP: 1, TYR: 3, VAL: 13', 'Total: 141', 'Ionizable: 40',
              'Ratio: 28.4%')
  - B:
 'RESIDUES': ('ALA: 15, ARG: 3, ASN: 6, ASP: 7, CYS: 2, GLN: 3, GLU: 8, GLY: 13, HIS: 9, LEU: 18, LYS: 11, MET: 1, PHE: 8, PRO: 7, SER: 5, THR: 7, TRP: 2, TYR: 3, VAL: 18', 'Total: 146', 'Ionizable: 43',
              'Ratio: 29.5%')

### Model 1 Free Cofactors & Waters:
  - A:
 'HEM': 1, 'HOH': 48, 'OXY': 1, 'PAA': 1, 'PDD': 1, 'PO4': 1
  - B:
 'HEM': 1, 'HOH': 61, 'OXY': 1, 'PAA': 1, 'PDD': 1

### Links:
  - NE2 HIS A 87 -- 1.94 Å --> FE  HEM A 143
  - FE  HEM A 143 -- 1.66 Å --> O1 OXY A 150
  - NE2 HIS B 92 -- 2.07 Å --> FE  HEM B 147
  - FE  HEM B 147 -- 1.86 Å --> O1 OXY B 150

### Sites:
  - AC1: ['BINDING SITE FOR RESIDUE PO4 A 142', 'LYS A  99', 'ARG A 141']
  - AC2: ['BINDING SITE FOR RESIDUE HEM A 143', 'PHE A  43', 'HIS A  45', 'HIS A  58', 'LYS A  61', 'ALA A  65', 'LEU A  83', 'HIS A  87', 'LEU A  91', 'VAL A  93', 'ASN A  97', 'PHE A  98', 'LEU A 101', 'VAL A 132', 'OXY A 150', 'HOH A 189']
  - AC3: ['BINDING SITE FOR RESIDUE OXY A 150', 'HIS A  58', 'VAL A  62', 'HIS A  87', 'HEM A 143']
  - AC4: ['BINDING SITE FOR RESIDUE HEM B 147', 'PRO A   4', 'THR B  38', 'PHE B  41', 'PHE B  42', 'HIS B  63', 'LYS B  66', 'VAL B  67', 'PHE B  71', 'LEU B  88', 'HIS B  92', 'VAL B  98', 'ASN B 102', 'LEU B 106', 'LEU B 141', 'OXY B 150', 'HOH B 158']
  - AC5: ['BINDING SITE FOR RESIDUE OXY B 150', 'LEU B  28', 'HIS B  63', 'VAL B  67', 'HEM B 147']

## MCCE.Step1
### Renamed:
  - " CAA HEM A 143" to " CAA PAA A 143"
  - " CAA HEM B 147" to " CAA PAA B 147"
  - " CAD HEM A 143" to " CAD PDD A 143"
  - " CAD HEM B 147" to " CAD PDD B 147"
  - " CBA HEM A 143" to " CBA PAA A 143"
  - " CBA HEM B 147" to " CBA PAA B 147"
  - " CBD HEM A 143" to " CBD PDD A 143"
  - " CBD HEM B 147" to " CBD PDD B 147"
  - " CGA HEM A 143" to " CGA PAA A 143"
  - " CGA HEM B 147" to " CGA PAA B 147"
  - " CGD HEM A 143" to " CGD PDD A 143"
  - " CGD HEM B 147" to " CGD PDD B 147"
  - " O1A HEM A 143" to " O1A PAA A 143"
  - " O1A HEM B 147" to " O1A PAA B 147"
  - " O1D HEM A 143" to " O1D PDD A 143"
  - " O1D HEM B 147" to " O1D PDD B 147"
  - " O2A HEM A 143" to " O2A PAA A 143"
  - " O2A HEM B 147" to " O2A PAA B 147"
  - " O2D HEM A 143" to " O2D PDD A 143"
  - " O2D HEM B 147" to " O2D PDD B 147"

### Termini:
 - <strong>NTR</strong>: "VAL A   1", "VAL B   1"
 - <strong>CTR</strong>: "ARG A 141", "HIS B 146"

### Labeling:
<strong><font color='red'>Generic topology file created for:</font></strong>  
PO4: https://pubchem.ncbi.nlm.nih.gov/#query=PO4&tab=substance; OXY: https://pubchem.ncbi.nlm.nih.gov/#query=OXY&tab=substance; 

### Free Cofactors:
  - Removed all 48 HOH in A. Removed all 61 HOH in B.
  - NOTE: Include the '--wet' option at the command line to keep buried waters and cofactors. Alternatively, change the water SAS cutoff to a non-zero, positive number using the command line 'u' option:
  > protinfo 1fat.pdb -u H2O_SASCUTOFF=0.05
  - Total deleted cofactors = 109.
  - Species and properties with assigned default values in debug.log:

  - PO4BK: ['VDW_RAD', 'VDW_EPS']

  - OXYBK: ['VDW_RAD', 'VDW_EPS']

  - HEM01: ['TORSION']

  - Empty connection slot(s):

  - FE: ['HEM 143 to atom  SD', 'HEM 147 to atom  SD']


### Distance Clashes:
<details><summary>Clashes found</summary>

- d= 1.56: " CA  NTR A   1" to " CB  VAL A   1"
- d= 1.94: " NE2 HIL A  87" to "FE   HEM A 143"
- d= 1.48: " CA  NTR B   1" to " CB  VAL B   1"
- d= 1.52: " C2A HEM A 143" to " CAA PAA A 143"
- d= 1.50: " C3D HEM A 143" to " CAD PDD A 143"
- d= 1.66: "FE   HEM A 143" to " O1  OXY A 150"
- d= 1.50: " C2A HEM B 147" to " CAA PAA B 147"
- d= 1.49: " C3D HEM B 147" to " CAD PDD B 147"
- d= 1.86: "FE   HEM B 147" to " O1  OXY B 150"

</details>

