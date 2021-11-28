#!/usr/bin/env python3
"""Utility script to use the hashOverride option to split files into parts."""

from typing import Any

import hashlib
import sys


MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1 GiB
ALIGN_PIECE_LENGTH = False


# Bencode

def bencode_to_python(benc: bytes, offset: int = 0) -> (Any, int):
  # Note: benc is assumed to be a valid Bencode encoded message.

  if benc[offset:offset + 1] == b'i':  # Integer
    endidx = benc.index(b'e', offset + 1)
    return int(benc[offset + 1: endidx]), endidx + 1

  if benc[offset:offset + 1].isdigit():  # String (bytes)
    mididx = benc.index(b':', offset + 1)
    length = int(benc[offset:mididx])
    return benc[mididx + 1:mididx + 1 + length], mididx + 1 + length

  if benc[offset:offset + 1] == b'l':  # List
    offset += 1
    result = []
    while benc[offset:offset + 1] != b'e':
      item, offset = bencode_to_python(benc, offset)
      result.append(item)
    return result, offset + 1

  if benc[offset:offset + 1] == b'd':  # Dictionary
    offset += 1
    result = {}
    while benc[offset:offset + 1] != b'e':
      key, offset = bencode_to_python(benc, offset)
      value, offset = bencode_to_python(benc, offset)
      result[key] = value
    return result, offset + 1

  raise ValueError(f'Unexpected character: {benc[offset]}')


def python_to_bencode(obj: Any) -> bytes:
  if isinstance(obj, str):
    obj = obj.encode('utf-8')
  if isinstance(obj, int):  # Integer
    return f'i{obj}e'.encode('utf-8')
  if isinstance(obj, bytes):  # String (bytes)
    return f'{len(obj)}:'.encode('utf-8') + obj
  if isinstance(obj, list):  # List
    return b'l' + b''.join(python_to_bencode(v) for v in obj) + b'e'
  if isinstance(obj, dict):  # Dictionary
    return b'd' + b''.join(
      python_to_bencode(key) + python_to_bencode(value)
      for key, value in sorted(obj.items())) + b'e'
  raise ValueError(f'Unexpected type: {type(obj)}')


# Torrent update

def split_files(torrent: Any) -> None:
  has_split = False
  all_filenames = {b'/'.join(file[b'path'])
                   for file in torrent[b'info'][b'files']}
  new_files = []
  offset = 0
  piece_length = torrent[b'info'][b'piece length']
  for file in torrent[b'info'][b'files']:
    file_size = file[b'length']
    if file_size > MAX_FILE_SIZE:
      parts = []
      if ALIGN_PIECE_LENGTH and offset % piece_length > 0:
        parts.append(piece_length - (offset % piece_length))
        file_size -= parts[0]
        offset += parts[0]
      while file_size >= MAX_FILE_SIZE:
        parts.append(MAX_FILE_SIZE)
        file_size -= MAX_FILE_SIZE
        offset += MAX_FILE_SIZE
      if file_size > 0:
        if (ALIGN_PIECE_LENGTH and file_size > piece_length and
            (offset + file_size) % piece_length > 0):
          last_part = (offset + file_size) % piece_length
          parts.append(file_size - last_part)
          parts.append(last_part)
        else:
          parts.append(file_size)
        offset += file_size
      for i, part in enumerate(parts):
        new_file = dict(file)
        new_file[b'length'] = part
        new_file[b'path'] = list(file[b'path'])
        new_file[b'path'][-1] += f'.part{i}'.encode('utf-8')
        if b'/'.join(new_file[b'path']) in all_filenames:
          raise RuntimeError('Some files already also have parts')
        new_files.append(new_file)
      has_split = True
    else:
      new_files.append(file)
      offset += file_size
  if has_split:
    m = hashlib.sha1()
    m.update(python_to_bencode(torrent[b'info']))
    torrent[b'hashOverride'] = m.digest()
    torrent[b'info'][b'files'] = new_files
  return has_split


# CLI

if __name__ == '__main__':
  if len(sys.argv) != 3:
    print(f'Usage: {argv[0]} infile.torrent outfile.torrent')
  with open(sys.argv[1], 'rb') as f:
    in_data = f.read()
  torrent = bencode_to_python(in_data)[0]
  if in_data != python_to_bencode(torrent):
    raise ValueError('The sanity check on the torrent file did not pass')
  has_split = split_files(torrent)
  with open(sys.argv[2], 'wb') as f:
    f.write(python_to_bencode(torrent))
  print(f'Done (modified: {has_split}).')

