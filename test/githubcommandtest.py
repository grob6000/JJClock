import subprocess

def doGitCommand(_CMD):
  githubuser = "grob6000"
  githubpass = "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"
  if (_CMD[0] == "git"):
    with subprocess.Popen(_CMD, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        p.communicate(githubuser + "\n" + githubpass + "\n")

doGitCommand(["git", "tags"])