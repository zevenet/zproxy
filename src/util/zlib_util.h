// Created by fernando
#pragma once

#include <string>
#include <sstream>
#include <stdexcept>

#include <string.h>
#include <zlib.h>

using std::string;
using std::stringstream;

// http://mail-archives.apache.org/mod_mbox/trafficserver-dev/201110.mbox/%3CCACJPjhYf=+br1W39vyazP=ix
//eQZ-4Gh9-U6TtiEdReG3S4ZZng@mail.gmail.com%3E
#define MOD_GZIP_ZLIB_WINDOWSIZE 15
#define MOD_GZIP_ZLIB_CFACTOR    9
#define MOD_GZIP_ZLIB_BSIZE      8096

namespace  zlib {

  std::string compress_message_deflate(const std::string& str,
                              int compressionlevel = Z_BEST_COMPRESSION)
  {
      z_stream zs;                        // z_stream is zlib's control structure
      memset(&zs, 0, sizeof(zs));

      if (deflateInit(&zs, compressionlevel) != Z_OK)
          throw(std::runtime_error("deflateInit failed while compressing."));

      zs.next_in = (Bytef*)str.data();
      zs.avail_in = str.size();           // set the z_stream's input

      int ret;
      char outbuffer[32768];
      std::string outstring;

      // retrieve the compressed bytes blockwise
      do {
          zs.next_out = reinterpret_cast<Bytef*>(outbuffer);
          zs.avail_out = sizeof(outbuffer);

          ret = deflate(&zs, Z_FINISH);

          if (outstring.size() < zs.total_out) {
              // append the block to the output string
              outstring.append(outbuffer,
                               zs.total_out - outstring.size());
          }
      } while (ret == Z_OK);

      deflateEnd(&zs);

      if (ret != Z_STREAM_END) {          // an error occurred that was not EOF
          std::ostringstream oss;
          oss << "Exception during zlib compression: (" << ret << ") " << zs.msg;
          throw(std::runtime_error(oss.str()));
      }

      return outstring;
  }


  std::string compress_message_gzip(const std::string& str,
                               int compressionlevel = Z_BEST_COMPRESSION)
  {
      z_stream zs;                        // z_stream is zlib's control structure
      memset(&zs, 0, sizeof(zs));

      if (deflateInit2(&zs,
                       compressionlevel,
                       Z_DEFLATED,
                       MOD_GZIP_ZLIB_WINDOWSIZE + 16,
                       MOD_GZIP_ZLIB_CFACTOR,
                       Z_DEFAULT_STRATEGY) != Z_OK
      ) {
          throw(std::runtime_error("deflateInit2 failed while compressing."));
      }

      zs.next_in = (Bytef*)str.data();
      zs.avail_in = str.size();           // set the z_stream's input

      int ret;
      char outbuffer[32768];
      std::string outstring;

      // retrieve the compressed bytes blockwise
      do {
          zs.next_out = reinterpret_cast<Bytef*>(outbuffer);
          zs.avail_out = sizeof(outbuffer);

          ret = deflate(&zs, Z_FINISH);

          if (outstring.size() < zs.total_out) {
              // append the block to the output string
              outstring.append(outbuffer,
                               zs.total_out - outstring.size());
          }
      } while (ret == Z_OK);

      deflateEnd(&zs);

      if (ret != Z_STREAM_END) {          // an error occurred that was not EOF
          std::ostringstream oss;
          oss << "Exception during zlib compression: (" << ret << ") " << zs.msg;
          throw(std::runtime_error(oss.str()));
      }

      return outstring;
  }
} // namespace zlib
