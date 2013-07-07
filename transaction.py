#
# Code for dumping a single transaction, given its ID
#

from bsddb.db import *
from datetime import datetime
import logging
import os.path
import sys
import time

from BCDataStream import *
from base58 import public_key_to_bc_address
from block import scan_blocks
from util import short_hex
from deserialize import *

def _read_CDiskTxPos(stream):
  n_file = stream.read_uint32()
  n_block_pos = stream.read_uint32()
  n_tx_pos = stream.read_uint32()
  return (n_file, n_block_pos, n_tx_pos)

def _dump_tx(datadir, tx_hash, tx_pos):
  blockfile = open(os.path.join(datadir, "blk%04d.dat"%(tx_pos[0],)), "rb")
  ds = BCDataStream()
  ds.map_file(blockfile, tx_pos[2])
  d = parse_Transaction(ds)
  print deserialize_Transaction(d)
  ds.close_file()
  blockfile.close()

def dump_transaction(datadir, db_env, tx_id):
  """ Dump a transaction, given hexadecimal tx_id-- either the full ID
      OR a short_hex version of the id.
  """
  db = DB(db_env)
  try:
    r = db.open("blkindex.dat", "main", DB_BTREE, DB_THREAD|DB_RDONLY)
  except DBError:
    r = True

  if r is not None:
    logging.error("Couldn't open blkindex.dat/main.  Try quitting any running Bitcoin apps.")
    sys.exit(1)

  kds = BCDataStream()
  vds = BCDataStream()

  n_tx = 0
  n_blockindex = 0

  key_prefix = "\x02tx"+(tx_id[-4:].decode('hex_codec')[::-1])
  cursor = db.cursor()
  (key, value) = cursor.set_range(key_prefix)

  while key.startswith(key_prefix):
    kds.clear(); kds.write(key)
    vds.clear(); vds.write(value)

    type = kds.read_string()
    hash256 = (kds.read_bytes(32))
    hash_hex = long_hex(hash256[::-1])
    version = vds.read_uint32()
    tx_pos = _read_CDiskTxPos(vds)
    if (hash_hex.startswith(tx_id) or short_hex(hash256[::-1]).startswith(tx_id)):
      _dump_tx(datadir, hash256, tx_pos)

    (key, value) = cursor.next()

  db.close()


def parse_block_from_block_data(datadir, block_data):
    blockfile = open(os.path.join(datadir, "blk%04d.dat"%(block_data['nFile'],)), "rb")

    ds = BCDataStream()
    ds.map_file(blockfile, block_data['nBlockPos'])
    data = parse_Block(ds)
    ds.close_file()

    return data

def find_address_from_previous_txn(datadir, db_env, txnHash, txnOutPos):

  db = DB(db_env)
  try:
    r = db.open("blkindex.dat", "main", DB_BTREE, DB_THREAD|DB_RDONLY)
  except DBError:
    r = True

  if r is not None:
    logging.error("Couldn't open blkindex.dat/main.  Try quitting any running Bitcoin apps.")
    sys.exit(1)

  kds = BCDataStream()
  vds = BCDataStream()

  n_tx = 0
  n_blockindex = 0

  key_prefix = "\x02tx"+(txnHash[-4:].decode('hex_codec')[::-1])
  cursor = db.cursor()
  (key, value) = cursor.set_range(key_prefix)

  while key.startswith(key_prefix):
    kds.clear(); kds.write(key)
    vds.clear(); vds.write(value)

    type = kds.read_string()
    hash256 = (kds.read_bytes(32))
    hash_hex = long_hex(hash256[::-1])
    version = vds.read_uint32()
    tx_pos = _read_CDiskTxPos(vds)
    if (hash_hex.startswith(txnHash) or short_hex(hash256[::-1]).startswith(txnHash)):
      blockfile = open(os.path.join(datadir, "blk%04d.dat"%(tx_pos[0],)), "rb")
      ds        = BCDataStream()
      ds.map_file(blockfile, tx_pos[2])
      txn = parse_Transaction(ds)
      txOuts = txn['txOut']
      txOut = txOuts[txnOutPos]

      db.close()
      return extract_public_key(txOut['scriptPubKey'])


    (key, value) = cursor.next()

  db.close()
  return "(None)"


def make_none_public_key_from_txn(txnHash, n):
  return "None_" + str(txnHash) + "_" + str(n)


def dump_all_transactions(datadir, db_env):
  """ Dump all transactions.
  """
  def for_each_block(block_data):
    try:
      data = parse_block_from_block_data(datadir, block_data)

      block_datetime = datetime.fromtimestamp(data['nTime'])
      dt = "%d-%02d-%02d-%02d-%02d-%02d"%(block_datetime.year, block_datetime.month, block_datetime.day, block_datetime.hour, block_datetime.minute, block_datetime.second)

      blockHeight = block_data['nHeight']

      for txn in data['transactions']:
        try:
          for txIn in txn['txIn']:
            try:
              if txIn['prevout_hash'] == "\x00"*32:
                print 'in\t' + txn['hash'] + '\tcoinbase\t' + dt
              else:
                pk = extract_public_key(txIn['scriptSig'])

                txnHash = long_hex(txIn['prevout_hash'][::-1])
                txnPrevOutN = txIn['prevout_n']

                if pk == "(None)":
                  pk = find_address_from_previous_txn(datadir, db_env, txnHash, txnPrevOutN)

                  if pk == "(None)":
                    pk = make_none_public_key_from_txn(txnHash, txnPrevOutN)

                print 'in\t' + txn['hash'] + '\t' + str(txnHash) + '\t' + str(txnPrevOutN) + '\t' + pk + '\t' + dt + '\t' + str(blockHeight)

            except Exception, err:
              txInKeyDecoded = [ x for x in script_GetOp(txIn['scriptSig']) ]
              txkeytxt = "["+','.join([public_key_to_bc_address(txInKeyDecoded[i][1]) for i in range(1,len(txInKeyDecoded)-2)])+"]"


              print 'error_txIn\t' + str(blockHeight) + '\t' + str(err) + '\t' + str(txInKeyDecoded) + '\t' + str(txkeytxt) + '\t' + str(txIn) + '\t' + str(txn)
          txnOutN = 0
          for txOut in txn['txOut']:
            try:
              pk = extract_public_key(txOut['scriptPubKey'])
              txnHash = txn['hash']

              if pk == "(None)":
                pk = make_none_public_key_from_txn(txnHash, txnOutN)
              # txOutKeyDecoded = [ x for x in script_GetOp(bytes) ]

              print 'out\t' + txnHash + '\t' + str(txnOutN) + '\t' + pk + '\t' + str(txOut['value']/1.0e8) + '\t' + dt + '\t' + str(blockHeight)

            except Exception, err:
              print 'error_txOut\t' + str(blockHeight) + '\t' + str(err) + '\t' + str(txOut) + '\t' + str(txn)


            txnOutN += 1

        except Exception, err:
          print 'error\t' + str(blockHeight) + '\t' + str(err) + '\t' + str(txn)

    except Exception, err:
        print 'error_block\t' + str(block_data['nHeight'])  + '\t' + str(err)

    return True

  scan_blocks(datadir, db_env, for_each_block)
  db_env.close()


