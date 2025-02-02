#!/bin/sh

# Install buildit.py
DEFAULT_PREFIX="/home/${USER}/MyLibraries"
INSTALL_DIR="buildit"

if [ -z ${1:+x} ]; then
    PREFIX=${DEFAULT_PREFIX}
else
    PREFIX=${1}
fi


if [ -d ${PREFIX} ]; then
    echo "Installing buildit.py to ${PREFIX}"

    # create the directory if it does not exist
    mkdir -p ${PREFIX}/${INSTALL_DIR}/bin

    cp buildit.py ${PREFIX}/${INSTALL_DIR}/bin/buildit

    ## add #!/usr/bin/env python to the first line of the script
    sed -i '1s/^.*$/#!\/usr\/bin\/env python/' ${PREFIX}/${INSTALL_DIR}/bin/buildit

    # make the script executable and readable only
    chmod 755 ${PREFIX}/${INSTALL_DIR}/bin/buildit
else
    echo "Error: ${PREFIX} does not exist"
    return 1
fi