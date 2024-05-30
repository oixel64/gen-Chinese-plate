#coding:utf8

"""
此脚本用于通过调整图像的角度和移除图像中的黑边来处理图像。
主要功能包括：
1. 将图像按照指定的角度进行旋转。
2. 通过透视变换来调整图像的视角。
3. 移除图像中的黑边部分，裁剪出有效区域。
"""

import os
import cv2
import numpy as np
import random
import copy
import sys

# 将角度转换为弧度
def rad(x):
    return x * np.pi / 180

# 改变图像的角度
def change_img_angle(img, anglex, angley, anglez):
    ih, iw = img.shape[:2]  # 获取图像的高度和宽度
    fov = 42  # 视场角（Field of View）
    # 计算镜头与图像之间的距离，21为半可视角，计算z的距离以确保在此可视角度下恰好显示整幅图像
    z = np.sqrt(ih ** 2 + iw ** 2) / 2 / np.tan(rad(fov / 2))
    
    # X轴旋转矩阵
    rx = np.array([[1, 0, 0, 0],
                   [0, np.cos(rad(anglex)), np.sin(rad(anglex)), 0],
                   [0, -np.sin(rad(anglex)), np.cos(rad(anglex)), 0],
                   [0, 0, 0, 1]], np.float32)

    # Y轴旋转矩阵
    ry = np.array([[np.cos(rad(angley)), 0, -np.sin(rad(angley)), 0],
                   [0, 1, 0, 0],
                   [np.sin(rad(angley)), 0, np.cos(rad(angley)), 0],
                   [0, 0, 0, 1]], np.float32)

    # Z轴旋转矩阵
    rz = np.array([[np.cos(rad(anglez)), np.sin(rad(anglez)), 0, 0],
                   [-np.sin(rad(anglez)), np.cos(rad(anglez)), 0, 0],
                   [0, 0, 1, 0],
                   [0, 0, 0, 1]], np.float32)

    # 综合旋转矩阵
    r = rx.dot(ry).dot(rz)

    # 图像中心点
    pcenter = np.array([iw / 2, ih / 2, 0, 0], np.float32)

    # 图像四个角点相对于中心点的坐标
    p1 = np.array([0, 0, 0, 0], np.float32) - pcenter
    p2 = np.array([ih, 0, 0, 0], np.float32) - pcenter
    p3 = np.array([0, iw, 0, 0], np.float32) - pcenter
    p4 = np.array([ih, iw, 0, 0], np.float32) - pcenter
    
    # 对角点进行旋转变换
    dst1 = r.dot(p1)
    dst2 = r.dot(p2)
    dst3 = r.dot(p3)
    dst4 = r.dot(p4)

    # 旋转后的角点坐标列表
    list_dst = [dst1, dst2, dst3, dst4]

    # 原始图像的四个角点坐标
    org = np.array([[0, 0],
                    [ih, 0],
                    [0, iw],
                    [ih, iw]], np.float32)

    # 变换后的角点坐标
    dst = np.zeros((4, 2), np.float32)

    # 投影至成像平面
    for i in range(4):
        dst[i, 0] = list_dst[i][0] * z / (z - list_dst[i][2]) + pcenter[0]
        dst[i, 1] = list_dst[i][1] * z / (z - list_dst[i][2]) + pcenter[1]

    # 计算透视变换矩阵
    warpR = cv2.getPerspectiveTransform(org, dst)
    # 应用透视变换
    result = cv2.warpPerspective(img, warpR, (iw, ih))
    return result

# 移除图像中的黑边
def remove_black(img):
    height, width, _ = img.shape  # 获取图像的高、宽和通道数
    angle = random.choice([36, 38, 40, 42, 44])  # 随机选择一个角度
    img_new = change_img_angle(img, 0, -1*angle, 0)  # 改变图像角度
    img_gray = cv2.cvtColor(img_new, cv2.COLOR_RGB2GRAY)  # 转换为灰度图像
    for j in range(int(width/2.0), width):
        pix_num = img_gray[int(height/2),j]  # 获取图像中间行的像素值
        if pix_num == 0:  # 找到黑边的边界
            break
    return img_new[:, 0:j]  # 裁剪图像，去除黑边

# 主函数
if __name__ == "__main__":
    img_path = "/home/gp/work/project/end-to-end-for-chinese-plate-recognition/plate/04.jpg"
    img = cv2.imread(img_path)  # 读取图像
    img_new = remove_black(img)  # 移除黑边
    cv2.imwrite("haha.jpg", img_new)  # 保存处理后的图像
