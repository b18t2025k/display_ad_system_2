# -*- coding: utf-8 -*-
import os
import sys
import csv

#引数の確認
def argCheck(arg):
    if len(arg) == 1:
        print("実行時の引数が異常です")
        sys.exit(1)
        
#ディレクトリが無ければ作成する
def ifmkdir(dir):
    if False == os.path.isdir(dir):
        os.mkdir(dir)


def checkdir(dir):
   if os.path.isdir(SAVE_DIR):
     print("すでに同名のユーザが試験済みなので、ユーザ名を変更するかディレクトリの待避を実施してください")
     sys.exit(1)

def checkfile(file):
   if os.path.isfile(file):
     print("すでに"+file+"ファイルが存在します。")
     sys.exit(1)

## 引数の確認と保存先の名称確認
# RESULT_DIR = 'result\\'        
# argCheck(sys.argv)
# SAVE_DIR = RESULT_DIR + sys.argv[1]
# CAMERA_DIR = SAVE_DIR+"\\cameraCapture"
# SCREENSHOT_DIR = SAVE_DIR+"\\screenShot"
## 引数の確認と保存先の名称確認 終了
