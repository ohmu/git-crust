#!/usr/bin/env python
"""
git-fixup - Automate the workflow of 'git commit {--fixup,--squash}'

  For each modified file, finds the latest commit X, that has changes
  to the same file and commits the changes with 'git commit --fixup=X'.

Github:

  https://github.com/ohmu/git-crust

License:

  MIT, https://github.com/ohmu/git-crust/LICENSE

Installation:

  Link/move/symlink this script somewhere in your $PATH as "git-fixup".

Usage:

    git fixup -h            # Show help
    git fixup               # View changes
    git fixup -a            # Commit all changes
    git fixup <file> [...]  # Commit only some changes
    git fixup -s            # Commit with --squash instead of --fixup
    git fixup -r            # 'git rebase --autosquash -i' all fixup commits
                            # over the nearest possible commit

Notes:

  * Older git version do not handle "rebase --autosquash" properly when
    there are commits that start with multiple levels of
    "fixup! fixup! fixup! ...", etc. Upgrading to a more recent git version
    helps (at least 1.9.1 and newer work ok).

"""
import subprocess
import optparse
import sys


class Error(Exception):
    """gix-fixup error"""


def parse_args(args):
    parser = optparse.OptionParser()
    parser.add_option("-a", "--all", action="store_true",
                      help="commit all changes")
    parser.add_option("-d", "--diff", action="store_true",
                      help="show diff of changes")
    parser.add_option("-n", "--no-commit", action="store_true",
                      help="just show the changes, do not commit")
    parser.add_option("-s", "--squash", action="store_true",
                      help="use --squash=<commit> instead of --fixup=<commit>")
    parser.add_option("-r", "--rebase", action="store_true",
                      help="rebase all fixup commits automatically")

    return parser.parse_args()


def git(args, capture=True):
    args = ["git"] + args
    sub = subprocess.Popen(args,
                           stdout=subprocess.PIPE if capture else None,
                           stderr=subprocess.PIPE if capture else None)
    stdout, stderr = sub.communicate()
    if sub.returncode:
        raise Error("command {0!r} failed with exit code {1!r}, "
                    "stdout={2!r}, stderr={3!r}".format(
                        args, sub.returncode, stdout, stderr))
    return (stdout or "").splitlines()


def changed_files():
    for line in git(["status", "--porcelain"]):
        if line[1:2] != "M":
            # we only handle modified files
            continue
        yield line[3:]


def fixup(files, commit=False, diff=False, squash=False):
    changes = {}
    desc = {}
    for file_path in files:
        parent, title = git(["log", "-n", "1", "--oneline",
                             "--", file_path])[0].split(" ", 1)
        children = changes.setdefault(parent, set())
        children.add(file_path)
        desc[parent] = title

    for commit_id, desc in desc.iteritems():
        print commit_id, desc
        for file_path in changes[commit_id]:
            if diff:
                for line in git(["--no-pager", "diff", file_path],
                                capture=False):
                    print line
            else:
                print "  ", file_path
        print

    if commit:
        for commit_id, files in changes.iteritems():
            git(["commit", "--squash" if squash else "--fixup",
                 commit_id] + list(files), capture=False)


def rebase_all():
    commits = [
        line.split(" ", 1)
        for line in git(["--no-pager", "log", "-n", "1000", "--oneline"])
    ]
    fixups = set([e[1].replace("fixup! ", "").replace("squash! ", "")
                  for e in commits
                  if e[1].startswith("fixup!") or e[1].startswith("squash!")])
    if not fixups:
        return
    parents = [e for e in commits if e[1] in fixups]
    if not parents:
        raise Error("could not find target for fixup/squashes: {0!r}".format(fixups))
    git(["rebase", "-i", "--autosquash", parents[-1][0] + "^"], capture=False)


def main(args):
    opt, files = parse_args(args)
    try:
        if opt.rebase:
            rebase_all()
        else:
            fixup(files or changed_files(),
                  commit=(not opt.no_commit and (opt.all or files)),
                  diff=opt.diff, squash=opt.squash)
    except Error as error:
        print "ERROR: {0.__class__.__name__}: {0}".format(error)
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
