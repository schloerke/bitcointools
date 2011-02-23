#!/usr/bin/env python
#
# Recover from a semi-corrupt wallet
#
from bsddb.db import *
import logging
import sys

from wallet import rewrite_wallet
from util import determine_db_dir

def main():
  import optparse
  parser = optparse.OptionParser(usage="%prog [options]")
  parser.add_option("--datadir", dest="datadir", default=None,
                    help="Look for files here (defaults to bitcoin default)")
  parser.add_option("--out", dest="outfile", default="walletNEW.dat",
                    help="Name of output file (default: walletNEW.dat)")
  parser.add_option("--skipkey", dest="skipkey",
                    help="Skip entries with keys that contain given string")
  parser.add_option("--tweakspent", dest="tweakspent",
                    help="Tweak transaction to mark unspent")
  (options, args) = parser.parse_args()

  if options.datadir is None:
    db_dir = determine_db_dir()
  else:
    db_dir = options.datadir

  db_env = DBEnv(0)
  r = db_env.open(db_dir,
                  (DB_CREATE|DB_INIT_LOCK|DB_INIT_LOG|DB_INIT_MPOOL|
                   DB_INIT_TXN|DB_THREAD|DB_RECOVER))

  if r is not None:
    logging.error("Couldn't open "+DB_DIR)
    sys.exit(1)

  if options.skipkey:
    def pre_put_callback(type, data):
      if options.skipkey in data['__key__']:
        return False
      return True
    rewrite_wallet(db_env, options.outfile, pre_put_callback)
  elif options.tweakspent:
    txid = options.tweakspent.decode('hex_codec')[::-1]
    def tweak_spent_callback(type, data):
      if txid in data['__key__']:
        import pdb
        pdb.set_trace()
        data['__value__'] = data['__value__'][:-1]+'\0'
      return True
    rewrite_wallet(db_env, options.outfile, tweak_spent_callback)
    pass
  else:
    rewrite_wallet(db_env, options.outfile)

  db_env.close()

if __name__ == '__main__':
    main()
