#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLONE_PATH="$(dirname "$SCRIPT_DIR")"
CLONE="$(basename "$CLONE_PATH")"
if [[ "$(uname -s)" != "Linux" ]]; then
  echo "$CLONE only runs on Linux."
  exit 1
fi
REPO_bin="$CLONE_PATH/bin"
ENV_NAME="mc4"
RELEASE="NextGenPB_v1.0.0"

echo "$CLONE 'Quick Install' Script"

# Use the -h switch to get help on usage.
help_msg() {
  echo ""
  echo "Usage:"
  echo "bash ./MCCE_bin/$(basename "$0")"
  echo ""
  echo "Help option:"
  echo " -h  : Display this help message & exit."
  echo "     : If you already have a conda environment named 'mc4', it won't be modified;"
  echo "     : yet, it will need to comply with the requirements in $CLONE_PATH/mc4.yml."
  echo ""
  exit 0
}

# Process options
while getopts "h" opt; do
  case $opt in
    h) help_msg ;;
    # Exit on invalid options:
    \?) printf "Invalid option: -%s\n" "$OPTARG" >&2
      exit 1
  esac
done

echo ""
# Check for curl download tool needed for apptainer installation:
if ! command -v curl >/dev/null 2>&1; then
  echo "STOP: Download tool 'curl' could not be found."
  echo "TODO: Please, install it with the following commands, then re-run the quick_install script:"
  echo "  sudo apt update "
  echo "  sudo apt install curl "
  echo "  cd $CLONE_PATH "
  echo ""
  exit 1
fi

NO_APPTAINER=1
export0=""
echo ""
echo "Checking for apptainer (container app for NGPB)..."
if command -v apptainer >/dev/null 2>&1; then
  NO_APPTAINER=0
  echo "  Container app 'apptainer' found."
else
  echo "  Container app 'apptainer' is not found on your system."
  if ! command -v rpm2cpio >/dev/null 2>&1; then
    echo "STOP: The unprivileged installation of apptainer requires rpm2cpio and cpio tools, install them with these"
    echo "commands, then re-run the quick_install script:"
    echo "  sudo apt-get install rpm2cpio"
    echo "  sudo apt-get install cpio"
    echo ""
    exit 1
  fi
  echo "Installing apptainer..."
  curl -s https://raw.githubusercontent.com/apptainer/apptainer/main/tools/install-unprivileged.sh | bash -s - "$HOME/apptainer"
  NO_APPTAINER=0
  export0="export PATH=\"$HOME/apptainer/bin:\$PATH\""
fi

if [[ "$NO_APPTAINER" -eq 0 ]]; then
  echo ""
  echo "Checking for NGPB image file..."
  # Name of the compiled image when Makefile is used or as link target to generic sif:
  sif_mc4="$REPO_bin/NextGenPB_MCCE4.sif"
  if [[ -f "$sif_mc4" ]]; then
    echo "  NextGenPB_MCCE4.sif is already installed."
    # # check if "$sif_mc4" is soft-linked & to "$sif_file":
    # if [[ -L "$sif_mc4" ]]; then
    #   resolved_target="$(readlink -f "$sif_mc4")"
    #   if [[ "$resolved_target" != "$(readlink -f "$sif_file")" ]]; then
    #     ln -sf "$sif_file" "$sif_mc4"
    #   fi
    # fi
  else
    # Name of the downloaded generic image & source url:
    sif_file="$REPO_bin/NextGenPB.sif"
    if [[ -f "$sif_file" ]]; then
      echo "  NGPB generic image file already exists: $sif_file"
      echo "  Delete it then re-run the script if you want to replace it."
      echo ""
    else
      echo "Getting NextGenPB generic container image from $sif_url (~1.5GB)..."
      sif_url="https://github.com/concept-lab/NextGenPB/releases/download/$RELEASE/NextGenPB.sif"
      #if [[ "$DOWNLOAD_CMD" = "curl" ]]; then
      curl -L -o "$sif_file" "$sif_url" || { echo "Failed to download NGPB image with curl"; exit 1; }
      #else # wget
      #  wget -O "$sif_file" "$sif_url" || { echo "Failed to download NGPB image with wget"; exit 1; }
      #fi
    fi
    echo "  Soft-linking the generic image as 'NextGenPB_MCCE4.sif'"
    ln -sf "$sif_file" "$sif_mc4"
  fi
fi

echo ""
echo "Checking for conda..."
rc_file="$HOME/.bashrc"
if [[ ! -f "$rc_file" ]]; then
  touch "$rc_file"
fi
DO_CONDA=0
if ! command -v conda >/dev/null 2>&1; then
  echo "STOP: conda is required, but not found on your system."
  echo "TODO: Please install miniconda with the following commands, then re-run this script:"
  echo "  cd ~ "
  echo "  curl -OL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh "
  # -b for batch mode: yes to all questions
  echo "  bash ~/Miniconda3-latest-Linux-x86_64.sh -b "
  echo "  ~/miniconda3/bin/conda init bash "
  echo "  source ~/.bashrc "
  echo "  cd $CLONE_PATH "
  echo ""
  echo "See: https://www.anaconda.com/docs/getting-started/miniconda/install"
else
  echo "  Conda found."
  DO_CONDA=1
fi

echo ""
echo "Conda environment creation..."
if [[ "$DO_CONDA" -eq 1 ]]; then
  ENVS="$(conda env list)"
  # check if env with default name already exists:
  if echo "$ENVS" | grep -q "$ENV_NAME"; then
      echo "  Env '$ENV_NAME' already exists. Make sure it complies with $CLONE_PATH/mc4.yml."
  else
      echo "  Creating a dedicated conda env with default name: $ENV_NAME"
      conda env create -f "$CLONE_PATH/mc4.yml"
  fi
fi

# export lines for the bin folders:
export1="export PATH=\"$REPO_bin:\$PATH\""
export2="export PATH=\"$SCRIPT_DIR:\$PATH\""
echo ""
echo "Checking PATH variables..."
# Check if rc file needs updating:
# Use grep -F to match fixed strings, which is safer and faster.
if grep -qF "$export1" "$rc_file"; then
  echo "  'MCCE4-Alpha/bin' already in PATH."
else
  echo "$export1" >> "$rc_file"
fi
if grep -qF "$export2" "$rc_file"; then
  echo "  'MCCE4-Alpha/MCCE_bin' already in PATH."
else
  echo "$export2" >> "$rc_file"
fi

# if file was not deleted:
if [[ -f "install-unprivileged.sh" ]]; then
  if grep -qF "$export0" "$rc_file"; then
    echo "$export0" >> "$rc_file"
  fi
fi

echo ""
if [[ "$DO_CONDA" -eq 1 ]]; then
  echo "Initializing conda..."
  ~/miniconda3/bin/conda init bash
  source "$rc_file"
  cd $CLONE_PATH
  echo ""
  echo "Now you can run these commands:"
  echo "  conda activate $ENV_NAME"
  echo "  which getpdb      # :: check tool is found via PATH"
  echo "  getpdb -h         # :: check several python requirements"
  echo ""
  echo ""
fi

echo "Thank you for giving $CLONE a try!"
echo ""
echo "Thank you for opening an issue if you encountered problems with the script:"
echo "https://github.com/GunnerLab/$CLONE/issues"
echo ""
