/*
  * Tencent is pleased to support the open source community by making GameAISDK available.

  * This source code file is licensed under the GNU General Public License Version 3.
  * For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

  * Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
*/

#ifndef GAME_AI_SDK_IMGPROC_COMM_UTILS_BASE64_H_
#define GAME_AI_SDK_IMGPROC_COMM_UTILS_BASE64_H_

#include <iostream>
#include <string>

// base 64的映射表，string的下标表示数字，对应的字符为转换后的字符
// 如 0-->A, 1-->B, 2-->C
static const std::string base64_chars =
"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
"abcdefghijklmnopqrstuvwxyz"
"0123456789+/";

static inline bool is_base64(const char c) {
    return (isalnum(c) || (c == '+') || (c == '/'));
}

std::string base64_encode(const char *bytes_to_encode, unsigned int in_len) {
    std::string   ret;
    int           i = 0;
    int           j = 0;
    unsigned char char_array_3[3];
    unsigned char char_array_4[4];

    while (in_len--) {
        char_array_3[i++] = *(bytes_to_encode++);
        if (i == 3) {
            // 取出第一个字符的前6位
            char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;

            // 取出第一个字符的后2位和第二个字符的前4位
            char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);

            // 取出第二个字符的后4位和第三个字符的前2位
            char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);

            // 取出第三个字符的后6位
            char_array_4[3] = char_array_3[2] & 0x3f;

            for (i = 0; (i < 4); i++) {
                // 找出对应的编码字符
                ret += base64_chars[char_array_4[i]];
            }

            i = 0;
        }
    }

    if (i) {
        // 不是3的倍数,在后面补0加“=”
        for (j = i; j < 3; j++) {
            char_array_3[j] = '\0';
        }

        // 取出第一个字符的前6位
        char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;

        // 取出第一个字符的后2位和第二个字符的前4位
        char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);

        // 取出第二个字符的后4位和第三个字符的前2位
        char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);

        // 取出第三个字符的后6位
        char_array_4[3] = char_array_3[2] & 0x3f;

        for (j = 0; (j < i + 1); j++) {
            // 找出对应的编码字符
            ret += base64_chars[char_array_4[j]];
        }

        while ((i++ < 3)) {
            ret += '=';
        }
    }

    return ret;
}

std::string base64_decode(std::string const &encoded_string) {
    int           in_len = static_cast<int>(encoded_string.size());
    int           i = 0;
    int           j = 0;
    int           in_ = 0;
    unsigned char char_array_4[4], char_array_3[3];
    std::string   ret;

    while (in_len-- && (encoded_string[in_] != '=') && is_base64(encoded_string[in_])) {
        char_array_4[i++] = encoded_string[in_]; in_++;
        if (i == 4) {
            // 转换为base 64的映射表的十进制数(A-->0, B-->1, C-->2)
            for (i = 0; i < 4; i++)
                char_array_4[i] = base64_chars.find(char_array_4[i]);

            // 第一个数字的前6位与第二个数字前2位进行组合
            char_array_3[0] = (char_array_4[0] << 2) + ((char_array_4[1] & 0x30) >> 4);

            // 第二个数字的后4位与第三个字符对应的前4位进行组合
            char_array_3[1] = ((char_array_4[1] & 0xf) << 4) + ((char_array_4[2] & 0x3c) >> 2);

            // 第三个字符对应的后2位和第四个数字进行组合
            char_array_3[2] = ((char_array_4[2] & 0x3) << 6) + char_array_4[3];

            for (i = 0; (i < 3); i++)
                ret += char_array_3[i];

            i = 0;
        }
    }

    if (i) {
        // 不是4的倍数,在后面补0
        for (j = i; j < 4; j++)
            char_array_4[j] = 0;

        // 转换为base 64的映射表的十进制数(A-->0, B-->1, C-->2)
        for (j = 0; j < 4; j++)
            char_array_4[j] = base64_chars.find(char_array_4[j]);

        // 第一个数字的前6位与第二个数字前2位进行组合
        char_array_3[0] = (char_array_4[0] << 2) + ((char_array_4[1] & 0x30) >> 4);

        // 第二个数字的后4位与第三个字符对应的前4位进行组合
        char_array_3[1] = ((char_array_4[1] & 0xf) << 4) + ((char_array_4[2] & 0x3c) >> 2);

        // 第三个字符对应的后2位和第四个数字进行组合
        char_array_3[2] = ((char_array_4[2] & 0x3) << 6) + char_array_4[3];

        for (j = 0; (j < i - 1); j++)
            ret += char_array_3[j];
    }

    return ret;
}
#endif  // GAME_AI_SDK_IMGPROC_COMM_UTILS_BASE64_H_
