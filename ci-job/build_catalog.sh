#! /bin/bash

# Comma separated list of directories to ignore, dont use spaces in the directory names when creating them.
IGNORE_DIRECTORIES="ci-job .git .github"


function is_ignored() {
  # if the directory is in the ignore list, return 0
  local dir

  for dir in ${IGNORE_DIRECTORIES[@]}
  do
    [[ $dir == $1 ]] && { return 0; }
  done
  return 1
}


# Create the categories array using directories that are not in the ignore list
for file in $(ls .)
do
  [[ -d $file ]] && { 
    is_ignored $file || CATEGORIES+=($file)
  }
done


# Output the catalog of tools in a markdown table using metadata from the README.md file in each tool directory
echo "## Catalog of Tools"
echo
echo "| Category | Tool | Description | Languages |"
echo "| :--- | :--- | :--- | :--- |"

for i in ${CATEGORIES[@]}
do
  for tool in $(ls $i)
  do
    [[ -f $i/$tool/README.md ]] && {
      DESCRIPTION=$(grep "description:" $i/$tool/README.md | cut -d ":" -f 2 )
      LANGUAGES=$(grep "languages:" $i/$tool/README.md | cut -d ":" -f 2 )
      echo "| $i | $tool | $DESCRIPTION | $LANGUAGES |"
    } || {
      echo "| $i | $tool | README.md not found for tool | |"
    }
  done
done


