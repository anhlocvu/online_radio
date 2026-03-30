# -*- coding: utf-8 -*-

# Online Radio Technology Entertainment
# Developer: Technology Entertainment
# Coder: LCBoy - Lập trình viên mù 
# Phiên bản: 2.1 - Tải cấu hình Cloud qua Requests và Tối ưu NVDA

import sys
import wx
import wx.media
import threading
import os
import json
import requests
from datetime import datetime

# --- Cấu hình Cloud ---
CONFIG_URL = "https://lc.ktgame207.com/radio/config.json"

# --- ID ---
ID_EXIT = wx.ID_EXIT
ID_ABOUT = wx.ID_ABOUT
ID_STOP_PLAYBACK = wx.ID_HIGHEST + 3
ID_MUTE_TOGGLE = wx.ID_HIGHEST + 4
ID_CLEAR_LOG = wx.ID_HIGHEST + 5

# --- Class Logger ---
class GuiLogger:
    def __init__(self, log_ctrl):
        self.log_ctrl = log_ctrl

    def log_message(self, message, error=False, debug=False):
        if debug: return
        now = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{now}] {message}\n"
        def append_text():
            if hasattr(self, 'log_ctrl') and self.log_ctrl:
                try:
                    color = wx.RED if error else wx.WHITE
                    self.log_ctrl.SetDefaultStyle(wx.TextAttr(color))
                    self.log_ctrl.AppendText(log_line)
                    self.log_ctrl.SetDefaultStyle(wx.TextAttr(wx.WHITE))
                except: pass
        wx.CallAfter(append_text)

class RadioFrame(wx.Frame):
    def __init__(self, parent, title):
        super(RadioFrame, self).__init__(parent, title=title, size=(700, 800))

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(20, 20, 20)) 
        self.panel.SetForegroundColour(wx.WHITE)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Khu vực Danh sách Kênh ---
        channel_box = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Danh sách Kênh")
        channel_box.GetStaticBox().SetForegroundColour(wx.CYAN)
        
        self.channel_listbox = wx.ListBox(self.panel, style=wx.LB_SINGLE)
        self.channel_listbox.SetName("Danh sách các đài phát thanh. Sử dụng mũi tên để chọn, Enter để phát.")
        self.channel_listbox.SetBackgroundColour(wx.Colour(40, 40, 40))
        self.channel_listbox.SetForegroundColour(wx.WHITE)
        self.channel_listbox.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        channel_box.Add(self.channel_listbox, 1, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(channel_box, 1, wx.EXPAND | wx.ALL, 15)

        # --- Khu vực Điều khiển và Phát ---
        playback_box = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Trình phát")
        playback_box.GetStaticBox().SetForegroundColour(wx.CYAN)
        
        self.now_playing_text = wx.StaticText(self.panel, label="Trạng thái: Sẵn sàng.")
        self.now_playing_text.SetName("Thông tin trạng thái hiện tại")
        self.now_playing_text.SetForegroundColour(wx.Colour(0, 255, 127))
        self.now_playing_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        playback_box.Add(self.now_playing_text, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.stop_button = wx.Button(self.panel, ID_STOP_PLAYBACK, "&Dừng phát")
        self.stop_button.SetName("Dừng phát nhạc")
        
        self.mute_button = wx.ToggleButton(self.panel, ID_MUTE_TOGGLE, "&Tắt tiếng")
        self.mute_button.SetName("Bật hoặc tắt âm thanh")
        
        volume_label = wx.StaticText(self.panel, label="Âm lượng:")
        # Đã bỏ wx.SL_LABELS để NVDA đọc chuẩn, và đặt giá trị mặc định là 50
        self.volume_slider = wx.Slider(self.panel, value=50, minValue=0, maxValue=100, style=wx.SL_HORIZONTAL)
        self.volume_slider.SetName("Âm lượng") 
        self.volume_slider.SetMinSize((200, -1))
        
        controls_sizer.Add(self.stop_button, 0, wx.RIGHT, 15)
        controls_sizer.Add(self.mute_button, 0, wx.RIGHT, 15)
        controls_sizer.Add(volume_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        controls_sizer.Add(self.volume_slider, 1, wx.ALIGN_CENTER_VERTICAL)
        
        playback_box.Add(controls_sizer, 0, wx.EXPAND | wx.ALL, 10)
        main_sizer.Add(playback_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # --- Khu vực Log Box ---
        log_box = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Nhật ký hoạt động")
        log_box.GetStaticBox().SetForegroundColour(wx.Colour(200, 200, 200))
        
        self.log_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.log_ctrl.SetName("Nội dung nhật ký hoạt động")
        self.log_ctrl.SetBackgroundColour(wx.Colour(10, 10, 10))
        self.log_ctrl.SetForegroundColour(wx.Colour(220, 220, 220))
        self.log_ctrl.SetMinSize((-1, 100))
        
        log_box.Add(self.log_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        
        self.clear_log_button = wx.Button(self.panel, ID_CLEAR_LOG, "&Xóa nhật ký")
        self.clear_log_button.SetName("Xóa trắng nhật ký")
        log_box.Add(self.clear_log_button, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, 5)
        
        main_sizer.Add(log_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        self.statusBar = self.CreateStatusBar(1)
        self.SetStatusText("Sẵn sàng.")
        
        self.panel.SetSizer(main_sizer)

        # --- Thứ tự Tab ---
        self.channel_listbox.MoveBeforeInTabOrder(self.stop_button)
        self.stop_button.MoveBeforeInTabOrder(self.mute_button)
        self.mute_button.MoveBeforeInTabOrder(self.volume_slider)
        self.volume_slider.MoveBeforeInTabOrder(self.log_ctrl)
        self.log_ctrl.MoveBeforeInTabOrder(self.clear_log_button)

        # ----- Khởi tạo Dữ liệu -----
        self.gui_logger = GuiLogger(self.log_ctrl)
        self.channels = {}
        self.current_playing_url = None
        self.current_channel_name = ""
        self.previous_volume = 50
        self.media_player = None
        self.user_stopped = False 
        self.play_start_time = datetime.now()

        self.load_config()
        self.populate_channel_list()

        # ----- Tạo Menu & Bind Events -----
        self._create_menubar()
        self._bind_events()
        
        self.stop_button.Disable()
        self.mute_button.Disable()
        self.volume_slider.Disable()

        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('D'), ID_STOP_PLAYBACK),
            (wx.ACCEL_ALT, ord('T'), ID_MUTE_TOGGLE),
            (wx.ACCEL_CTRL, ord('L'), ID_CLEAR_LOG)
        ])
        self.SetAcceleratorTable(accel_tbl)

        self.Centre()
        self.Show()
        self.channel_listbox.SetFocus()
        self.log_message("Phần mềm Radio Online TE v2.1 sẵn sàng!")

    def _create_media_player_if_needed(self):
        if self.media_player is None:
            try:
                try: self.media_player = wx.media.MediaCtrl(self.panel, szBackend=wx.media.MEDIABACKEND_WMP10)
                except: self.media_player = wx.media.MediaCtrl(self.panel)
                self.media_player.Hide()
                self.Bind(wx.media.EVT_MEDIA_LOADED, self.on_media_loaded, self.media_player)
                self.Bind(wx.media.EVT_MEDIA_STOP, self.on_media_stopped_or_finished, self.media_player)
                self.Bind(wx.media.EVT_MEDIA_FINISHED, self.on_media_stopped_or_finished, self.media_player)
                return True
            except Exception as e:
                self.log_message(f"Lỗi trình phát: {e}", error=True)
                return False
        return True

    def log_message(self, message, error=False, debug=False):
        if hasattr(self, 'gui_logger'): self.gui_logger.log_message(message, error, debug)

    def _create_menubar(self):
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu(); help_menu = wx.Menu()
        exit_item = file_menu.Append(ID_EXIT, "Thoát (&X)\tAlt+X")
        about_item = help_menu.Append(ID_ABOUT, "Giới thiệu (&G)\tF1")
        menu_bar.Append(file_menu, "&Tệp"); menu_bar.Append(help_menu, "&Trợ giúp")
        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

    def _bind_events(self):
        self.Bind(wx.EVT_CLOSE, self.on_exit)
        self.channel_listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.on_channel_select)
        self.Bind(wx.EVT_BUTTON, self.on_stop_playback, id=ID_STOP_PLAYBACK)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_mute_toggle, id=ID_MUTE_TOGGLE)
        self.volume_slider.Bind(wx.EVT_SLIDER, self.on_volume_change)
        self.Bind(wx.EVT_BUTTON, id=ID_CLEAR_LOG, handler=lambda e: self.log_ctrl.Clear())
        self.channel_listbox.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.channel_listbox.Bind(wx.EVT_CHAR, self.on_key_down)

    def on_key_down(self, event):
        if event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE]:
            self.on_channel_select(None)
        else: event.Skip()

    def on_exit(self, event):
        self.user_stopped = True
        if self.media_player: self.media_player.Stop()
        self.Destroy()

    def on_about(self, event):
        wx.MessageBox("Online Radio TE v2.1\n\nCoder: LCBoy (Vũ Anh Lộc)\nTải cấu hình trực tiếp từ Cloud (Requests).", "Giới thiệu", wx.OK | wx.ICON_INFORMATION)

    def load_config(self):
        self.log_message("Đang tải danh sách kênh từ máy chủ...")
        def _fetch():
            try:
                # Sử dụng requests để tải trực tiếp vào RAM, không lưu file
                response = requests.get(CONFIG_URL, timeout=10)
                response.raise_for_status()
                data = response.json()
                self.channels = data.get("Channels", {})
                wx.CallAfter(self.populate_channel_list)
                wx.CallAfter(self.log_message, f"Đã tải thành công {len(self.channels)} kênh.")
            except Exception as e:
                wx.CallAfter(self.log_message, "Lỗi tải cấu hình từ máy chủ.", error=True)
                wx.CallAfter(wx.MessageBox, "Không tải được danh sách kênh từ máy chủ.\nVui lòng kiểm tra mạng!", "Lỗi", wx.OK | wx.ICON_ERROR)
        
        threading.Thread(target=_fetch, daemon=True).start()

    def populate_channel_list(self):
        self.channel_listbox.Clear()
        for name in sorted(self.channels.keys()):
            self.channel_listbox.Append(name)

    def on_channel_select(self, event):
        sel = self.channel_listbox.GetSelection()
        if sel == wx.NOT_FOUND: return
        name = self.channel_listbox.GetString(sel); url = self.channels[name]
        
        self.log_message(f"Kết nối tới: {name}...")
        self.now_playing_text.SetLabelText(f"Đang kết nối: {name}...")
        self.now_playing_text.SetForegroundColour(wx.Colour(255, 255, 0))
        
        self.user_stopped = True
        if self.media_player: self.media_player.Stop()
        
        self.user_stopped = False
        self.current_channel_name = name
        self.play_start_time = datetime.now()
        
        if self._create_media_player_if_needed(): self.media_player.Load(url)
        else: self.playback_failed(name, "Lỗi trình phát.")

    def on_media_loaded(self, event):
        if not self.media_player: return
        self.user_stopped = False
        self.play_start_time = datetime.now()
        self.media_player.Play()
        self.now_playing_text.SetLabelText(f"Đang phát: {self.current_channel_name}")
        self.now_playing_text.SetForegroundColour(wx.Colour(0, 255, 127))
        self.SetStatusText(f"Đang phát: {self.current_channel_name}")
        self.stop_button.Enable(); self.mute_button.Enable(); self.volume_slider.Enable(); self.apply_volume()
        self.stop_button.SetFocus()
        wx.LogStatus(f"Bắt đầu phát {self.current_channel_name}")

    def on_media_stopped_or_finished(self, event):
        if self.user_stopped: event.Skip(); return
        if (datetime.now() - self.play_start_time).total_seconds() < 15:
            event.Skip(); return
        if self.media_player and self.current_channel_name:
            channel = self.current_channel_name
            self.log_message(f"Luồng '{channel}' bị ngắt, đang thử kết nối lại...")
            self.media_player.Play()
            wx.CallLater(5000, self.check_real_error, channel, 1)
        event.Skip()

    def check_real_error(self, channel_name, attempt):
        if not self.media_player or self.user_stopped or self.current_channel_name != channel_name: return
        if self.media_player.GetState() == wx.media.MEDIASTATE_PLAYING: return
        if attempt < 3:
            self.media_player.Play()
            wx.CallLater(5000, self.check_real_error, channel_name, attempt + 1)
        else: self.playback_failed(channel_name, "Mất kết nối máy chủ.")

    def playback_failed(self, name, reason):
        if self.user_stopped: return
        if self.media_player and self.media_player.GetState() == wx.media.MEDIASTATE_PLAYING: return
        self.log_message(f"Sự cố: {reason}", error=True)
        wx.MessageBox(f"Đã có sự cố khi chuẩn bị luồng hoặc mất kết nối.\nKênh: {name}", "Lỗi", wx.OK | wx.ICON_ERROR)
        self.stop_playback_ui()

    def on_stop_playback(self, event):
        self.user_stopped = True
        if self.media_player: self.media_player.Stop()
        self.stop_playback_ui()

    def stop_playback_ui(self):
        self.user_stopped = True
        self.channel_listbox.SetFocus()
        self.now_playing_text.SetLabelText("Trạng thái: Sẵn sàng.")
        self.now_playing_text.SetForegroundColour(wx.Colour(0, 255, 127))
        self.SetStatusText("Sẵn sàng.")
        self.current_channel_name = ""
        self.stop_button.Disable(); self.mute_button.Disable(); self.volume_slider.Disable()
        wx.LogStatus("Đã dừng phát")

    def on_mute_toggle(self, event):
        if not self.media_player: return
        if self.mute_button.GetValue():
            self.previous_volume = self.volume_slider.GetValue(); self.media_player.SetVolume(0.0); self.volume_slider.Disable()
        else:
            self.volume_slider.Enable(); self.volume_slider.SetValue(self.previous_volume); self.apply_volume()

    def on_volume_change(self, event):
        self.apply_volume()
        vol = self.volume_slider.GetValue()
        self.SetStatusText(f"Âm lượng {vol}%")
        wx.LogStatus(f"Âm lượng {vol} phần trăm")

    def apply_volume(self):
        if self.media_player:
            vol = self.volume_slider.GetValue(); self.media_player.SetVolume(vol / 100.0)
            if vol == 0: self.mute_button.SetValue(True); self.volume_slider.Disable()

if __name__ == '__main__':
    app = wx.App(False)
    RadioFrame(None, "Online Radio Technology Entertainment")
    app.MainLoop()
