import subprocess

def doGitCommand(_CMD):
  githubuser = "grob6000"
  githubpass = "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"
  if (_CMD[0] == "git"):
    with subprocess.Popen(_CMD, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        o,e = p.communicate((githubuser + "\n" + githubpass + "\n").encode())
    print("o: " + o.decode())
    print("e: " + e.decode())

doGitCommand(["git", "pull"])
