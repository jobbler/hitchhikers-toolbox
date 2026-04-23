#!/usr/bin/env python3
# -----------------------------------------------------------------------------
# Utility: git-logic-search (search-repo.py)
# Created by: Gemini (AI Collaborator) in collaboration with John Herr
# Purpose: Boolean logic-based searching across Git branches.
# Date: 2026
# -----------------------------------------------------------------------------

import argparse
import subprocess
import sys
import collections
import re

# Standard ANSI Colors for terminal readability
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31;1m"
RESET = "\033[0m"
YELLOW = "\033[33m"

def run_command(cmd, verbose=False):
    """Executes a git command and returns the output or an empty string on 'not found'."""
    if verbose:
        print(f"{YELLOW}[DEBUG] Executing: {' '.join(cmd)}{RESET}", file=sys.stderr)
    try:
        # We set check=False because 'grep' returning 1 (no match) is a valid logic state
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return res.stdout
        return ""
    except Exception as e:
        if verbose:
            print(f"{RED}[DEBUG] Execution Exception: {str(e)}{RESET}", file=sys.stderr)
        return ""

def main():
    description = f"{CYAN}Git Logic Search Utility{RESET}\n{YELLOW}Co-authored by John Herr & Gemini (AI Collaborator){RESET}\n\nSearch across multiple git branches using complex Boolean logic (AND, OR, NOT)."
    
    epilog = f"""{YELLOW}SORT_BY KEYS:{RESET}
  branch, file, line, term

{YELLOW}SCOPE (--scope):{RESET}
  {GREEN}file{RESET}   (Default) All logic conditions must be met within a single file.
  {GREEN}branch{RESET} Conditions can be met anywhere across the entire branch.

{YELLOW}EXAMPLES:{RESET}
  python3 search-repo.py --all --scope branch --must-have "API_KEY" --brief
  python3 search-repo.py --all --regex --must-have "automated.*Mode" --show-line
"""

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    logic_group = parser.add_argument_group("Logic Constraints")
    logic_group.add_argument("--must-have", nargs="+", default=[], help="AND: All terms must exist.")
    logic_group.add_argument("--can-have", nargs="+", default=[], help="OR: At least one must exist (if provided).")
    logic_group.add_argument("--must-not-have", nargs="+", default=[], help="NOT: None of these can exist.")

    op_group = parser.add_argument_group("Scope & Operation")
    op_group.add_argument("--all", action="store_true", help="Search all local and remote branches.")
    op_group.add_argument("--branches", nargs="+", default=[], help="Specific branches/refs to search.")
    op_group.add_argument("--regex", action="store_true", help="Interpret terms as POSIX Extended Regex.")
    op_group.add_argument("--scope", choices=["file", "branch"], default="file", help="Granularity of logic.")
    op_group.add_argument("-v", "--verbose", action="store_true", help="Show debug git commands.")
    
    out_group = parser.add_argument_group("Output Control")
    out_group.add_argument("--brief", action="store_true", help="Print only matching files or branches.")
    out_group.add_argument("--sort-by", default="branch,file,line", help="Priority: branch,file,line,term.")
    out_group.add_argument("--show-line", action="store_true", help="Show the full matching line.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # 1. Resolve Branch References
    if args.all:
        raw = run_command(["git", "for-each-ref", "--format=%(refname)", "refs/heads/", "refs/remotes/"], args.verbose)
    elif args.branches:
        raw = "\n".join(args.branches)
    else:
        raw = run_command(["git", "for-each-ref", "--format=%(refname)", "refs/heads/"], args.verbose)
    
    targets = [t.strip() for t in raw.splitlines() if t.strip()]
    if not targets:
        print(f"{RED}Error: No branches found.{RESET}"); sys.exit(1)

    # 2. Execute Primary Search (Gather initial hits)
    # If must-not is used alone, we still need to find files. 
    # But usually we search for MUST/CAN first.
    search_terms = list(set(args.must_have + args.can_have))
    data = collections.defaultdict(lambda: collections.defaultdict(list))
    
    if search_terms:
        grep_cmd = ["git", "grep", "-I", "-n", "--full-name"]
        if args.regex: grep_cmd.append("-E")
        for t in search_terms: grep_cmd.extend(["-e", t])
        
        results = run_command(grep_cmd + targets, args.verbose).splitlines()
        for line in results:
            parts = line.split(":", 3)
            if len(parts) < 4: continue
            ref, path, lnum, content = parts
            
            # Find which terms triggered this line
            hits = [t for t in search_terms if (re.search(t, content) if args.regex else t in content)]
            
            display_name = ref.replace("refs/heads/", "").replace("refs/remotes/", "")
            data[ref][path].append({
                "branch": display_name, "ref": ref, "file": path,
                "line": int(lnum), "content": content.strip(), "terms": hits,
                "term": hits[0] if hits else ""
            })

    # 3. Filtering & Boolean Logic Engine
    final_output = []
    seen_brief = set()

    for ref in targets:
        b_files = data.get(ref, {})
        # Aggregate all terms found across the entire branch
        b_all_terms = {t for ms in b_files.values() for m in ms for t in m['terms']}
        display_branch = ref.replace("refs/heads/", "").replace("refs/remotes/", "")

        # --- BRANCH SCOPE ---
        if args.scope == "branch":
            must_pass = all(m in b_all_terms for m in args.must_have)
            can_pass = (not args.can_have) or any(c in b_all_terms for c in args.can_have)
            
            if must_pass and can_pass:
                # Check Branch-wide Must-Not (Must not exist anywhere in branch)
                forbidden = False
                for n in args.must_not_have:
                    # git grep -q returns 0 if found
                    check_cmd = ["git", "grep", "-q"]
                    if args.regex: check_cmd.append("-E")
                    check_cmd.extend([n, ref])
                    
                    # We check the returncode directly
                    if subprocess.run(check_cmd, capture_output=True).returncode == 0:
                        forbidden = True; break
                
                if not forbidden:
                    if args.brief:
                        if display_branch not in seen_brief:
                            print(f"{CYAN}[{display_branch}]{RESET}")
                            seen_brief.add(display_branch)
                    else:
                        for ms in b_files.values(): final_output.extend(ms)
        
        # --- FILE SCOPE ---
        else:
            for path, ms in b_files.items():
                f_terms = {t for m in ms for t in m['terms']}
                must_pass = all(m in f_terms for m in args.must_have)
                can_pass = (not args.can_have) or any(c in f_terms for c in args.can_have)
                
                if must_pass and can_pass:
                    # Check File-specific Must-Not
                    forbidden = False
                    for n in args.must_not_have:
                        check_cmd = ["git", "grep", "-q"]
                        if args.regex: check_cmd.append("-E")
                        check_cmd.extend([n, f"{ref}:{path}"])
                        
                        if subprocess.run(check_cmd, capture_output=True).returncode == 0:
                            forbidden = True; break
                    
                    if not forbidden:
                        if args.brief:
                            brief_key = f"{display_branch}:{path}"
                            if brief_key not in seen_brief:
                                print(f"{CYAN}[{display_branch}]{RESET} {GREEN}{path}{RESET}")
                                seen_brief.add(brief_key)
                        else:
                            final_output.extend(ms)

    # 4. Sorting & Output (Non-brief)
    if not args.brief:
        if not final_output:
            print(f"{YELLOW}No matches found matching the criteria.{RESET}")
            return

        key_map = {"branch": "branch", "file": "file", "line": "line", "term": "term"}
        s_keys = [k.strip() for k in args.sort_by.split(",")]
        final_output.sort(key=lambda x: tuple(x.get(key_map.get(k, "branch")) for k in s_keys if k in key_map))

        for r in final_output:
            t_str = f"[{', '.join(r['terms'])}]"
            l_str = f"- {r['content']}" if args.show_line else ""
            print(f"{CYAN}[{r['branch']}]{RESET} {GREEN}{r['file']}{RESET}:{r['line']} {RED}{t_str}{RESET} {l_str}")

if __name__ == "__main__":
    main()
