#! /bin/bash

# Script Name: yaml-compare.sh
# Author: John Herr <joherr@redhat.com>
# Date: 7 Mar 2025
# Description: This normalizes two YAML files and compares them.
#              It requires the yq command to function correctly.
#              yq: https://github.com/mikefarah/yq


usage() {
  echo "Usage: $0 [-k] [-d directory] file1.yaml file2.yaml"
  echo "       -k    Keep the artifact files. Can also set the ENV variable 'KEEP'"
  echo "       -n    Just normalize the files. Do not perform the DIFF."
  echo "             Automatically implies the -k flag."
  echo "             Can also set the ENV variables 'NODIFF' and 'KEEP'"
  echo "       -d    Specify the directory to place tempory artifact files."
  echo "             Defaults to current directory"
  echo "             Can also set the ENV variable 'TMPDIR'"
  echo
  echo "For example, the following lines are functionally the same:"
  echo "    KEEP=0 $0    file1.yaml file2.yaml"
  echo "           $0 -k file1.yaml file2.yaml"
  echo
  echo "For example, the following lines are functionally the same:"
  echo "    KEEP=0 TMPDIR=/tmp $0            file1.yaml file2.yaml"
  echo "                       $0 -k -d /tmp file1.yaml file2.yaml"
  exit 1
}

: ${TMPDIR:=.}

while getopts ":knd:" options
do
  case "${options}" in
 
    k)
       KEEP=0
       ;;

    n)
       NODIFF=0
       KEEP=0
       ;;

    d)
       TMPDIR=${OPTARG}
       ;;

    *)
       usage
       ;;

   esac
done

shift $((OPTIND-1))


[[ $# -ne 2 ]] && {
  echo "Need two files to compare"
  echo 
  usage
}


file1=$1
file2=$2

[[ ! -f ${file1} ]] \
&& {
     echo "File ${file1} does not exist"
     exit 1
   }

[[ ! -f ${file2} ]] \
&& {
     echo "File ${file2} does not exist"
     exit 1
   }

[[ ! -d ${TMPDIR} ]] \
&& {
     echo "Tempory directory ${TMPDIR} does not exist"
     exit 1
   }


out1=${TMPDIR}/${file1}.$$
out2=${TMPDIR}/${file2}.$$


echo "Normalizing files: "
echo "  : ${file1}"
echo "  : ${file2}"
echo

# We need to sort things using yq

cat ${file1} \
  | yq 'sortkeys(...)' > ${out1}

 cat ${file2} \
  | yq 'sortkeys(...)' > ${out2}


[[ -z ${KEEP+x} ]] \
&& {
     echo "Comparing files"
     echo

     diff ${out1} ${out2}
   }


echo

[[ -n ${KEEP+x} ]] \
&& {
     echo "Retaining artifacts:"
     echo "  : ${out1}"
     echo "  : ${out2}"
} || {
     echo "Removing artifacts:"
     rm -v ${out1} ${out2}
}


