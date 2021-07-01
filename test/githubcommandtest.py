import subprocess

def setGitCredentials():
  subprocess.run(["git", "config", "--local", "credential.helper", "store"])
  githubuser = "grob6000"
  githubpass = "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"
  data = "username={0}\npassword={1}\nhostname=github.com\nprotocol=https\n\n".format(githubuser,githubpass).encode()
  with subprocess.Popen(["git", "credential-store", "store"], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE) as p:
    p.communicate(data, timeout=5)

setGitCredentials()
