#!/bin/sh

echo "MCCE4 \"Quick Install\" Script"
echo ""

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLONE_PATH="$(dirname "$SCRIPT_DIR")"
CLONE="$(basename "$CLONE_PATH")"
ENV_NAME="mc4"

# Use the -h switch to get help on usage.
help_msg() {
  echo ""
  echo "Usage:"
  echo ""
  echo "sh ./MCCE_bin/$(basename "$0") -h"
  echo "sh ./MCCE_bin/$(basename "$0") [env_name]"
  echo ""
  echo " -h                 : Display this help message & exit."
  echo " env_name (optional): Custom name for the conda environment to create (default is 'mc4')."
  echo "                    : Required if you already have a conda environment named 'mc4'."
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
# Shift arguments to access possible env_name after options processing
shift $(( OPTIND - 1 ))
# Get arguments from command line
env_name=""
if [ -n "$1" ];
then
  env_name="$1"
  echo "User env: $env_name"
fi

echo "Checking for a download tool (curl or wget)..."
DOWNLOAD_CMD=""
if command -v wget >/dev/null 2>&1;
then
    DOWNLOAD_CMD="wget"
elif command -v curl >/dev/null 2>&1;
then
    DOWNLOAD_CMD="curl"
else
    echo "Error: Neither 'wget' nor 'curl' could be found."
    echo "Please install one of them to download the NGPB container image."
    exit 1
fi
echo "Using '$DOWNLOAD_CMD' for downloads."
echo ""

REPO_bin="$CLONE_PATH/bin"
echo "MCCE4/bin folder: $REPO_bin"
echo "MCCE_bin folder: $SCRIPT_DIR"
echo ""
echo "Getting NextGenPB generic container image with $DOWNLOAD_CMD..."
# Need to check if file exists first, otherwise wget will save it as: 'path/NextGenPB.sif.1'
#
# Name of the compiled image when Makefile is used:
sif_mc4="$REPO_bin/NextGenPB_MCCE4.sif"
# Name of the downloaded generic image & source url:
sif_file="$REPO_bin/NextGenPB.sif"
sif_url="https://github.com/concept-lab/NextGenPB/releases/download/NextGenPB_v1.0.0/NextGenPB.sif"

if [ ! -f "$sif_file" ];
then
  echo "Downloading NGPB image from $sif_url..."
  if [ "$DOWNLOAD_CMD" = "curl" ]; then
      curl -L -o "$sif_file" "$sif_url" || { echo "Failed to download NGPB image with curl"; exit 1; }
  else # wget
      wget -O "$sif_file" "$sif_url" || { echo "Failed to download NGPB image with wget"; exit 1; }
  fi
  echo "Soft-linking the generic image as 'NextGenPB_MCCE4.sif'"
  ln -sf "$sif_file" "$REPO_bin/NextGenPB_MCCE4.sif"

else
  echo "NGPB image file already exists: $sif_file"
  echo "Delete it before re-running the script if you need to replace it."
fi

echo ""
echo "ATTENTION: MCCE4-Alpha comes with precompiled \`mcce\` and \`delphi\` executable files"
echo "to simplify the installation."
echo "These files and the NGPB image MAY NOT WORK on your system, but you should try them..."
echo "as they might!"
echo ""
echo "Please refer to the Installation guide to obtain compiled versions for your system."
echo ""
echo "Conda environment creation..."
if command -v conda >/dev/null 2>&1;
    DO_CONDA=1
else
    DO_CONDA=0
    echo "'conda' could not be found. Please run this script:"
    echo " sh ./MCCE_bin/check_environment.sh"
    echo ""
    echo "Skipping conda env creation."
fi

if [ "$DO_CONDA" -eq 1 ];
then
  ENVS=$(conda env list)
  if [ -z "$env_name" ];
  then
    # check if env with default name already exists:
    if echo "$ENVS" | grep -q "$ENV_NAME"; then
        echo "Env '$ENV_NAME' already exists. Make sure it complies with $CLONE_PATH/mc4.yml."
    else
        echo "Creating a dedicated conda env with default name: $ENV_NAME"
        conda env create -f "$REPO_PATH/mc4.yml"
    fi
    # set name for activation message:
    env_name="$ENV_NAME"
  else
    # check if env with user-provided name already exists:
    if echo "$ENVS" | grep -q "$env_name"; then
        echo "Env '$env_name' already exists. Make sure it complies with $CLONE_PATH/mc4.yml."
    else
        echo "Creating a dedicated conda env with given name: $env_name"
        conda env create -f "$REPO_PATH/mc4.yml" -n "$env_name"
    fi
fi

echo ""
# export lines for the bin folders:
export1="export PATH=\"$REPO_bin:\$PATH\""
export2="export PATH=\"$SCRIPT_DIR:\$PATH\""

# Detect OS and suggest appropriate RC file
if [ "$(uname -s)" = "Darwin" ]; then
    # On macOS, login shells for bash source .bash_profile. For zsh, it's .zprofile.
    # We will check for .bash_profile as a common default and inform the user.
    rc_file="$HOME/.bash_profile"
    echo "On macOS, this script will check/modify '$rc_file'."
    echo "If you use a different shell (e.g., zsh), you might need to manually edit '~/.zshrc' or '~/.zprofile'."
else
    # Assume Linux/other Unix-like, where .bashrc is common for interactive shells.
    rc_file="$HOME/.bashrc"
fi

# Check if rc file exists
no_rc_msg=""
if [ ! -f "$rc_file" ];
then
  echo "RC file ($rc_file) not found."
  # create a message for latter use:
  no_rc_msg="Create the RC file with this command: ' cd ~; touch $rc_file '"
  echo ""
else
  # Use grep -F to match fixed strings, which is safer and faster.
  if grep -qF "$export1" "$rc_file";
  then
    echo "'MCCE4-Alpha/bin' already in PATH."
  fi
  if grep -qF "$export2" "$rc_file";
  then
    echo "'MCCE4-Alpha/MCCE_bin' already in PATH."
  fi
fi

echo ""
echo "Almost done!"
echo ""
if [ -n "$no_rc_msg" ]; then
    echo "$no_rc_msg"
    echo ""
fi
echo "Add these export path lines to your $rc_file (if not already there), then save the file:"
echo ""
echo " $export1"
echo " $export2"
echo ""
echo "To effect the changes to your PATH variable, please start a new"
echo "terminal session or run:"
echo ""
echo " source $rc_file"
echo ""

if [ "$DO_CONDA" -eq 0 ];
then
    echo "To complete this quick installation, activate a python 3.10 environment"
    echo "that complies with requirement.txt."
else
    echo "To complete this quick installation, activate your environment:"
    echo ""
    echo "  conda activate $env_name"
fi
echo ""
echo "You can then run these commands:"
echo ""
echo "  which getpdb  # 1. check tool is found via PATH"
echo "  getpdb -h     # 2. check several python requirements"
echo ""
echo ""
echo "Thank you for using MCCE4!"
echo "Thank you for opening an issue if you encountered problems with the script:"
echo "https://github.com/GunnerLab/MCCE4-Alpha/issues"
echo ""
