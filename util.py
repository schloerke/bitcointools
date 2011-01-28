#
# Misc util routines
#

def long_hex(bytes):
  return bytes.encode('hex_codec')

def short_hex(bytes):
  t = bytes.encode('hex_codec')
  if len(t) < 11:
    return t
  return t[0:4]+"..."+t[-4:]

def determine_db_dir():
  import os
  import os.path
  import platform
  if platform.system() == "Darwin":
    return os.path.expanduser("~/Library/Application Support/Bitcoin/")
  elif platform.system() == "Windows":
    return os.path.join(os.environ['APPDATA'], "Bitcoin")
  return os.path.expanduser("~/.bitcoin")
