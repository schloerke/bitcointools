#!/usr/bin/env python
#
# Read the block database, generate monthly statistics and dump out
# a CSV file.
#
from bsddb.db import *
from datetime import date
import logging
import os
import sys

from BCDataStream import *
from block import scan_blocks
from deserialize import parse_Block
from util import determine_db_dir

def main():
  import optparse
  parser = optparse.OptionParser(usage="%prog [options]")
  parser.add_option("--datadir", dest="datadir", default=None,
                    help="Look for files here (defaults to bitcoin default)")
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

  blockfile = open(os.path.join(db_dir, "blk%04d.dat"%(1,)), "rb")
  block_datastream = BCDataStream()
  block_datastream.map_file(blockfile, 0)

  n_transactions = { }
  v_transactions = { }
  def gather_stats(block_data):
    block_datastream.seek_file(block_data['nBlockPos'])
    data = parse_Block(block_datastream)
    block_date = date.fromtimestamp(data['nTime'])
    key = "%d-%02d"%(block_date.year, block_date.month)
    for txn in data['transactions'][1:]:
      for txout in txn['txOut']:
        if key in n_transactions:
          n_transactions[key] += 1
          v_transactions[key] += txout['value'] 
        else:
          n_transactions[key] = 1
          v_transactions[key] = txout['value'] 
    return True

  scan_blocks(db_dir, db_env, gather_stats)

  db_env.close()

  keys = n_transactions.keys()
  keys.sort()
  for k in keys:
    v = v_transactions[k]/1.0e8
    print "%s,%d,%.2f"%(k, n_transactions[k], v)

if __name__ == '__main__':
    main()
