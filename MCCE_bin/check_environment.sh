#!/bin/sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLONE_PATH="$(dirname "$SCRIPT_DIR")"
CLONE="$(basename "$CLONE_PATH")"

echo ""
echo "MCCE4 clone: $CLONE"
echo "MCCE4 clone path: $CLONE_PATH"
echo ""
echo "Script to check pre-requisites on the current system:"
echo " - conda"
echo "   - conda env 'mc4', default name in mc4.yml file"
echo " - apptainer, the container app for MCCE4 default PBE solver, NGPB"
echo ""
echo "NOTE: Any 'TODO' line listed below means that you cannot run any simulation"
echo "      using $CLONE unless you perform those actions."
echo "----------------------------------------------------------------------------"
echo ""

ENV_NAME="mc4"

echo "Checking for conda..."
if ! command -v conda >/dev/null 2>&1; then
    echo "  WARNING: conda is required, but not found on your system."
    echo "  TODO: Please install miniconda."
else
    echo "  Conda found."
    ENVS=$(conda env list)
    if echo "$ENVS" | grep -q "$ENV_NAME"; then
        echo "  Env '$ENV_NAME' already exists. Make sure it complies with $CLONE_PATH/mc4.yml."
    else
        echo "  Env '$ENV_NAME' will be created by a quick-install script in $CLONE/MCCE_bin (unless script receives a different name)."
    fi
fi

echo ""
echo "Checking for apptainer (container app for NGPB)..."

if command -v apptainer >/dev/null 2>&1; then
    echo "  Container app 'apptainer' found: you're good to go."
else
    echo "  WARNING: apptainer is not found on your system, but is required for running a simulation."
    echo "  TODO: Please install apptainer before running MCCE4."
    if [ "$(uname -s)" = "Linux" ]; then
        echo "  You're on Linux. Check with your systems administrator if you can run these commands:"
        echo "   sudo add-apt-repository -y ppa:apptainer/ppa"
        echo "   sudo apt update"
        echo "   sudo apt install -y apptainer"
        echo ""
        echo "  See: https://apptainer.org/docs/admin/main/installation.html#install-ubuntu-packages"
    else
        echo "  You're on macOS. It's complicated."
        echo "  See: https://apptainer.org/docs/admin/main/installation.html#mac"
    fi
fi
