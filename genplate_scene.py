#coding=utf-8

'''
生成车牌数据，将车牌放到自然图像中
'''

import os
import numpy as np
import cv2
import argparse
from PIL import ImageFont, Image, ImageDraw
from math import *

from PlateCommon import *  # 引入自定义的车牌生成通用函数

TEMPLATE_IMAGE = "./images/template.bmp"
# 这里假设车牌最小的检测尺寸是65*21，检测车牌的最小图像为65*21，车牌宽高比变化范围是(1.5, 4.0)
PLATE_SIZE_MIN = (65, 21)

class GenPlateScene:
    '''车牌数据生成器，将车牌放在自然场景中，位置信息存储在同名的txt文件中
    '''
    def __init__(self, fontCh, fontEng, NoPlates):
        '''
        初始化车牌生成器
        :param fontCh: 中文字体文件路径
        :param fontEng: 英文字体文件路径
        :param NoPlates: 无车牌图像的背景目录
        '''
        self.fontC = ImageFont.truetype(fontCh, 43, 0)    # 省简称使用字体
        self.fontE = ImageFont.truetype(fontEng, 60, 0)   # 字母数字字体
        # 创建一个空白的车牌图像
        self.img = np.array(Image.new("RGB", (226, 70), (255, 255, 255)))
        # 读取车牌背景模板
        self.bg = cv2.resize(cv2.imread(TEMPLATE_IMAGE), (226, 70))
        # 加载无车牌图像路径
        self.noplates_path = []
        for parent, _, filenames in os.walk(NoPlates):
            for filename in filenames:
                self.noplates_path.append(parent + "/" + filename)

    def gen_plate_string(self):
        '''生成车牌号码字符串'''
        plate_str = ""
        for cpos in range(7):
            if cpos == 0:
                plate_str += chars[r(31)]  # 生成省份简称
            elif cpos == 1:
                plate_str += chars[41 + r(24)]  # 生成英文字母
            else:
                plate_str += chars[31 + r(34)]  # 生成字母或数字
        return plate_str

    def draw(self, val):
        '''绘制车牌图像'''
        offset = 2
        self.img[0:70, offset+8:offset+8+23] = GenCh(self.fontC, val[0])  # 绘制省份简称
        self.img[0:70, offset+8+23+6:offset+8+23+6+23] = GenCh1(self.fontE, val[1])  # 绘制字母
        for i in range(5):
            base = offset + 8 + 23 + 6 + 23 + 17 + i * 23 + i * 6
            self.img[0:70, base:base + 23] = GenCh1(self.fontE, val[i + 2])  # 绘制后续的字母或数字
        return self.img

    def generate(self, text):
        '''生成带有自然背景的车牌图像'''
        print(text, len(text))
        fg = self.draw(text.decode(encoding="utf-8"))  # 得到白底黑字的车牌
        fg = cv2.bitwise_not(fg)  # 反转颜色，得到黑底白字
        com = cv2.bitwise_or(fg, self.bg)  # 字放到（蓝色）车牌背景中
        com = rot(com, r(60) - 30, com.shape, 30)  # 矩形变成平行四边形
        com = rotRandrom(com, 10, (com.shape[1], com.shape[0]))  # 随机旋转
        com = tfactor(com)  # 调整灰度

        com, loc = random_scene(com, self.noplates_path)  # 放入背景中
        if com is None or loc is None:
            return None, None

        com = AddGauss(com, 1 + r(4))  # 添加高斯模糊
        com = addNoise(com)  # 添加噪声
        return com, loc

    def gen_batch(self, batchSize, outputPath):
        '''批量生成图片'''
        if not os.path.exists(outputPath):
            os.mkdir(outputPath)
        for i in range(batchSize):
            plate_str = self.gen_plate_string()
            img, loc = self.generate(plate_str)
            if img is None:
                continue
            cv2.imwrite(outputPath + "/" + str(i).zfill(2) + ".jpg", img)
            with open(outputPath + "/" + str(i).zfill(2) + ".txt", 'w') as obj:
                line = ','.join([str(v) for v in loc]) + ',"' + plate_str + '"\n'
                obj.write(line)

def parse_args():
    '''解析命令行参数'''
    parser = argparse.ArgumentParser()
    parser.add_argument('--bg_dir', default='/Users/zhangxin/data/OCR/SynthText/bg_img', help='背景图像目录')
    parser.add_argument('--out_dir', default='./plate_train/', help='输出目录')
    parser.add_argument('--make_num', default=10000, type=int, help='生成图像的数量')
    return parser.parse_args()

def main(args):
    '''主函数，生成车牌图像'''
    G = GenPlateScene("./font/platech.ttf", './font/platechar.ttf', args.bg_dir)
    G.gen_batch(args.make_num, args.out_dir)

if __name__ == '__main__':
    main(parse_args())
