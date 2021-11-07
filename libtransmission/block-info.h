/*
 * This file Copyright (C) Mnemosyne LLC
 *
 * It may be used under the GNU GPL versions 2 or 3
 * or any future license endorsed by Mnemosyne LLC.
 *
 */

#pragma once

#ifndef __TRANSMISSION__
#error only libtransmission should #include this header.
#endif

#include "transmission.h"

#include "torrent-metainfo.h"

struct tr_block_info
{
    uint64_t total_size = 0;
    uint64_t piece_size = 0;
    uint64_t n_pieces = 0;

    tr_block_index_t n_blocks = 0;
    tr_block_index_t n_blocks_in_piece = 0;
    tr_block_index_t n_blocks_in_final_piece = 0;
    uint32_t block_size = 0;
    uint32_t final_block_size = 0;
    uint32_t final_piece_size = 0;

    void initBlockInfo(uint64_t total_size_in, uint64_t piece_size_in);

    void initBlockInfo(tr_torrent_metainfo const& tm)
    {
        initBlockInfo(tm.total_size, tm.piece_size);
    }

    constexpr tr_piece_index_t pieceForBlock(tr_block_index_t block) const
    {
        return block / n_blocks_in_piece;
    }

    constexpr uint32_t countBytesInPiece(tr_piece_index_t piece) const
    {
        // how many bytes are in this piece?
        return piece + 1 == n_pieces ? final_piece_size : piece_size;
    }

    constexpr uint32_t countBytesInBlock(tr_block_index_t block) const
    {
        // how many bytes are in this block?
        return block + 1 == n_blocks ? final_block_size : block_size;
    }

    constexpr uint64_t totalOffset(tr_piece_index_t index, uint32_t offset, uint32_t length = 0) const
    {
        auto ret = piece_size;
        ret *= index;
        ret += offset;
        ret += length;
        return ret;
    }

    constexpr tr_block_range blockRangeForPiece(tr_piece_index_t piece) const
    {
        uint64_t offset = piece_size;
        offset *= piece;
        tr_block_index_t const first_block = offset / block_size;
        offset += countBytesInPiece(piece) - 1;
        tr_block_index_t const final_block = offset / block_size;

        return { first_block, final_block };
    }

    static uint32_t bestBlockSize(uint64_t piece_size);
};