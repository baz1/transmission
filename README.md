# Transmission by parts

This repository is a fork of https://github.com/transmission/transmission with
the added capability to split large files into parts that can be downloaded
separately.

Use
[split_files.py](https://github.com/baz1/transmission/blob/master/split_files.py)
to create copies of existing torrents with large files split into parts
(see constant at the top for the maximum file size).

The modified `.torrent` file that this script produces can then only be used
with the modified transmission binary from this fork.

## Details

A small change in the forked transmission binary adds an optional `hashOverride`
entry in the torrent's bencode, which is then used instead of the hash of the
`info` entry.
This is needed because that infohash is used to identify the torrent with the
tracker and peers.

The python script then makes use of it to be able to change the list of files
while preserving the original infohash.

Everything else works fine since the protocol does not further involve the files
architecture in anything else than the infohash. The order of the parts just
needs to be maintained since the pieces data corresponds to the concatenated
file content.

