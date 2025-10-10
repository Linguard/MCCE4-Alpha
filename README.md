# Multi-Conformation Continuum Electrostatics

<p align="center">
  <img src="docs/images/mcce_logo1.png" alt="MCCE Logo" style="max-width: 100%; height: auto;">
</p>

## Welcome to the __MCCE4-Alpha__! 

__🎬 Let's Get Started:__ 

This tutorial walks you through calculating and analyzing __electrostatic interactions__ from a PDB structure.  
You’ll find step-by-step practical examples designed to help new users quickly run simulations and understand key features of MCCE4.

__🛠️ Install Now:__ [Installation](https://gunnerlab.github.io/mcce4_tutorial/docs/installation/) 
#### TL;DR (Installation):
  1. Clone this repo, then cd into it:
  ```
   git clone https://github.com/GunnerLab/MCCE4-Alpha.git; cd MCCE4-Alpha
  ```
  
  2. Check if you have pre-requisites such as `conda` and `apptainer`. If not. a TODO list with instructions is displayed. Run:
  ```
   sh ./MCCE_bin/check_environment.sh
  ```

  3. If no "TODOs" to do, then run this script to download NGPB's image file and create a conda environment for MCCE4:
  ```
   sh ./MCCE_bin/quick_install.sh
  ``` 

__🚀 Run Your First Job:__ [Quick Start](https://gunnerlab.github.io/mcce4_tutorial/docs/guide/quick_start/)  

__📖 MCCE4-Alpha Tutorial:__ [Full Documentation](https://gunnerlab.github.io/mcce4_tutorial/)

## MCCE4-Tools 🔧  
Please also check out the companion repository __MCCE4-Tools__. 

🧰 __Explore Now:__ [MCCE4-Tools GitHub](https://github.com/GunnerLab/MCCE4-Tools)

---

## __Quick Introduction__

Given the structure of a macromolucule (in a PDB file), __MCCE4__ can predict the following:

- __pKₐ values__
- __Protonation states__
- __Electrostatic properties__ of biomolecules

In this program, protein side chain motions are simulated explicitly while the dielectric effect of solvent and bulk protein material is modeled by continuum electrostatics.

## __Documentation Overview__
Comprehensive documentation covering:
- Installation
- Guide: Detailed explanations of all settings
- Example Projects 

## Help us improve MCCE4
This is a testing version of MCCE4 development. 
Please let us know about questions, comments or report any issues you encounter [here](https://github.com/GunnerLab/MCCE4-Alpha/issues).
Thank You and we hope you enjoy using MCCE4!  

# MCCE Wiki
[Learn about MCCE, installation, available tools, and research done with MCCE.](https://mccewiki.levich.net) (under construction)

---

Copyright (C) 2024 GunnerLab
This software is distributed under the terms the terms of the MIT licence
