# bitcointools

This is a fork from [harrigan](https://github.com/harrigan/bitcointools)'s extension from [gavinandresen](https://github.com/gavinandresen/bitcointools)'s bitcointools.  The changes made by [gavinandresen](https://github.com/gavinandresen/bitcointools) have been applied manually, rather than by merging.  Sorry.

There are two main additions in this fork.

1. instead of just passing over the transactions that cause an error, at least print an error and anything useful that could be used to debug it.
2. the code has been updated to read from multiple files (within harrigan's addition).

This fork is purely made for the purpose of exporting the whole database.  If you have other desires and wish to stay on the latest bleeding edge, please see [gavinandresen](https://github.com/gavinandresen/bitcointools)'s bitcointools.


# Requirements

I had issues trying to execute this code on an OSX machine because of the "by default" bsddb [not working](http://stackoverflow.com/questions/814041/how-to-fix-the-broken-bsddb-install-in-the-default-python-package-on-mac-os-x-10) on export.  I also had issues trying to use ```bitcoind``` on redhat.  Therefore, I downloaded all data on my OSX machine and transferred it to a redhat machine to export the bitcoin data to a human readable format.

Software Used
* Python - 2.7.3
* [bitcoind](https://github.com/bitcoin/bitcoin/archive/v0.7.2.tar.gz) - 0.7.2
  Read your corresponding  'build-*.txt' file to install the program


# My Install Script

File stucture looks like the following
<pre>
  ./bitcoin
    | - bitcoind
    | - bitcoin_data
    | - bitcoin_output
    | - bitcointools
</pre>

## Install bitcoind

```{bash}
cd ./bitcoin
wget https://github.com/bitcoin/bitcoin/archive/v0.7.2.tar.gz
tar -zxvf v0.7.2
mv -r bitcoin-0.7.2 bitcoind
rm v0.7.2
cd bitcoind
### READ AND PERFORM INSTALL DIRECTIONS in ./doc/build-*.txt
ls src | grep bitcoind # should return a result
```

## Import Data with ./bitcoind

To save you about 3+ days of computing, download [the torrent file of blocks/transactions](http://www.bitcointrading.com/forum/bitcoin-software/bitcoin-blockchain-data-torrent-read-this-it's-actually-important/).  The direct link is located [here](http://gtf.org/garzik/bitcoin/bootstrap.dat.torrent).  It is around 8.1 GB of data

Once that is finished downloading into a single file, import the bootstrap.dat file using ./bitcoind. This will take less than a day.

Note:
* It may not exit after the file is imported.  If this happens, it will be spinning on a message similar to "ERROR: Already imported block #######".  No big deal, just stop the ./bitcoind execution, as the file has been imported and the program is trying to import it again.
* The '-detachdb' flag is REQUIRED by the bitcointools program.
* The '-datadir' flag is used to make put the data into the same place when using different platforms.

```{bash}
cd ./bitcoin/bitcoind/src
./bitcoind -detachdb -datadir="../bitcoin_data" -loadblock="./bootstrap.dat"
```

If you would like to watch the import status of the ./bitcoind action, tail the debug.log file.

```{bash}
tail -f ./bitcoin/bitcoin_data/debug.log
```

Once you have imported the file, you can sync to the rest of the bitcoin world by doing.  This will connect to other peers in the network and download the data for you. Stop the program when you feel you have enough data.  This might take a 2-3 days.

```{bash}
cd ./bitcoin/bitcoind/src
./bitcoind -detachdb -datadir=../bitcoin_data
```


## Install bitcointools

```{bash}
cd ./bitcoin
git clone https://github.com/schloerke/bitcointools.git
cd bitcointools
```

# Exporting the Database

Exporting takes a non trivial amount of time.  On my redhat machine it would produce about a 1 MB a second.  However, there was more than 14.5 GB of output into a single file.

```{bash}
cd ./bitcoin/bitcointools
mkdir ../bitcoin_output

# check to make sure it works
python ./dbdump.py --datadir=../bitcoin_data --block=244150

# Export the whole library...
python ./dbdump.py --datadir=../bitcoin_data --all-transactions > "../bitcoin_output/transactions.txt"
```


# Notes from gavin's orginal fork:

<pre>
NOTE:

These tools are becoming obsolete as we move away from using Berkeley DB in
Bitcoin-Qt/bitcoind.

If you are looking for a tool to manipulate the wallet.dat file, you might
want to try https://github.com/joric/pywallet

REQUIREMENTS:

You must run Bitcoin-Qt/bitcoind versions 0.6.0 through 0.7.* with the "-detachdb" option
or these tools will be unable to read the Berkeley DB files.

Now that the bitcoin blockchain is more than 2GB big, some of these tools will no longer
run on 32-bit systems!

Running on a 32-bit system will result in a 'Cannot allocate memory' error when the tools
try to mmap the second blk000?.dat file.

----- dbdump.py -----
Run    dbdump.py --help    for usage.  Database files are opened read-only, but
you might want to backup your Bitcoin wallet.dat file just in case.

You must quit Bitcoin before reading the transactions, blocks, or address database files.

Examples:

Print out  wallet keys and transactions:
  dbdump.py --wallet --wallet-tx

Print out the "genesis block" (the very first block in the proof-of-work block chain):
  dbdump.py --block=000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f

Print out one of the transactions from my wallet:
  dbdump.py --transaction=c6e1bf883bceef0aa05113e189982055d9ba7212ddfc879798616a0d0828c98c
  dbdump.py --transaction=c6e1...c98c

Print out all 'received' transactions that aren't yet spent:
  dbdump.py --wallet-tx-filter='fromMe:False.*spent:False'

Print out all blocks involving transactions to the Bitcoin Faucet:
  dbdump.py --search-blocks=15VjRaDX9zpbA8LVnbrCAFzrVzN7ixHNsC

There's a special search term to look for non-standard transactions:
  dbdump.py --search-blocks=NONSTANDARD_CSCRIPTS

----- statistics.py -----
Scan all the transactions in the block chain and dump out a .csv file that shows transaction volume per month.

----- fixwallet.py -----
Half-baked utility that reads a wallet.dat and writes out a new wallet.dat.

Only half-baked because to be really useful I'd have to write serialize routines to re-pack data after modifying it...

----- jsonToCSV.py -----
Read JSON list-of-objects from standard input, writes CSV file to standard output.
Useful for converting bitcoind's listtransactions output to CSV that can be
imported into a spreadsheet.
</pre>
