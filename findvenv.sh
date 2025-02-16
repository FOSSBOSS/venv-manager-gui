#!/bin/bash
#set -xv

# Find all the python virtual enviornments. 
vnv_cfg=$(locate pyvenv.cfg)
if [ -z "$vnv_cfg" ]; then
	echo "No python virtual enviornments found"
	echo "Maybe try sudo updatedb and rerun script"
	exit 1
fi
echo "Found the following python virtual enviornments"

# list all the directories, their respective python versions, and what packages thety include.
for vnvs in $vnv_cfg;
	do
		# extract path
		vnv_path=$(dirname "$vnvs")
		# exec that version of python for its version
		py_version=$("$vnv_path/bin/python" --version 2>&1)
		# exec pip list
		#pkgz=$(python "$vnv_path/bin/pip" list 2>/dev/null) # hide warnings

		# print findings
		echo "____________________________________________"
		echo "Virtual Enviornment: $vnv_path"
		echo "Python Version: $py_version"
		# Turns out listing all the pkgz is crazy long.
		# so Ima just tell you how to list them. 
		# Also not running that command makes this thing run faster
		
		echo "Use python \"$vnv_path/bin/pip\" list | less"
		echo "to list installed packages."

    done


vnv_count=$(echo "$vnv_cfg" | wc -l)
echo "Found " $vnv_count " python virtual environments"
