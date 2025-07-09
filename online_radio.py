# -*- coding: utf-8 -*-

# Online Radio Technology Entertainment
# Developer: Technology Entertainment
# Coder: LCBoy - Lập trình viên mù 
# <<< ĐÃ SỬA TÊN
# Phiên bản: 1.7 - Cập nhật tên Coder, sửa lỗi trước đó

import wx
import wx.media
import threading
import os
import configparser
from datetime import datetime
import subprocess

# --- ID (Giữ nguyên) ---
ID_EXIT = wx.ID_EXIT; ID_ABOUT = wx.ID_ABOUT; ID_ADD_CHANNEL = wx.ID_HIGHEST + 1
ID_REMOVE_CHANNEL = wx.ID_HIGHEST + 2; ID_STOP_PLAYBACK = wx.ID_HIGHEST + 3
ID_MUTE_TOGGLE = wx.ID_HIGHEST + 4; ID_CLEAR_LOG = wx.ID_HIGHEST + 5

# --- Config và Default Channels (Giữ nguyên) ---
CONFIG_FILE = "radio_config.ini"
DEFAULT_CHANNELS = { "LC channel": "http://ktgame207.com:8000/lc", "KT Game channel": "http://ktgame207.com:8000/live", "nnh channel": "http://ktgame207.com:8000/nnh","đông trường channel":"http://ktgame207.com:8000/dongtruong"}

# --- Class Logger (Giữ nguyên) ---
class GuiLogger:
    def __init__(self, log_ctrl): self.log_ctrl = log_ctrl
    def log_message(self, message, error=False, debug=False):
        if debug: return
        now = datetime.now().strftime("%H:%M:%S"); log_line = f"[{now}] {message}\n"
        def append_text():
            if hasattr(self, 'log_ctrl') and self.log_ctrl:
                try: color = wx.RED if error else wx.WHITE; self.log_ctrl.SetDefaultStyle(wx.TextAttr(color)); self.log_ctrl.AppendText(log_line); self.log_ctrl.SetDefaultStyle(wx.TextAttr(wx.WHITE))
                except: print(f"LOG (wxError): {log_line.strip()}")
            else: print(f"LOG (No GUI): {log_line.strip()}")
        wx.CallAfter(append_text)
# -------------------------------------------------

class RadioFrame(wx.Frame):
    def __init__(self, parent, title):
        super(RadioFrame, self).__init__(parent, title=title, size=(600, 700))

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(30, 30, 30)); self.panel.SetForegroundColour(wx.WHITE)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Khu vực Danh sách Kênh (Giữ nguyên) ---
        channel_box = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Danh sách Kênh")
        channel_box.GetStaticBox().SetForegroundColour(wx.WHITE)
        self.channel_listbox = wx.ListBox(self.panel, style=wx.LB_SINGLE)
        self.channel_listbox.SetBackgroundColour(wx.Colour(50, 50, 50)); self.channel_listbox.SetForegroundColour(wx.WHITE)
        channel_box.Add(self.channel_listbox, 1, wx.EXPAND | wx.ALL, 5)
        channel_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL); add_button = wx.Button(self.panel, ID_ADD_CHANNEL, "Thêm"); remove_button = wx.Button(self.panel, ID_REMOVE_CHANNEL, "Xóa"); remove_button.Disable()
        channel_buttons_sizer.Add(add_button, 0, wx.RIGHT, 5); channel_buttons_sizer.Add(remove_button, 0); channel_box.Add(channel_buttons_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 5)
        main_sizer.Add(channel_box, 1, wx.EXPAND | wx.ALL, 10)

        # --- Khu vực Điều khiển và Phát (Giữ nguyên) ---
        self.player_area_sizer = wx.BoxSizer(wx.VERTICAL)
        self.now_playing_text = wx.StaticText(self.panel, label="Chưa phát kênh nào."); self.now_playing_text.SetForegroundColour(wx.CYAN)
        self.player_area_sizer.Add(self.now_playing_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self.player_placeholder = wx.Panel(self.panel, size=(-1, 50)); self.player_placeholder.SetBackgroundColour(self.panel.GetBackgroundColour())
        self.player_area_sizer.Add(self.player_placeholder, 0, wx.EXPAND | wx.ALL, 5)
        self.media_player = None # Khởi tạo là None
        self.custom_controls_sizer = wx.BoxSizer(wx.HORIZONTAL); self.stop_button = wx.Button(self.panel, ID_STOP_PLAYBACK, "Dừng"); self.mute_button = wx.ToggleButton(self.panel, ID_MUTE_TOGGLE, "Tắt tiếng"); volume_label = wx.StaticText(self.panel, label="Âm lượng:"); self.volume_slider = wx.Slider(self.panel, value=80, minValue=0, maxValue=100, style=wx.SL_HORIZONTAL); self.volume_slider.SetMinSize((150, -1))
        self.custom_controls_sizer.Add(self.stop_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10); self.custom_controls_sizer.Add(self.mute_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10); self.custom_controls_sizer.Add(volume_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5); self.custom_controls_sizer.Add(self.volume_slider, 1, wx.ALIGN_CENTER_VERTICAL)
        self.player_area_sizer.Add(self.custom_controls_sizer, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.player_area_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.player_area_sizer.ShowItems(False) # Ẩn ban đầu

        # --- Khu vực Log Box (Giữ nguyên) ---
        log_sizer = wx.StaticBoxSizer(wx.VERTICAL, self.panel, "Nhật ký"); log_sizer.GetStaticBox().SetForegroundColour(wx.WHITE); self.log_ctrl = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2|wx.HSCROLL); self.log_ctrl.SetBackgroundColour(wx.Colour(10,10,10)); self.log_ctrl.SetForegroundColour(wx.Colour(220,220,220)); self.log_ctrl.SetMinSize((-1, 80)); log_sizer.Add(self.log_ctrl, 1, wx.EXPAND|wx.ALL, 5); clear_log_button = wx.Button(self.panel, ID_CLEAR_LOG, "Xóa Nhật ký"); log_sizer.Add(clear_log_button, 0, wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, 5); main_sizer.Add(log_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        # --- Status Bar (Giữ nguyên) ---
        self.statusBar = self.CreateStatusBar(1); self.SetStatusText("Sẵn sàng.")
        self.panel.SetSizer(main_sizer)

        # ----- Khởi tạo Logger, Data, Config -----
        self.gui_logger = GuiLogger(self.log_ctrl)
        self.channels = {}; self.current_playing_url = None; self.previous_volume = 80
        self.load_config(); self.populate_channel_list()

        # ----- Tạo Menu, Bind Events, Hoàn thiện -----
        self._create_menubar()
        self._bind_events() # Bind sự kiện không liên quan media player trước
        self.Centre(); self.Show()
        self.log_message("Radio Online TE v1.8 (LCBoy Coder) sẵn sàng!")

    def _create_media_player_if_needed(self): # Giữ nguyên
        if self.media_player is None:
            self.log_message("Creating new MediaCtrl instance...")
            try:
                player_style = wx.SIMPLE_BORDER
                try: self.media_player = wx.media.MediaCtrl(self.panel, style=player_style, szBackend=wx.media.MEDIABACKEND_WMP10); self.log_message("MediaCtrl created (Backend: WMP10).")
                except: self.media_player = wx.media.MediaCtrl(self.panel, style=player_style); self.log_message("MediaCtrl created (Backend: Default).")
                self.media_player.SetMinSize((-1, 50))
                placeholder_index = -1;
                for i, item in enumerate(self.player_area_sizer.GetChildren()):
                    if item.GetWindow() == self.player_placeholder: placeholder_index = i; break
                if placeholder_index != -1:
                    self.player_area_sizer.Hide(placeholder_index); self.player_area_sizer.Remove(placeholder_index); self.player_area_sizer.Insert(placeholder_index, self.media_player, 0, wx.EXPAND | wx.ALL, 5); self.log_message(f"Inserted new MediaCtrl at index {placeholder_index}.")
                else: self.log_message("Placeholder not found!", error=True); self.player_area_sizer.Insert(1, self.media_player, 0, wx.EXPAND | wx.ALL, 5)
                # Bind events for new player
                self.Bind(wx.media.EVT_MEDIA_LOADED, self.on_media_loaded, self.media_player); self.Bind(wx.media.EVT_MEDIA_STOP, self.on_media_stopped_or_finished, self.media_player); self.Bind(wx.media.EVT_MEDIA_FINISHED, self.on_media_stopped_or_finished, self.media_player)
                self.panel.Layout() # Update layout
                return True
            except Exception as e: self.log_message(f"FATAL: Cannot recreate MediaCtrl: {e}", error=True); wx.MessageBox(f"Lỗi tạo player:\n{e}", "Lỗi", wx.OK|wx.ICON_ERROR); self.media_player = None; return False
        else: return True # Already exists

    def _destroy_media_player(self): # Giữ nguyên
        if self.media_player:
            player_to_destroy = self.media_player; self.media_player = None
            self.log_message("Destroying old MediaCtrl instance...")
            try: # Replace with placeholder
                 placeholder_index = -1
                 for i, item in enumerate(self.player_area_sizer.GetChildren()):
                     if item.GetWindow() == player_to_destroy: placeholder_index = i; break
                 if placeholder_index != -1:
                      self.player_area_sizer.Hide(placeholder_index); self.player_area_sizer.Remove(placeholder_index); self.player_area_sizer.Insert(placeholder_index, self.player_placeholder, 0, wx.EXPAND | wx.ALL, 5); self.player_area_sizer.Show(placeholder_index); self.log_message("Replaced MediaCtrl with placeholder.")
                      self.panel.Layout()
                 else: self.log_message("Old MediaCtrl not found in sizer.", error=True)
            except Exception as e_remove: self.log_message(f"Error removing MediaCtrl: {e_remove}", error=True)
            wx.CallAfter(player_to_destroy.Destroy); self.log_message("Destroy request sent.")

    # --- Log, Clear Log, Menu, Bind Events, Exit, About ---
    def log_message(self, message, error=False, debug=False): # Giữ nguyên
        if hasattr(self,'gui_logger'): self.gui_logger.log_message(message,error,debug)
        else: print(f"LOG: {message}")
    def on_clear_log(self, event): # Giữ nguyên
        if self.log_ctrl: self.log_ctrl.Clear(); self.log_message("Nhật ký đã xóa.")
    def _create_menubar(self): # Giữ nguyên
        menu_bar=wx.MenuBar(); file_menu=wx.Menu(); help_menu=wx.Menu(); exit_item=file_menu.Append(ID_EXIT,"Thoát"); about_item=help_menu.Append(ID_ABOUT,"Giới thiệu"); menu_bar.Append(file_menu,"Tệp"); menu_bar.Append(help_menu,"Giúp"); self.SetMenuBar(menu_bar); self.Bind(wx.EVT_MENU,self.on_exit,exit_item); self.Bind(wx.EVT_MENU,self.on_about,about_item)
    def _bind_events(self): # Giữ nguyên
        self.Bind(wx.EVT_MENU,self.on_exit,id=ID_EXIT); self.Bind(wx.EVT_MENU,self.on_about,id=ID_ABOUT); self.Bind(wx.EVT_CLOSE,self.on_exit)
        self.channel_listbox.Bind(wx.EVT_LISTBOX, self.on_channel_select); self.channel_listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.on_channel_select); self.Bind(wx.EVT_BUTTON, self.on_add_channel, id=ID_ADD_CHANNEL); self.Bind(wx.EVT_BUTTON, self.on_remove_channel, id=ID_REMOVE_CHANNEL); self.channel_listbox.Bind(wx.EVT_LISTBOX, self.update_remove_button_state)
        self.Bind(wx.EVT_BUTTON, self.on_stop_playback, id=ID_STOP_PLAYBACK); self.Bind(wx.EVT_TOGGLEBUTTON, self.on_mute_toggle, id=ID_MUTE_TOGGLE); self.volume_slider.Bind(wx.EVT_SLIDER, self.on_volume_change)
        self.Bind(wx.EVT_BUTTON, self.on_clear_log, id=ID_CLEAR_LOG)
    def on_exit(self, event): # Giữ nguyên (đã sửa lỗi)
        self.log_message("Closing..."); self.stop_playback(force_destroy=True); self.Destroy()
    def on_about(self, event):
        # ***** SỬA TÊN CODER TRONG ABOUT *****
        wx.MessageBox("Online Radio TE v1.8\n\nNhà phát triển: Technology Entertainment\nCoder: LCBoy",
                      "Giới thiệu", wx.OK | wx.ICON_INFORMATION)
    # ------------------------------------

    # --- Config Handling (Giữ nguyên) ---
    def load_config(self): # Giữ nguyên
        self.log_message(f"Loading config: {CONFIG_FILE}...")
        config = configparser.ConfigParser();
        if not os.path.exists(CONFIG_FILE): self.log_message("Config not found, creating default."); self.create_default_config()
        try:
            config.read(CONFIG_FILE, encoding='utf-8')
            if 'Channels' in config: self.channels = dict(config['Channels']); self.log_message(f"Loaded {len(self.channels)} channels.")
            else: self.log_message("No [Channels] section."); self.channels = {}
        except Exception as e: self.log_message(f"Error loading config: {e}",True); wx.MessageBox(f"Lỗi đọc config:\n{e}","Lỗi",wx.OK|wx.ICON_ERROR); self.channels = DEFAULT_CHANNELS.copy()
    def save_config(self): # Giữ nguyên
        self.log_message(f"Saving config: {CONFIG_FILE}...")
        config = configparser.ConfigParser(); config['Channels'] = self.channels
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as cf: config.write(cf)
            self.log_message("Config saved.")
        except Exception as e: self.log_message(f"Error saving config: {e}",True); wx.MessageBox(f"Lỗi lưu config:\n{e}","Lỗi",wx.OK|wx.ICON_ERROR)
    def create_default_config(self): # Giữ nguyên
        self.channels = DEFAULT_CHANNELS.copy(); self.save_config()

    # --- Channel List Management (Giữ nguyên) ---
    def populate_channel_list(self): # Giữ nguyên
        self.channel_listbox.Clear();
        for name in self.channels.keys(): self.channel_listbox.Append(name)
        self.update_remove_button_state(None)
    def on_add_channel(self, event): # Giữ nguyên
        name_dlg = wx.TextEntryDialog(self,"Tên kênh:","Thêm Kênh","");
        if name_dlg.ShowModal()==wx.ID_OK:
            name=name_dlg.GetValue().strip();
            if not name: wx.MessageBox("Tên trống!","Lỗi",wx.OK|wx.ICON_ERROR); name_dlg.Destroy(); return
            if name in self.channels: wx.MessageBox("Tên đã tồn tại!","Lỗi",wx.OK|wx.ICON_ERROR); name_dlg.Destroy(); return
            url_dlg = wx.TextEntryDialog(self,f"URL stream cho '{name}':","Thêm Kênh","http://")
            if url_dlg.ShowModal()==wx.ID_OK:
                url=url_dlg.GetValue().strip()
                if not url.startswith("http"): wx.MessageBox("URL không hợp lệ!","Lỗi",wx.OK|wx.ICON_ERROR); url_dlg.Destroy(); name_dlg.Destroy(); return
                self.log_message(f"Adding: '{name}' - {url}"); self.channels[name]=url; self.populate_channel_list(); self.save_config()
            url_dlg.Destroy()
        name_dlg.Destroy()
    def on_remove_channel(self, event): # Giữ nguyên
        sel = self.channel_listbox.GetSelection();
        if sel == wx.NOT_FOUND: return
        name = self.channel_listbox.GetString(sel)
        if wx.MessageBox(f"Xóa kênh '{name}'?","Xác nhận",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)==wx.YES:
            self.log_message(f"Removing: '{name}'")
            if name in self.channels:
                if self.current_playing_url == self.channels[name]: self.stop_playback(force_destroy=True)
                del self.channels[name]; self.populate_channel_list(); self.save_config(); self.log_message("Removed.")
            else: self.log_message("Error: Channel not found.",True)
    def update_remove_button_state(self, event): # Giữ nguyên
        enable = self.channel_listbox.GetSelection() != wx.NOT_FOUND
        remove_btn = self.FindWindowById(ID_REMOVE_CHANNEL)
        if remove_btn: remove_btn.Enable(enable)
        if event: event.Skip()

    # --- Playback Control (Giữ nguyên) ---
    def on_channel_select(self, event): # Giữ nguyên
        sel = self.channel_listbox.GetSelection();
        if sel == wx.NOT_FOUND: return
        name = self.channel_listbox.GetString(sel)
        if name in self.channels:
            url = self.channels[name]; self.log_message(f"Selected: '{name}' ({url})")
            self.stop_playback(force_destroy=True) # Dừng và hủy player cũ
            self.show_player_area(True) # Hiện khu vực UI
            self.now_playing_text.SetLabelText(f"Đang kết nối: {name}...")
            self.reset_player_ui_without_hiding() # Reset nút
            self.panel.Layout() # Cập nhật layout
            self.current_playing_url = url
            if self._create_media_player_if_needed(): self.start_playback_thread(url, name) # Tạo player mới và bắt đầu tải
            else: self.playback_failed(name, "Không thể tạo player.")
        else: self.log_message(f"Error: URL not found for '{name}'",True)

    def show_player_area(self, show=True): # Giữ nguyên (đã sửa)
        if hasattr(self, 'player_area_sizer'):
            is_currently_shown = self.now_playing_text.IsShown()
            if is_currently_shown != show:
                self.log_message(f"Requesting player area {'show' if show else 'hide'}...")
                self.player_area_sizer.ShowItems(show)
                self.Layout() # Layout Frame
                self.log_message(f"Layout updated after player area {'show' if show else 'hide'}.")
        else: self.log_message("Error: player_area_sizer not found.", error=True)

    def start_playback_thread(self, url, name): # Giữ nguyên
        if not self.media_player: self.log_message("Player not ready.",True); self.playback_failed(name, "Player is None."); return
        self.SetStatusText(f"Đang tải '{name}'...")
        thread = threading.Thread(target=self._load_media, args=(url, name), name=f"Load-{name}"); thread.daemon=True; thread.start()

    def _load_media(self, url, name): # Giữ nguyên
        if not self.media_player: self.log_message("Thread: Player gone before Load()?", True); return # Kiểm tra lại player
        self.log_message(f"Thread: Loading URL: {url}")
        try:
            loaded = self.media_player.Load(url)
            if not loaded: self.log_message(f"Thread: Load() failed.",True); wx.CallAfter(self.playback_failed, name, "Load() returned false.")
            else: self.log_message(f"Thread: Load() OK, waiting...")
        except Exception as e: self.log_message(f"Thread: Load() exception: {e}",True); wx.CallAfter(self.playback_failed, name, f"Lỗi: {e}")

    def on_media_loaded(self, event): # Giữ nguyên
        if not self.media_player: return
        self.log_message("Event: Media Loaded.")
        current_label = self.now_playing_text.GetLabelText()
        name = current_label.replace("Đang kết nối: ","").replace("...","") if current_label.startswith("Đang kết nối:") else "Kênh"
        self.SetStatusText(f"Loaded '{name}', playing...")
        try:
            if self.media_player.Play():
                self.log_message("Media playing.")
                self.now_playing_text.SetLabelText(f"Đang phát: {name}")
                self.stop_button.Enable(); self.mute_button.Enable(); self.volume_slider.Enable()
                self.mute_button.SetValue(False); self.apply_volume()
            else: self.log_message("Play() failed after load.",True); self.playback_failed(name, "Không thể Play().")
        except Exception as e: self.log_message(f"Play() exception: {e}",True); self.playback_failed(name, f"Lỗi: {e}")

    def playback_failed(self, channel_name, reason): # Giữ nguyên
        self.log_message(f"Playback failed '{channel_name}': {reason}",True)
        self.SetStatusText(f"Lỗi phát '{channel_name}'!")
        self.now_playing_text.SetLabelText(f"Lỗi: {channel_name}")
        wx.MessageBox(f"Không phát được '{channel_name}'.\n{reason}","Lỗi",wx.OK|wx.ICON_ERROR)
        self.show_player_area(False) # Ẩn khi lỗi
        self.current_playing_url = None
        self._destroy_media_player() # Hủy luôn player

    def on_stop_playback(self, event): # Giữ nguyên
        self.log_message("Stop button clicked.")
        self.stop_playback(force_destroy=True)

    def stop_playback(self, force_destroy=False): # Giữ nguyên (đã sửa để hủy player)
        player_was_playing = False
        if self.media_player:
            player_was_playing = (self.media_player.GetState() != wx.media.MEDIASTATE_STOPPED)
            if player_was_playing:
                try: self.log_message("Calling Stop()..."); self.media_player.Stop(); self.log_message(f"State after Stop(): {self.media_player.GetState()}")
                except Exception as e: self.log_message(f"Error Stop(): {e}", error=True)
            if force_destroy or player_was_playing: self._destroy_media_player()
            else: self.log_message("Player already stopped, not destroying.")
        else: self.log_message("Stop called but no player exists.")
        self.stop_playback_ui()

    def stop_playback_ui(self): # Giữ nguyên
        self.log_message("Hiding player area.")
        self.show_player_area(False)
        self.SetStatusText("Sẵn sàng.")
        self.now_playing_text.SetLabelText("Chưa phát kênh nào.")
        self.current_playing_url = None

    def reset_player_ui_without_hiding(self): # Giữ nguyên
         self.log_message("Resetting player UI controls.")
         self.now_playing_text.SetLabelText("...")
         self.stop_button.Disable(); self.mute_button.Disable(); self.mute_button.SetValue(False); self.volume_slider.Disable(); self.volume_slider.SetValue(80)

    def on_media_stopped_or_finished(self, event): # Giữ nguyên
        self.log_message("Event: Media Stopped/Finished.")
        state = self.media_player.GetState() if self.media_player else wx.media.MEDIASTATE_STOPPED
        if state == wx.media.MEDIASTATE_STOPPED and self.media_player is not None and hasattr(self, 'player_area_sizer') and self.now_playing_text.IsShown():
             self.log_message("Media stopped unexpectedly, cleaning up.")
             self.stop_playback(force_destroy=True)
        event.Skip()

    # --- Mute/Volume (Giữ nguyên) ---
    def on_mute_toggle(self, event): # Giữ nguyên
        if not self.media_player: return
        is_muted = self.mute_button.GetValue()
        try:
             if is_muted: self.previous_volume = self.volume_slider.GetValue(); self.media_player.SetVolume(0.0); self.volume_slider.Disable(); self.log_message("Muted.")
             else: self.volume_slider.SetValue(self.previous_volume); self.apply_volume(); self.volume_slider.Enable(); self.log_message("Unmuted.")
        except Exception as e: self.log_message(f"Mute toggle error: {e}", error=True)
    def on_volume_change(self, event): # Giữ nguyên
        if not self.media_player or self.mute_button.GetValue(): return
        self.apply_volume()
    def apply_volume(self): # Giữ nguyên
        if not self.media_player: return
        vol = self.volume_slider.GetValue(); vol_f = vol / 100.0
        try:
            self.media_player.SetVolume(vol_f)
            if vol == 0 and not self.mute_button.GetValue(): self.mute_button.SetValue(True); self.volume_slider.Disable(); self.log_message("Muted (vol 0).")
        except Exception as e: self.log_message(f"Volume error: {e}",True)

# --- Chạy ứng dụng ---
if __name__ == '__main__':
    print("-" * 40); print("Khởi chạy Radio Online TE v1.7..."); print("-" * 40)
    app = wx.App(False)
    frame = RadioFrame(None, "Online Radio Technology Entertainment")
    if frame and frame.IsShown(): app.MainLoop()
    else: print("Lỗi khởi chạy GUI/Player.")
    print("-" * 40); print("Radio Online TE đã đóng."); print("-" * 40)