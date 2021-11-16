# 偶に上下バナーの単色表示で上のバナーが出ず下の表示だけしかないバグ ← 原因不明 set_event()でmainloop()を先に起動することを保証したが解決できない
# ボタンdestroy時の穴あきは直す window作り直す ← 現状閉じるボタンと画像が重ならないように配置しているので修正していません
# 無視時の処理方法変える

import time
import datetime
import random
from selenium import webdriver
from PIL import ImageGrab, Image, ImageTk
from threading import (Event, Thread)
import tkinter
import sys
import csv
import glob
import cv2
import os.path
from pynput import mouse, keyboard
import pyautogui
import exutil

# 以下グローバル定数・変数定義 グローバルの必要ないものもあるかも

# 保存するフォルダのパスの定数作成
RESULT_DIR = "result\\"
NAME_PATH = "result\\nowUser.txt"
if os.path.exists(NAME_PATH) == False:
	print(NAME_PATH + "にファイルがありません")
	sys.exit(1)

with open(NAME_PATH, 'r') as f:
	SAVE_DIR = RESULT_DIR + f.read()

# chromedriverのパス
CHROMEDRIVER_PATH = "chromedriver_win32\chromedriver"

# 広告関連の定数
TIME_FIRSTWAITING = 6
TIME_EXPERIMENT = 60 * 14
TIME_RESET = 15
NUM_LOOP = 3

# ループ速度
FPS = 60.0

# 画像のパス
SIKAKU_DIR = "image\\small_image\\sikaku\\"
YOKO_DIR = "image\\small_image\\yokonaga\\"
CLOSE_DIR = "image\\small_image\\close\\"
SIMPLE_SIKAKU_DIR = "image\\simple\\sikaku\\"
SIMPLE_YOKO_DIR = "image\\simple\\yokonaga\\"
WHITE_TRANS_PATH = "image\\white_trans_image\\white_w_trans.png"

# キャンバス関連の定数
SIZE_WINDOW = "1910x1070"
SIZE_YOKO = "700x150"
SIZE_SIKAKU = "300x280"
SIZE_ZENMEN = "300x350"
POS_JOUGE_TOP_QUIZ = "610+150" # 1920x1080
POS_JOUGE_BUTTOM_QUIZ = "810+650"
POS_JOUGE_TOP_RESULT = "610+150"
POS_JOUGE_BUTTOM_RESULT = "810+650"
POS_ZENMEN = "810+365"

# 無視広告時の最大クリック数
IGNORE_MAX = 6

# 広告無視の確率の変更に用いる変数
ignore_rate = 1

# 表示している画像が存在するディレクトリ
now_dir = ""
now_dir = ""

# 広告種類が何通りあるかのリスト
ad_kinds = [0,1,2,3,4,5,6]

# 画像のパスを格納するリスト
im_sikaku_list = []
im_yoko_list = []
im_simple_sikaku_list = []
im_simple_yoko_list = []

# 画像のパスを格納する変数
cur_im_sikaku_path = ""
cur_im_yoko_path = ""
next_im_sikaku_path = ""
next_im_yoko_path = ""

# ログやリセット区間測定のために用いる変数
time_close = None

# 広告の表示/非表示に用いるフラグ
flag_click = False
is_disp = False
disp_ready = False

# 画面遷移の判定に用いるフラグ
flag_trans = False
flag_finish = False
is_result = False # 正解表示画面か
is_correct = False # 正解画面か

# auto_clickに用いるフラグ
flag_auto_click = False

# どちらかがTrueで起動しない
flag_pose = True
flag_cap = True

# 実験開始時間を記録する変数
start = None

# キャンバスの初期設置を先に終わらせるために用いる
event = Event()

# キャンバス関連の変数
root, root = (None, None)
canvas, canvas2 = (None, None)
item, item2 = (None, None) # item = create_image()でitemのidを取得する必要あり,itemもグローバル変数にする
img, img2 = (None, None) # PhotoImageでの参照先が消えないようにグローバル変数にする必要がある

# ディレクトリの存在確認+ログファイルを作る関数
def preparation_files():
	global RESULT_DIR, SAVE_DIR

	if os.path.isdir(SAVE_DIR) == False:
		print(SAVE_DIR + "フォルダが見つかりません")
		sys.exit(1)

	exutil.checkfile(SAVE_DIR+'\\advertising.csv')
	with open(SAVE_DIR+'\\advertising.csv','a',newline='') as f: # 広告ログ
		writer = csv.writer(f)
		writer.writerow(['time','nasi','jouge+','jouge','zenmen+','zenmen','musi+','musi','image','image2(banner)',\
		'correct','incorrect'])

	exutil.checkfile(SAVE_DIR+'\\advertising_close.csv')
	with open(SAVE_DIR+'\\advertising_close.csv','a',newline='') as f: # 閉じるオンリーログ
		writer = csv.writer(f)
		writer.writerow(['time','is_closed'])

# 画像のpathを四角画像と横長画像にわけてlistに格納
def get_image(image_dir):
   image_path = image_dir+'*'
   image_path_list = glob.glob(image_path)
   return image_path_list

# 経過時間取得関数
def get_elapsed_time():
	global start
	return time.perf_counter() - start

# 同期するため,mainloop()から0.5秒後に呼ばれる関数
def set_event(id):
	global event
	if id == 1:
		event.set()

# 初期設定関数1 canvas関連まとめてクラス検討
def set_canvas():

	global root, canvas, item, im_sikaku_list, img, \
	root2, canvas2, item2, im_sikaku_list, img2

	root = tkinter.Tk()
	root.geometry("800x450+250+250")	# 作成するwindowサイズ+x+y
	root.overrideredirect(1) # ウィンドウ上部のバー(閉じる・最小化ボタンなど)を削除
	root.attributes("-topmost", True) # 常に最前面に配置する

	img = ImageTk.PhotoImage(file=im_sikaku_list[0], master=root) # とりあえず適当な画像

	#キャンバスエリア
	canvas = tkinter.Canvas(root,width=1920,height=1080,bg="white") # 一番大きな広告のサイズに合わせる 大きいほうが良い

	item = canvas.create_image(0, 0, image=img, anchor=tkinter.NW) # canvas.create_imageは１つのキャンバスにつき１回呼び出すだけで良い?

	#キャンバスバインド
	canvas.place(x=0, y=0)#Canvasの配置(windowサイズからの座標)

	### RoundedButton(parent, width, height, cornerradius, padding, fillcolor, background, command)
	# 必要かどうか
	root.loadimage = tkinter.PhotoImage(file=CLOSE_DIR+"small_tojiru_button.png", master=root) # ボタンにする画像を読み込み
	root.roundedbutton = tkinter.Button(root, image=root.loadimage, command=btn_click)
	root.roundedbutton["bg"] = "white" # 背景がTkinterウィンドウと同じに
	root.roundedbutton["border"] = "0" # ボタンの境界線が削除
	root.roundedbutton.place(x=75,y=280)
	
	# 以下toplevel()でのサブウィンドウ表示
	root2 = tkinter.Toplevel()
	root2.geometry("800x450+500+500")
	root2.overrideredirect(1)
	root2.attributes("-topmost", True)

	img2 = ImageTk.PhotoImage(file=im_sikaku_list[0], master=root2)

	#キャンバスエリア
	canvas2 = tkinter.Canvas(root2,width=1920,height=1080,bg="white")

	item2 = canvas2.create_image(0, 0, image=img2, anchor=tkinter.NW)

	#キャンバスバインド
	canvas2.place(x=0, y=0)

	root2.loadimage = tkinter.PhotoImage(file=CLOSE_DIR+"small_tojiru_button.png", master=root2)
	root2.roundedbutton = tkinter.Button(root2, image=root2.loadimage, command=btn_click)
	root2.roundedbutton["bg"] = "white"
	root2.roundedbutton["border"] = "0"
	root2.roundedbutton.place(x=75,y=280)

	root2.withdraw() # 非表示ではじめる
	root.withdraw()

	root.after(500, set_event, 1)

	root.mainloop()

# 初期設置関数2 Toplevel()に気が付かず2つめのメインウィンドウ作成しています 時間があれば修正
def set_canvas2():

	global root2, canvas2, item2, im_sikaku_list, img2

	

# 前面系で閉じるを押したときのログ(閉じるボタンコマンドから呼び出し)
def close_log(time):
	with open(SAVE_DIR+'\\advertising_close.csv','a',newline='') as f:
		writer = csv.writer(f)
		writer.writerow([time,1])

# 閉じるボタンコマンド
def btn_click():
	global root, flag_click, time_close, is_disp, root2
	print("flag_click")
	time_close = get_elapsed_time()
	root.withdraw()
	root2.withdraw()
	is_disp = False
	flag_click = True
	close_log(time_close)

# 閉じるボタンコマンド(6割クリック無視)
def ignore_btn_click():
	global root, flag_click, time_close, is_disp, ignore_rate, IGNORE_MAX, root2
	print("flag_click")
	if random.random() < ignore_rate:
		ignore_rate = ignore_rate - 1/IGNORE_MAX
		return
	ignore_rate = 1
	time_close = get_elapsed_time()
	root.withdraw()
	root2.withdraw()
	is_disp = False
	flag_click = True
	close_log(time_close)

# on_release関数に呼び出される関数
def autoClick():
	global flag_auto_click
	#pyautogui.click(800,800) # 既にウェブサイト上で名前入力+enterを押して開始が実装済み
	flag_auto_click = True

# キーボードリスナーのon_release時に呼び出される関数
def on_release(key):
	if key == keyboard.Key.enter:
		#print('pressed Enter key')
		autoClick()
		return False

# ログ出力関数
def ad_log(time, ad_kind, is_result, is_correct, is_disp, content, content2=""):
	global now_dir, now_dir2
	
	ad_kinds = [0,0,0,0,0,0,0] # 無し,上下刺激,上下一般,前面刺激,前面一般,無視刺激,無視一般
	contents = ["",""]
	rw = [0,0] # right or wrong
	
	if is_disp == True:
		ad_kinds[ad_kind] = 1
		if ad_kind != 0:
			contents[0] = content.replace(now_dir, "")
			contents[1] = content2.replace(now_dir2, "")
			if not(ad_kind == 1 or ad_kind == 2):
				contents[1] = ""
	
	if is_result == True: # 正解表示画面
		if is_correct == True:
			rw[0] = 1
		else:
			rw[1] = 1
	
	with open(SAVE_DIR + '\\advertising.csv', 'a', newline='') as f:
		writer = csv.writer(f)
		# 時間,広告種類(7つ分),内容(最大2つ),正解画面か不正解画面か(2つ)
		writer.writerow([time,ad_kinds[0],ad_kinds[1],ad_kinds[2],ad_kinds[3],ad_kinds[4],ad_kinds[5],ad_kinds[6],contents[0],contents[1],rw[0],rw[1]])

# 画像を選択しパスをnext_im_sikaku_pathとnext_im_yoko_pathに格納する関数
def select_ad_image(ad_kind):
	global im_yoko_list, im_sikaku_list, im_simple_yoko_list, im_simple_sikaku_list, next_im_yoko_list, next_im_sikaku_list, \
	next_im_yoko_path, next_im_sikaku_path, now_dir, now_dir2, SIKAKU_DIR, YOKO_DIR, SIMPLE_SIKAKU_DIR, SIMPLE_YOKO_DIR
	
	if ad_kind == 0:
		(next_im_yoko_list, next_im_sikaku_list) = ("", "")
		return

	if ad_kind % 2 == 0: # 一般画像
		next_im_yoko_path = random.choice(im_yoko_list)
		next_im_sikaku_path = random.choice(im_sikaku_list)
		now_dir = SIKAKU_DIR
		now_dir2 = YOKO_DIR
	else: # 刺激画像
		next_im_yoko_path = random.choice(im_simple_yoko_list)
		next_im_sikaku_path = random.choice(im_simple_sikaku_list)
		now_dir = SIMPLE_SIKAKU_DIR
		now_dir2 = SIMPLE_YOKO_DIR

# リセット区間中に呼び出される,広告表示の準備をする関数
def set_display_ad(ad_kind):
	global root, root2, canvas, canvas2, item, item2, CLOSE_DIR, POS_ZENMEN, \
	POS_JOUGE_TOP_QUIZ, POS_JOUGE_BUTTOM_QUIZ, POS_JOUGE_TOP_RESULT, POS_JOUGE_BUTTOM_RESULT, \
	SIZE_YOKO, SIZE_SIKAKU, is_disp, img, img2, SIZE_ZENMEN, WHITE_TRANS_PATH, SIZE_WINDOW, \
	next_im_sikaku_path, next_im_yoko_path, disp_ready
	
	select_ad_image(ad_kind) # 次の画像の準備
	
	if ad_kind == 0:
		return
	
	print("next_im_sikaku_path is" + str(next_im_sikaku_path))
	print("next_im_sikaku_path is" + str(next_im_yoko_path))
	
	canvas.delete(item) ## 追加
	canvas2.delete(item2)
	
	# 表示場所やボタンの設定
	pos, pos2 = (None, None)
	geo = None
	if ad_kind == 1 or ad_kind == 2: # 上下
		root.roundedbutton.destroy() # pack(), pack_forget()に置き換えられるかも コマンドの書き換えだけできれば
		root2.roundedbutton.destroy()
		if is_result == True:
			pos = POS_JOUGE_BUTTOM_RESULT
			pos2 = POS_JOUGE_TOP_RESULT
		else:
			pos = POS_JOUGE_BUTTOM_QUIZ
			pos2 = POS_JOUGE_TOP_QUIZ
		geo = SIZE_SIKAKU + "+" + pos
		geo2 = SIZE_YOKO + "+" + pos2
		img2 = ImageTk.PhotoImage(file=next_im_yoko_path, master=root2)
		root2.attributes('-alpha', 1.0) # 透明度を戻す
		root2.attributes("-topmost", True)
	else:
		if ad_kind == 3 or ad_kind == 4:
			com = btn_click
		else:
			com = ignore_btn_click
		
		root2.roundedbutton.destroy()
		
		root.loadimage = tkinter.PhotoImage(file=CLOSE_DIR+"small_tojiru_button.png", master=root)
		root.roundedbutton = tkinter.Button(root, image=root.loadimage, command=com)
		root.roundedbutton["bg"] = "white"
		root.roundedbutton["border"] = "0"
		root.roundedbutton.place(x=75,y=280)
		pos = POS_ZENMEN
		pos2 = "0+0"
		geo = SIZE_ZENMEN + "+" + pos
		geo2 = SIZE_WINDOW + "+" + pos2
		img2 = ImageTk.PhotoImage(file=WHITE_TRANS_PATH, master=root2)
		root2.attributes('-alpha', 0.2) # 透明
		root2.attributes("-topmost", False) # 最前面だと閉じる押せなくなるから
	
	root.geometry(geo)
	root2.geometry(geo2)
	img = ImageTk.PhotoImage(file=next_im_sikaku_path, master=root)
	
	#canvas.itemconfig(item, image=img)
	#canvas2.itemconfig(item2, image=img2)
	item = canvas.create_image(0, 0, image=img, anchor=tkinter.NW)
	item2 = canvas2.create_image(0, 0, image=img2, anchor=tkinter.NW)
	
	canvas.place()
	canvas2.place()
	
	disp_ready = True

# 広告表示関数(is_dispをオンにできる関数)
def display_ad(ad_kinds, setcount):
	global root, root2, is_disp, cur_im_sikaku_path, cur_im_yoko_path, next_im_sikaku_path, next_im_yoko_path
	
	cur_im_sikaku_path = next_im_sikaku_path
	cur_im_yoko_path = next_im_yoko_path
	
	if ad_kinds[setcount] != 0: # 刺激区間中の無刺激区間でなければ
		root2.deiconify()
		root.deiconify()
	
	is_disp = True

# 広告非表示 + それに伴う処理をまとめた関数
def hide_ad():
	global is_disp, time_close, root, root2, disp_ready

	root.withdraw()
	root2.withdraw()

	time_close = get_elapsed_time()

	is_disp = False
	disp_ready = False

# urlによって状態変数などを変更する関数
def check_url(driver):
	global is_result, flag_trans, is_correct, flag_finish
	
	cur_url = driver.current_url
	if r"http://3.134.34.102/question?result=" in cur_url: # 正否表示画面 # http://3.134.34.102/question?result=true&questionid=86
		if is_result == False:
			flag_trans = True
		else:
			flag_trans = False
		if "true" in cur_url: # 正解画面
			is_correct = True
		else:
			is_correct = False
		is_result = True
	elif r"http://3.134.34.102/question" in cur_url: # 出題画面 # http://3.134.34.102/question
		if is_result == True:
			flag_trans = True
		else:
			flag_trans = False
		is_result = False
	elif r"http://3.134.34.102/result" == cur_url: # 終了画面 一応
		flag_finish = True

def main_sub():

	global start, CHROMEDRIVER_PATH, ad_kinds, TIME_ONESET, TIME_FIRSTWAITING, TIME_LASTWAITING, NUM_LOOP, \
	flag_trans, flag_finish, is_result, event, root, root2, canvas, canvas2, item, item2, \
	flag_click, is_disp, time_close, FPS, cur_im_sikaku_path, cur_im_yoko_path, disp_ready
	
	im_yoko_path, im_sikaku_path = (None, None) # 宣言だけでも local

	while flag_pose == False or flag_cap == False:
		pass

	# 別スレッドのset_canvasが終わるまで待つ
	event.wait()

	options = webdriver.ChromeOptions()
	options.add_experimental_option("excludeSwitches", ['enable-automation'])
	driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=options)
	driver.maximize_window()
	driver.get("http://3.134.34.102/")


	# enterキー押すまで待機
	keyboard_listener = keyboard.Listener(on_release=on_release)
	keyboard_listener.start()
	while flag_auto_click == False:
		pass

	# クイズスタート時のタイムスタンプ & 記録
	start = time.perf_counter()
	start_quiz_date = time.time() # 上の行との間に小さなズレがあるかも
	with open(SAVE_DIR+'\\startTime.csv','a',newline='') as f: # プログラム開始終了タイムスタンプ
		writer = csv.writer(f)
		writer.writerow(['randomAd',start_quiz_date])

	print("wait " + str(TIME_FIRSTWAITING) + " second") # デバッグ用
	time_before = 0 - FPS # ループがいきなり始まってほしいので
	while get_elapsed_time() < TIME_FIRSTWAITING: # 最初待機 + 一応ログ
		elapsed = get_elapsed_time()
		if elapsed - time_before < 1.0 / FPS: # 前のループからそこまで時間が経っていない場合 中の処理重い場合かなりズレが出てくる
			continue
		
		time_before = elapsed
		
		check_url(driver)
			
		if elapsed >= TIME_FIRSTWAITING:
			break
		
		ad_log(elapsed, 0, is_result, is_correct, False, "", "")

	time_close = 0 - TIME_RESET # 練習後に15秒リセット後と同じ動作をさせるため
	print("for-while loop start") # デバッグ用
	for i in range(NUM_LOOP):
		random.shuffle(ad_kinds)
		setcount = 0 # 範囲は0~6
		ad_kinds = [4,2,6,1,3,5,0] # デバッグ用
		while setcount <= len(ad_kinds) - 1:
			elapsed = get_elapsed_time()
			if elapsed - time_before < 1.0 / FPS: # 前のループからそこまで時間が経っていない場合
				continue
			
			time_before = elapsed
			
			check_url(driver)

			# 終了画面になった時
			if flag_finish == True:
				break;
			
			# 次の表示の準備
			if is_disp == False and disp_ready == False and flag_click == False: # setcountは増加した後の値になる
				set_display_ad(ad_kinds[setcount])
			
			# ループ最後は次への準備が不可能
			
			# 前まではここでclickされた場合の処理

			if elapsed - int(elapsed) <= 0.01: # デバッグ用
				print(elapsed)
				print(setcount)
				print(ad_kinds[setcount])
			
			# 前面系で閉じるボタンが押された時の処理
			if flag_click == True:
				setcount = setcount + 1
				disp_ready = False
				flag_click = False

			if elapsed - time_close >= TIME_RESET: # 刺激区間
				if flag_trans == True: # 画面遷移した場合
					if is_result == False: # 出題画面の場合
						# 広告表示
						display_ad(ad_kinds, setcount)

					else: # 正解表示画面
						if is_disp == True: # 既に広告表示されている場合
							hide_ad()
							time_close = elapsed
							setcount = setcount + 1

				else: # 画面遷移しない場合
					# 処理
					pass
				
				

			else: # 無刺激区間(リセット区間)
				# 処理
				pass
			
			# 以下while抜ける前の処理
			if setcount >= len(ad_kinds): # 応急処置的
				suf = len(ad_kinds)-1
			else:
				suf = setcount
			ad_log(elapsed, ad_kinds[suf], is_result, is_correct, is_disp, cur_im_sikaku_path, cur_im_yoko_path)
		
		
		if flag_finish == True: # リザルト画面
			break;

	# 以下最後の待機無刺激区間

	if is_disp == True:
		hide_ad()

	if flag_finish != True: # 上のfor-whileループが自然に終了した時
		print("wait " + str( get_elapsed_time() - TIME_EXPERIMENT )) # デバッグ用
		while get_elapsed_time() < TIME_EXPERIMENT: # 実験終了まで待機処理
			elapsed = get_elapsed_time()
			if elapsed - time_before < 1.0 / FPS:
				continue
				
			time_before = elapsed
			check_url(driver)
			if flag_finish == True:
				break

	print("finish") # 確認用

	while True:
		pass

# main

if __name__ == '__main__': # コマンドラインから実行された場合

	im_sikaku_list = get_image(SIKAKU_DIR)
	im_yoko_list = get_image(YOKO_DIR)
	im_simple_sikaku_list = get_image(SIMPLE_SIKAKU_DIR)
	im_simple_yoko_list = get_image(SIMPLE_YOKO_DIR)
	print(im_simple_sikaku_list)
	print(im_simple_yoko_list)

	try:
		preparation_files()

		advertisingDisplayThread = Thread(target=set_canvas)
		advertisingDisplayThread.setDaemon(True)
		advertisingDisplayThread.start()

		main_sub()

	# Ctrl+C で終了
	except KeyboardInterrupt:
		print ('Ctrl+C pressed...')
		sys.exit(0)
