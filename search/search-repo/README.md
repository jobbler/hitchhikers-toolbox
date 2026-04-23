---
description: search files and branches of a git repository
languages: python
---

# search-repo

This script is used to search the files and branches of a repository. It leverages gits 'grep' that searchs the object database. This makes the script more efficient and faster.

Use the `--help` option to show how to use the script.

Here are some highlights of the script: 
- The search scope can be a single branch, multiple branches, or all branches of a repository.
- The search terms can consist of:
  - must include terms
  - may include terms
  - must not include terms
- The search terma can include regex expressions (if option specified)
