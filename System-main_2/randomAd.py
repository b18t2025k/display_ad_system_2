# 偶に上下バナーの単色表示で上のバナーが出ず下の表示だけしかないバグ ← Toplevel使うと治ったかも 前まではtkinter.Tk()を2つ作りスレッド2つで回していた
# 前面時に透過ウィンドウを用いたいが、純透明だとクリックも透けてしまう問題 ← 少しだけ透明にした
# 画像表示前に前の画像が一瞬うつりこむ問題 ← canvas.delete() → 白画像差し替え でましになった? geometry()とalpha値はそのままのほうが良さげ
# 最前面2つで順序付けたい問題 ← -topmostとlift()の順番で制御できるかも
# ボタンdestroy()で画像が欠ける問題あり(画像と被らないように配置することで回避)

import time
import datetime
import random
from selenium import webdriver
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver
from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
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
from pynput import mouse
import exutil

# 以下グローバル定数・変数定義 グローバルの必要ないものもあるかも

# 保存するフォルダのパスの定数作成
RESULT_DIR = "experiment\\result\\"
NAME_PATH = RESULT_DIR + "nowUser.txt"
if os.path.exists(NAME_PATH) == False:
	print(NAME_PATH + "にファイルがありません")
	sys.exit(1)

with open(NAME_PATH, 'r') as f:
	SAVE_DIR = RESULT_DIR + f.read()

# chromedriverのパス
CHROMEDRIVER_PATH = "chromedriver_win32\chromedriver"

# 広告関連の定数
TIME_FIRSTWAITING = 6
TIME_EXPERIMENT = 60 * 14 + 15
TIME_RESET = 5
NUM_LOOP = 3

# ループ速度
FPS = 60.0

# 画像のパス
SIKAKU_DIR = "image\\small_image\\sikaku\\"
YOKO_DIR = "image\\small_image\\yokonaga\\"
CLOSE_DIR = "image\\small_image\\close\\"
SIMPLE_SIKAKU_DIR = "image\\simple\\sikaku\\"
SIMPLE_YOKO_DIR = "image\\simple\\yokonaga\\"
WHITE_TRANS_PATH = "image\\white_trans_image\\trans.png"

# キャンバス関連の定数(後に設定 or 直接書いて下の関数消してもいい)
SIZE_WINDOW = ""
SIZE_YOKO = "700x150" # 使わないけれど書かないとエラーなものは値直接入れています
SIZE_SIKAKU = ""
SIZE_ZENMEN = ""
POS_JOUGE_TOP_QUIZ = "100+100"
POS_JOUGE_BUTTOM_QUIZ = ""
POS_JOUGE_TOP_RESULT = "100+100"
POS_JOUGE_BUTTOM_RESULT = ""
POS_ZENMEN = ""
PADDING = ""
SIZE_BUTOON_TOJIRU = ""
POS_BUTTON_TOJIRU = ""

# 上の空の定数に値を入れる処理(pos～の引数に0を入れると中央)
def create_hensuu(window_size_x, window_size_y, image_size_x, image_size_y, padding, pos_sita_x, pos_sita_y, pos_zenmen_x, pos_zenmen_y, button_size_x, button_size_y,\
):
	global SIZE_WINDOW, SIZE_SIKAKU, SIZE_ZENMEN, POS_JOUGE_BUTTOM_QUIZ, POS_JOUGE_BUTTOM_RESULT, POS_ZENMEN, PADDING, SIZE_BUTOON_TOJIRU, POS_BUTTON_TOJIRU
	SIZE_SIKAKU = str( int(image_size_x + padding*2) ) + "x" + str( int(image_size_y + padding*2) )
	SIZE_ZENMEN = str( int(image_size_x + padding*2) ) + "x" + str( int(image_size_y + padding + button_size_y + padding*3) )
	POS_JOUGE_BUTTOM_QUIZ = str( int( (window_size_x - image_size_x)/2 + pos_sita_x) ) + "+" + str( window_size_y - image_size_y + pos_sita_y)
	POS_JOUGE_BUTTOM_RESULT = str( int((window_size_x - image_size_x)/2 + pos_sita_x)) + "+" + str( window_size_y - image_size_y + pos_sita_y)
	POS_ZENMEN = str( int((window_size_x - image_size_x)/2 + pos_zenmen_x)) + "+" + str( int((window_size_y - image_size_y)/2 + pos_zenmen_y ) )
	PADDING = padding
	SIZE_BUTTON_TOJIRU = str(button_size_x) + "x" + str(button_size_y)
	POS_BUTTON_TOJIRU = str(int( (image_size_x + padding*2 - button_size_x) / 2 )) + "+" + str( padding+image_size_y+int(padding) )
	SIZE_WINDOW = str(window_size_x) + "x" + str(window_size_y)

create_hensuu(1920, 1080, 500, 400, 10, 0, -130, 0, -70, 198, 59)

# 無視広告時の最大クリック数
IGNORE_MAX = 6

# 広告無視回数の変更に用いる変数
ignore_num = 1

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

"""
# クリックログを書き込む際1つ前の状態を保存する仕様のため
state_click_log_before = [0,0,0]
"""

# 広告の表示/非表示に用いるフラグ
flag_close = False
is_disp = False
disp_ready = False

"""
# クリック取得のため必要なフラグ
flag_click = False
"""

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
items_wakusen = [None,None,None,None,None,None,None,None] # 枠線消す用
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
		writer.writerow(['time','nasi','sita/n','sita/p','zenmen/n','zenmen/p','musi/n','musi/p','image',\
		'correct','incorrect']) # 上下の場合は'image'の次の列に'image2(banner)'を追加

	exutil.checkfile(SAVE_DIR+'\\advertising_close.csv')
	with open(SAVE_DIR+'\\advertising_close.csv','a',newline='') as f: # 閉じるオンリーログ
		writer = csv.writer(f)
		writer.writerow(['time','is_closed'])
	
	"""
	exutil.checkfile(SAVE_DIR+'\\site_click.csv')
	with open(SAVE_DIR+'\\site_click.csv','a',newline='') as f:
		writer = csv.writer(f)
		writer.writerow(['time','next','left','right','miss'])
	"""

# 画像のpathを四角画像と横長画像にわけてlistに格納
def get_image(image_dir):
   image_path = image_dir+'*'
   image_path_list = glob.glob(image_path)
   return image_path_list

# 経過時間取得関数
def get_elapsed_time():
	global start
	return time.perf_counter() - start

"""
# リスナー デバッグ用
def on_move(x, y):
    print('Pointer moved to {0}'.format(
        (x, y)))
"""

"""
# クリックリスナー用関数 押し込み解除時にフラグ立てる
def on_click(x, y, button, pressed):
	global flag_click
	
	if not pressed: # 離した後
		flag_click = True
	
	#print('{0} at {1}'.format('Pressed' if pressed else 'Released', (x, y)))
"""

"""
# リスナー デバッグ用
def on_scroll(x, y, dx, dy):
    print('Scrolled {0} at {1}'.format(
        'down' if dy < 0 else 'up',
        (x, y)))
"""

"""
# 使わなくなったリスナー
class MyListener(AbstractEventListener):
	def before_click(self, element, driver):
		time = get_elapsed_time()
		print(element.get_attribute("class"))
		if element.get_attribute("class") == "btn btn-primary" and element.get_attribute("type") != "submit":
			flags = [0,0,0,0]
			id = elemetn.get_attribute("id")
			if id == "button1":
				flags[0] = 1
			elif id == "button2":
				flags[1] = 1
			else:
				flags[2] = 1
			
			with open(SAVE_DIR+'\\site_click.csv','a',newline='') as f:
				writer = csv.writer(f)
				writer.writerow(time,flags[0],flags[1],flags[2],flags[3])
	
	def after_click(self, element, driver):
		pass
"""

# 同期するため,mainloop()から0.5秒後に呼ばれる関数
def set_event(id):
	global event
	if id == 1:
		event.set()

# 初期設定関数1 canvas関連まとめてクラス検討
def set_canvas():

	global root, canvas, item, im_sikaku_list, img, \
	root2, canvas2, item2, im_sikaku_list, img2, \
	POS_BUTTON_TOJIRU

	root = tkinter.Tk()
	root.title("root")
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
	root.loadimage = tkinter.PhotoImage(file=CLOSE_DIR+"small_tojiru_button.png", master=root) # ボタンにする画像を読み込み
	root.roundedbutton = tkinter.Button(root, image=root.loadimage, command=btn_click)
	root.roundedbutton["bg"] = "white" # 背景がTkinterウィンドウと同じに
	root.roundedbutton["border"] = "0" # ボタンの境界線が削除
	root.roundedbutton.place(x=int(POS_BUTTON_TOJIRU[0:3])+2,y=int(POS_BUTTON_TOJIRU[4:7])+2)
	
	# 以下toplevel()でのサブウィンドウ表示
	root2 = tkinter.Toplevel()
	root2.title("root2")
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
	root2.roundedbutton.place(x=(360-198)/2,y=240+80)

	root2.withdraw() # 非表示ではじめる
	root.withdraw()

	root.after(500, set_event, 1)

	root.mainloop()

# 一瞬だけ今の画像を透過白画像に変更する関数 ! 考えどころ 大きさも帰る?
def display_white_moment():
	global root, canvas, img, item, root2, canvas2, img2, item2, WHITE_TRANS_PATH
	
	#root.attributes('-alpha', 0.02) # 透明と半透明のギリギリ
	#root2.attributes('-alpha', 0.02)

	canvas.delete(item)
	canvas2.delete(item2)
	
	img = ImageTk.PhotoImage(file=WHITE_TRANS_PATH, master=root)
	img2 = ImageTk.PhotoImage(file=WHITE_TRANS_PATH, master=root2)
	
	item = canvas.create_image(0, 0, image=img, anchor=tkinter.NW)
	item2 = canvas2.create_image(0, 0, image=img2, anchor=tkinter.NW)
	#canvas.itemconfig(item, image=img)
	#canvas2.itemconfig(item2, image=img2)

	#root.geometry("1910x1070+0+0")
	#root2.geometry("1910x1070+0+0")

	#root.attributes('-alpha', 0.02) # 透明と半透明のギリギリ
	#root2.attributes('-alpha', 0.02)

"""
# クリックログ, クリックした瞬間のログを書き込むのではなく1つ前の状態のログを書き込む(clickのほうがcloseよりも早いから)
def click_log(time):
	global flag_click, flag_close, state_click_log_before

	if flag_click == False: # クリックされていないならcloseを1つ前のclickと結びつける処理してリターン
		if flag_close == True: # closeだけたっているときは1つ前のクリックログのクリックによってcloseされている
			state_click_log_before[1] = 1 # closeフラグを立てる
		return
	
	# 1つ前の状態を保存
	with open(SAVE_DIR+'\\advertising_close.csv','a',newline='') as f:
			writer = csv.writer(f)
			writer.writerow(state_click_log_before)
	
	# 現在の状態に更新
	state_click_log_before = [0, 0, 0]
	state_click_log_before[0] = time
	if flag_close == True:
		print("close") # デバッグ用
		state_click_log_before[1] = 1
	if flag_click == True:
		print("click") # デバッグ用
		state_click_log_before[2] = 1
	
	flag_click = False
"""

# 前面系で閉じるを押したときのログ(閉じるボタンコマンドから呼び出し)
def close_log(time):
	with open(SAVE_DIR+'\\advertising_close.csv','a',newline='') as f:
		writer = csv.writer(f)
		writer.writerow([time,1])

# 閉じるボタンコマンド
def btn_click():
	global root, flag_close, time_close, is_disp, root2
	print("flag_close")
	display_white_moment()
	root.withdraw()
	root2.withdraw()
	time_close = get_elapsed_time()
	is_disp = False
	flag_close = True
	close_log(time_close)

# 閉じるボタンコマンド(6割クリック無視)
def ignore_btn_click():
	global root, flag_close, time_close, is_disp, ignore_num, IGNORE_MAX, root2
	print("flag_close") # デバッグ用
	if 1 < ignore_num:
		ignore_num = ignore_num - 1
		return
	
	display_white_moment()
	root.withdraw()
	root2.withdraw()
	time_close = get_elapsed_time()
	is_disp = False
	flag_close = True
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
def ad_log(time, ad_kind, is_result, is_correct, is_disp_local, content, content2=""):
	global now_dir, now_dir2
	
	ad_kinds = [0,0,0,0,0,0,0] # 無し,上下刺激,上下一般,前面刺激,前面一般,無視刺激,無視一般
	contents = ["",""]
	rw = [0,0] # right or wrong
	
	if is_disp_local == True:
		ad_kinds[ad_kind] = 1
		if ad_kind != 0:
			contents[0] = content.replace(now_dir, "")
			contents[1] = content2.replace(now_dir2, "")
			if ad_kind == 1 or ad_kind == 2: # ログ出力時に上下の2つ目が出なくなるように仕様変更したのでログにも出ないように修正
				contents[1] = ""
			if not(ad_kind == 1 or ad_kind == 2):
				contents[1] = ""
	
	if is_result == True: # 正解表示画面
		if is_correct == True:
			rw[0] = 1
		else:
			rw[1] = 1
	
	with open(SAVE_DIR + '\\advertising.csv', 'a', newline='') as f:
		writer = csv.writer(f)
		# 時間,広告種類(7つ分),内容(最大2つ),正解画面か不正解画面か(2つ), 上下の場合はcontent[0][-4]の次にcontents[1][:-4]を追加
		writer.writerow([time,ad_kinds[0],ad_kinds[1],ad_kinds[2],ad_kinds[3],ad_kinds[4],ad_kinds[5],ad_kinds[6],contents[0][:-4],rw[0],rw[1]])

# 画像を選択しパスをnext_im_sikaku_pathとnext_im_yoko_pathに格納する関数 追加で一度表示した画像を一周するまで表示しない処理いれた
def select_ad_image(ad_kind):
	global im_yoko_list, im_sikaku_list, im_simple_yoko_list, im_simple_sikaku_list, next_im_yoko_list, next_im_sikaku_list, \
	next_im_yoko_path, next_im_sikaku_path, now_dir, now_dir2, SIKAKU_DIR, YOKO_DIR, SIMPLE_SIKAKU_DIR, SIMPLE_YOKO_DIR
	
	if ad_kind == 0:
		(next_im_yoko_list, next_im_sikaku_list) = ("", "")
		return

	if ad_kind % 2 == 0: # 一般画像 ← positive
		next_im_yoko_path = random.choice(im_yoko_list)
		next_im_sikaku_path = random.choice(im_sikaku_list)
		
		im_yoko_list.remove(next_im_yoko_path)
		im_sikaku_list.remove(next_im_sikaku_path)
		if len(im_yoko_list) <= 0:
			im_yoko_list = get_image(YOKO_DIR)
			print("reset yoko image list") # デバッグ用
		if len(im_sikaku_list) <= 0:
			im_sikaku_list = get_image(SIKAKU_DIR)
			print("reset sikaku image list") # デバッグ用
		
		now_dir = SIKAKU_DIR
		now_dir2 = YOKO_DIR
	else: # 刺激画像 ← negative
		next_im_yoko_path = random.choice(im_simple_yoko_list)
		next_im_sikaku_path = random.choice(im_simple_sikaku_list)
		
		im_simple_yoko_list.remove(next_im_yoko_path)
		im_simple_sikaku_list.remove(next_im_sikaku_path)
		if len(im_simple_yoko_list) <= 0:
			im_simple_yoko_list = get_image(SIMPLE_YOKO_DIR)
			print("reset simple yoko image list") # デバッグ用
		if len(im_simple_sikaku_list) <= 0:
			im_simple_sikaku_list = get_image(SIMPLE_SIKAKU_DIR)
			print("reset simple sikaku image list") # デバッグ用
		
		now_dir = SIMPLE_SIKAKU_DIR
		now_dir2 = SIMPLE_YOKO_DIR

# 枠線描く関数, id==1で前面時の枠, それ以外で下広告時の枠
def create_wakusen(id):
	global SIZE_ZENMEN, SIZE_SIKAKU, items_wakusen, canvas
	
	if id == 1: # zenmen
		size_x = int(SIZE_ZENMEN[0:3])
		size_y = int(SIZE_ZENMEN[4:7])
	else: # jouge(sita)
		size_x = int(SIZE_SIKAKU[0:3])
		size_y = int(SIZE_SIKAKU[4:7])
	
	for item in items_wakusen:
		canvas.delete(item)
	
	items_wakusen[0] = canvas.create_line(0+2, 0+2, 0+2, size_y+2, fill='gray', width = 4)
	items_wakusen[1] = canvas.create_line(0+2, size_y+2, size_x+2, size_y+2, fill='gray', width = 4)
	items_wakusen[2] = canvas.create_line(size_x+2, size_y+2, size_x+2, 0+2, fill='gray', width = 4)
	items_wakusen[3] = canvas.create_line(size_x+2, 0+2, 0+2, 0+2, fill='gray', width = 4)
	# 二重線
	items_wakusen[4] = canvas.create_line(0+2+10, 0+2+10, 0+2+10, size_y+2-10, fill='gray', width = 2)
	items_wakusen[5] = canvas.create_line(0+2+10, size_y+2-10, size_x+2-10, size_y+2-10, fill='gray', width = 2)
	items_wakusen[6] = canvas.create_line(size_x+2-10, size_y+2-10, size_x+2-10, 0+2+10, fill='gray', width = 2)
	items_wakusen[7] = canvas.create_line(size_x+2-10, 0+2+10, 0+2+10, 0+2+10, fill='gray', width = 2)

# リセット区間中に呼び出される,広告表示の準備をする関数
def set_display_ad(ad_kind):
	global root, root2, canvas, canvas2, item, item2, CLOSE_DIR, POS_ZENMEN, \
	POS_JOUGE_TOP_QUIZ, POS_JOUGE_BUTTOM_QUIZ, POS_JOUGE_TOP_RESULT, POS_JOUGE_BUTTOM_RESULT, \
	SIZE_YOKO, SIZE_SIKAKU, img, img2, SIZE_ZENMEN, WHITE_TRANS_PATH, SIZE_WINDOW, \
	next_im_sikaku_path, next_im_yoko_path, disp_ready, ignore_num, IGNORE_MAX, \
	POS_BUTTON_TOJIRU
	
	select_ad_image(ad_kind) # 次の画像の準備
	
	if ad_kind == 0: # select_ad_image()でもad_kind == 0の時を処理をしたいので後に書いてる
		return
	
	print("next_im_sikaku_path is" + str(next_im_sikaku_path)) # デバッグ用
	print("next_im_yoko_path is" + str(next_im_yoko_path))
	
	canvas.delete(item) ## 追加
	canvas2.delete(item2)
	
	# 表示場所やボタンの設定
	pos, pos2 = (None, None)
	geo = None
	if ad_kind == 1 or ad_kind == 2: # 上下 ← 上下から下のみに変更
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
		create_wakusen(0)
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
		root.roundedbutton.place(x=int(POS_BUTTON_TOJIRU[0:3])+2,y=int(POS_BUTTON_TOJIRU[4:7])+2)
		pos = POS_ZENMEN
		pos2 = "0+0"
		geo = SIZE_ZENMEN + "+" + pos
		geo2 = SIZE_WINDOW + "+" + pos2
		img2 = ImageTk.PhotoImage(file=WHITE_TRANS_PATH, master=root2)
		root2.attributes('-alpha', 0.002) # 半透明, 透明と半透明のギリギリが0.02あたりだった
		root2.attributes("-topmost", False) # 最前面だと閉じる押せなくなるから
		ignore_num = random.randint(1, IGNORE_MAX)
		create_wakusen(1)
	
	root.attributes('-alpha', 1.0)
	root.geometry(geo)
	root2.geometry(geo2)
	img = ImageTk.PhotoImage(file=next_im_sikaku_path, master=root)
	
	if ad_kind == 1 or ad_kind == 2:
		#canvas.itemconfig(item, image=img) # なぜか真っ白
		#canvas2.itemconfig(item2, image=img2)
		item = canvas.create_image(0+2+PADDING, 0+2+PADDING, image=img, anchor=tkinter.NW)
		item2 = canvas2.create_image(0, 0, image=img2, anchor=tkinter.NW)	
		canvas.place(x=-2, y=-2)
		canvas2.place(x=-2, y=-2)
	else:
		item = canvas.create_image(0+2+PADDING, 0+2+PADDING, image=img, anchor=tkinter.NW)
		item2 = canvas2.create_image(0, 0, image=img2, anchor=tkinter.NW)
		canvas.place(x=-2, y=-2)
		canvas2.place(x=-2, y=-2)
		
	disp_ready = True

# 広告表示関数(is_dispをオンにできる関数)
def display_ad(ad_kind):
	global root, root2, is_disp, cur_im_sikaku_path, cur_im_yoko_path, next_im_sikaku_path, next_im_yoko_path
	
	cur_im_sikaku_path = next_im_sikaku_path
	cur_im_yoko_path = next_im_yoko_path
	
	if ad_kind != 0: # 刺激区間中の無刺激区間でなければ
		root.deiconify()
		
		if not( ad_kind == 1 or ad_kind == 2 ):
			root2.deiconify()
			root2.attributes("-topmost", True) # 最前面 → キャンセルで背景がブラウザの下にいかないように
			root2.attributes("-topmost", False)
			#root2.lift() # 漏れがありそうなのでコメントアウト
	
	is_disp = True

# 広告非表示関数
def hide_ad():
	global is_disp, time_close, root, root2, disp_ready

	display_white_moment()
	
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
	flag_close, is_disp, time_close, FPS, cur_im_sikaku_path, cur_im_yoko_path, disp_ready, flag_click
	
	im_yoko_path, im_sikaku_path = (None, None) # 宣言だけでも local

	while flag_pose == False or flag_cap == False:
		pass

	# 別スレッドのset_canvasが終わるまで待つ
	event.wait()

	options = webdriver.ChromeOptions()
	options.add_experimental_option("excludeSwitches", ['enable-automation'])
	driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=options)
	#ef_driver = EventFiringWebDriver(driver, MyListener())
	driver.maximize_window()
	driver.get("http://3.134.34.102/")

	# enterキー押すまで待機
	keyboard_listener = keyboard.Listener(on_release=on_release)
	keyboard_listener.start()
	while flag_auto_click == False: # オートクリックしてた名残
		pass

	# クイズスタート時のタイムスタンプ & 記録
	start = time.perf_counter()
	start_quiz_date = time.time() # 上の行との間に小さなズレがあるかも
	with open(SAVE_DIR+'\\startTime.csv','a',newline='') as f: # プログラム開始終了タイムスタンプ
		writer = csv.writer(f)
		writer.writerow(['randomAd',start_quiz_date])
	
	"""
	# クリック等取得
	mouse_listener = mouse.Listener(on_click=on_click)
	mouse_listener.start()
	"""
	
	print("wait " + str(TIME_FIRSTWAITING) + " second") # デバッグ用
	time_before = 0 - FPS # ループがいきなり始まってほしいので
	while get_elapsed_time() < TIME_FIRSTWAITING: # 最初待機 + 一応ログ
		elapsed = get_elapsed_time()
		if elapsed - time_before < 1.0 / FPS: # 前のループからそこまで時間が経っていない場合 中の処理重い場合かなりズレが出てくる
			continue
		
		time_before = elapsed
		
		check_url(driver)
		
		#click_log(elapsed)
			
		if elapsed >= TIME_FIRSTWAITING:
			break
		
		ad_log(elapsed, 0, is_result, is_correct, False, "", "")

	time_close = 0 - TIME_RESET # 練習後に15秒リセット後と同じ動作をさせるため
	print("for-while loop start") # デバッグ用
	for i in range(NUM_LOOP):
		random.shuffle(ad_kinds)
		setcount = 0 # 範囲は0~6
		#ad_kinds = [3,6,4,2,5,1,0] # デバッグ用
		while setcount <= len(ad_kinds) - 1:
			elapsed = get_elapsed_time()
			if elapsed - time_before < 1.0 / FPS: # 前のループからそこまで時間が経っていない場合
				continue
			time_before = elapsed
			
			is_disp_in_loop = is_disp # 1ループ中に切り替わることを防ぐための変数(排他制御したいけど難しそうなので妥協)
			flag_close_in_loop = flag_close # 同様
			
			check_url(driver)
			
			#click_log(elapsed)

			# 終了画面になった時
			if flag_finish == True:
				break;
			
			# 次の表示の準備
			if is_disp_in_loop == False and disp_ready == False and flag_close_in_loop == False: # flag_close_in_loop == Falseによりsetcountは増加した後の値になる
				set_display_ad(ad_kinds[setcount])

			if elapsed - int(elapsed) <= 0.01: # デバッグ用
				print(elapsed)
				print(setcount)
				print(ad_kinds[setcount])
			
			# 前面系で閉じるボタンが押された時の処理
			if flag_close_in_loop == True:
				setcount = setcount + 1
				disp_ready = False
				flag_close = False
				flag_close_in_loop = False

			if elapsed - time_close >= TIME_RESET: # 刺激区間
				#root2.lift() # 透過背景がブラウザの下に行かないように
				
				if flag_trans == True: # 画面遷移した場合
					if is_result == False: # 出題画面の場合
						# 広告表示
						display_ad(ad_kinds[setcount])
						is_disp_in_loop = True

					else: # 正解表示画面
						if is_disp == True: # 既に広告表示されている場合, is_disp_in_loopじゃないのはis_dispがイベントで変更されるのは前面系の時だけだからここは大丈夫
							hide_ad()
							is_disp_in_loop = False
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
			ad_log(elapsed, ad_kinds[suf], is_result, is_correct, is_disp_in_loop, cur_im_sikaku_path, cur_im_yoko_path)
		
		
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
			ad_log(elapsed, 0, is_result, is_correct, False, "", "")
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
