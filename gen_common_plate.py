#coding=utf-8

"""
此脚本用于生成车牌图像。
主要功能包括：
1. 绘制和生成特定格式的车牌图像。
2. 处理和调整车牌图像的颜色和噪声。
3. 批量生成车牌图像，并保存到指定目录。

使用方法：
1. 指定中文和英文字体文件路径。
2. 指定无车牌图像的背景目录。
3. 指定输出目录和生成图像的数量。
"""

import os
import argparse
from math import *
import numpy as np
import cv2
import copy
from PIL import Image, ImageFont, ImageDraw
from PlateCommon import *  # 引入自定义的车牌生成通用函数

class GenPlate:
    def __init__(self, fontCh, fontEng, NoPlates):
        # 初始化，加载中文和英文字体
        self.fontC = ImageFont.truetype(fontCh, 43, 0)  # 中文字体
        self.fontE = ImageFont.truetype(fontEng, 60, 0)  # 英文字体
        # 创建一个空白的车牌图像
        self.img = np.array(Image.new("RGB", (226, 70), (255, 225, 225)))
        # 读取车牌背景模板
        self.bg = cv2.resize(cv2.imread("./images/template1.bmp"), (226, 70))
        # 读取污损图像
        self.smu = cv2.imread("./images/smu2.jpg")
        # 加载无车牌图像路径
        self.noplates_path = []
        for parent, parent_folder, filenames in os.walk(NoPlates):
            for filename in filenames:
                path = parent + "/" + filename
                self.noplates_path.append(path)

    def draw(self, val):
        """
        绘制车牌图像
        :param val: 车牌字符列表
        :return: 生成的车牌图像
        """
        offset = 2  # 偏移量
        # 绘制车牌的第一个字符（省份简称）
        self.img[0:70, offset + 8:offset + 8 + 23] = GenCh(self.fontC, val[0])
        # 绘制车牌的第二个字符（英文字母）
        self.img[0:70, offset + 8 + 23 + 6:offset + 8 + 23 + 6 + 23] = GenCh1(self.fontE, val[1])
        # 绘制车牌的后五个字符（数字或字母）
        for i in range(5):
            base = offset + 8 + 23 + 6 + 23 + 17 + i * 23 + i * 6
            self.img[0:70, base: base + 23] = GenCh1(self.fontE, val[i + 2])
        return self.img

    def generate(self, text):
        """
        生成车牌图像
        :param text: 车牌字符串
        :return: 生成的车牌图像
        """
        if len(text) == 9:
            # 得到白底黑字的车牌图像
            fg = self.draw(text.decode(encoding="utf-8"))

            # 在普通车牌上添加白字
            com = copy.deepcopy(self.bg)
            for i in range(70):
                for j in range(226):
                    for c in range(3):
                        if fg[i, j, c] == 0:
                            com[i, j, c] = 255

            # 随机环境处理
            com = random_envirment(com, self.noplates_path)
            # 添加高斯模糊
            com = AddGauss(com, 1 + r(2))
            # 添加噪声
            com = addNoise(com)
            return com

    def genPlateString(self, pos, val):
        """
        生成车牌字符串
        :param pos: 指定位置
        :param val: 指定字符
        :return: 生成的车牌字符串
        """
        plateStr = ""
        box = [0, 0, 0, 0, 0, 0, 0]
        if pos != -1:
            box[pos] = 1
        for unit, cpos in zip(box, range(len(box))):
            if unit == 1:
                plateStr += val
            else:
                if cpos == 0:
                    plateStr += chars[r(31)]
                elif cpos == 1:
                    plateStr += chars[41 + r(24)]
                else:
                    plateStr += chars[31 + r(34)]
        return plateStr

    def genBatch(self, batchSize, pos, charRange, outputPath, size):
        """
        批量生成车牌图像
        :param batchSize: 生成数量
        :param pos: 指定位置
        :param charRange: 字符范围
        :param outputPath: 输出目录
        :param size: 图像尺寸
        """
        if not os.path.exists(outputPath):
            os.makedirs(outputPath)
        for i in range(batchSize):
            plateStr = self.genPlateString(-1, -1)
            img = self.generate(plateStr)
            img = cv2.resize(img, size)
            filename = os.path.join(outputPath, str(i).zfill(5) + '_' + plateStr + ".jpg")
            cv2.imwrite(filename, img)
            print(filename, plateStr)

def parse_args():
    """
    解析命令行参数
    :return: 解析后的参数
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--font_ch', default='./font/platech.ttf', help='中文字体文件路径')
    parser.add_argument('--font_en', default='./font/platechar.ttf', help='英文字体文件路径')
    parser.add_argument('--bg_dir', default='./NoPlates', help='无车牌图像背景目录')
    parser.add_argument('--out_dir', default='./data/common_plate', help='输出目录')
    parser.add_argument('--make_num', default=100, type=int, help='生成图像的数量')
    parser.add_argument('--img_w', default=120, type=int, help='输出图像宽度')
    parser.add_argument('--img_h', default=32, type=int, help='输出图像高度')
    return parser.parse_args()

def main(args):
    """
    主函数，生成车牌图像
    :param args: 命令行参数
    """
    G = GenPlate(args.font_ch, args.font_en, args.bg_dir)
    G.genBatch(args.make_num, 2, list(range(31, 65)), args.out_dir, (args.img_w, args.img_h))

if __name__ == '__main__':
    main(parse_args())
