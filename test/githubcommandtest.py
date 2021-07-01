import subprocess

def doGitCommand(_CMD):
  githubuser = "grob6000"
  githubpass = "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"
  if (_CMD[0] == "git"):
    with subprocess.Popen(_CMD, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE) as p:
      for n in range(0,3):
        print("round " + str(n))
        try:
          o,e = p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
          print("timeout")
        if o:
          t = o.decode()
          if t.startswith("Username"):
            p.communicate(githubuser + "\n")
            print("gave username")
          elif t.startswith("Password"):
            p.communicate(githubpass + "\n")
            print("gave password")
            break
            
doGitCommand(["git", "pull"])
