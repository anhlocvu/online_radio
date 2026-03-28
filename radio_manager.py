# -*- coding: utf-8 -*-

# Radio Config Manager
# Hỗ trợ tạo và quản lý file config.json cho Online Radio
# Coder: LCBoy - Lập trình viên mù 

import wx
import json
import os

CONFIG_FILE = "config.json"

class ManagerFrame(wx.Frame):
    def __init__(self, parent, title):
        super(ManagerFrame, self).__init__(parent, title=title, size=(600, 500))

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(30, 30, 30))
        self.panel.SetForegroundColour(wx.WHITE)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Danh sách ---
        self.listbox = wx.ListBox(self.panel, style=wx.LB_SINGLE)
        self.listbox.SetName("Danh sách kênh hiện có")
        self.listbox.SetBackgroundColour(wx.Colour(50, 50, 50))
        self.listbox.SetForegroundColour(wx.WHITE)
        main_sizer.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 10)

        # --- Ô nhập liệu ---
        input_grid = wx.FlexGridSizer(2, 2, 10, 10)
        input_grid.AddGrowableCol(1, 1)

        name_label = wx.StaticText(self.panel, label="Tên kênh:")
        self.name_input = wx.TextCtrl(self.panel)
        self.name_input.SetName("Ô nhập tên kênh")

        url_label = wx.StaticText(self.panel, label="URL luồng:")
        self.url_input = wx.TextCtrl(self.panel)
        self.url_input.SetName("Ô nhập địa chỉ URL luồng")

        input_grid.Add(name_label, 0, wx.ALIGN_CENTER_VERTICAL)
        input_grid.Add(self.name_input, 1, wx.EXPAND)
        input_grid.Add(url_label, 0, wx.ALIGN_CENTER_VERTICAL)
        input_grid.Add(self.url_input, 1, wx.EXPAND)

        main_sizer.Add(input_grid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        # --- Nút điều khiển ---
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.add_btn = wx.Button(self.panel, label="&Thêm mới")
        self.add_btn.SetName("Thêm kênh mới vào danh sách tạm")
        
        self.update_btn = wx.Button(self.panel, label="&Cập nhật")
        self.update_btn.SetName("Cập nhật thông tin cho kênh đang chọn")
        
        self.delete_btn = wx.Button(self.panel, label="&Xóa")
        self.delete_btn.SetName("Xóa kênh đang chọn khỏi danh sách")
        
        self.save_btn = wx.Button(self.panel, label="&Lưu file JSON")
        self.save_btn.SetName("Lưu tất cả thay đổi vào file config.json")
        self.save_btn.SetBackgroundColour(wx.Colour(0, 128, 0))
        self.save_btn.SetForegroundColour(wx.WHITE)

        btn_sizer.Add(self.add_btn, 1, wx.RIGHT, 5)
        btn_sizer.Add(self.update_btn, 1, wx.RIGHT, 5)
        btn_sizer.Add(self.delete_btn, 1, wx.RIGHT, 5)
        btn_sizer.Add(self.save_btn, 1)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        self.panel.SetSizer(main_sizer)

        # ----- Data -----
        self.channels = {}
        self.load_local_json()

        # ----- Events -----
        self.Bind(wx.EVT_LISTBOX, self.on_select, self.listbox)
        self.Bind(wx.EVT_BUTTON, self.on_add, self.add_btn)
        self.Bind(wx.EVT_BUTTON, self.on_update, self.update_btn)
        self.Bind(wx.EVT_BUTTON, self.on_delete, self.delete_btn)
        self.Bind(wx.EVT_BUTTON, self.on_save, self.save_btn)

        self.Centre()
        self.Show()
        self.listbox.SetFocus()

    def load_local_json(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.channels = data.get("Channels", {})
                    self.refresh_list()
            except Exception as e:
                wx.MessageBox(f"Lỗi đọc file: {e}", "Lỗi", wx.ICON_ERROR)

    def refresh_list(self):
        self.listbox.Clear()
        for name in sorted(self.channels.keys()):
            self.listbox.Append(name)

    def on_select(self, event):
        sel = self.listbox.GetSelection()
        if sel != wx.NOT_FOUND:
            name = self.listbox.GetString(sel)
            self.name_input.SetValue(name)
            self.url_input.SetValue(self.channels[name])

    def on_add(self, event):
        name = self.name_input.GetValue().strip()
        url = self.url_input.GetValue().strip()
        if not name or not url:
            wx.MessageBox("Vui lòng nhập đủ Tên và URL!", "Thông báo")
            return
        self.channels[name] = url
        self.refresh_list()
        self.name_input.Clear(); self.url_input.Clear()
        wx.LogStatus(f"Đã thêm tạm thời: {name}")

    def on_update(self, event):
        sel = self.listbox.GetSelection()
        if sel == wx.NOT_FOUND: return
        
        old_name = self.listbox.GetString(sel)
        new_name = self.name_input.GetValue().strip()
        new_url = self.url_input.GetValue().strip()
        
        if not new_name or not new_url: return
        
        if old_name != new_name:
            del self.channels[old_name]
        
        self.channels[new_name] = new_url
        self.refresh_list()
        wx.LogStatus(f"Đã cập nhật: {new_name}")

    def on_delete(self, event):
        sel = self.listbox.GetSelection()
        if sel == wx.NOT_FOUND: return
        name = self.listbox.GetString(sel)
        if wx.MessageBox(f"Xóa kênh '{name}'?", "Xác nhận", wx.YES_NO) == wx.YES:
            del self.channels[name]
            self.refresh_list()
            self.name_input.Clear(); self.url_input.Clear()
            wx.LogStatus(f"Đã xóa: {name}")

    def on_save(self, event):
        data = {"Channels": self.channels}
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            wx.MessageBox("Đã lưu file config.json thành công!\nBây giờ bạn có thể upload file này lên web server.", "Thành công")
        except Exception as e:
            wx.MessageBox(f"Lỗi lưu file: {e}", "Lỗi", wx.ICON_ERROR)

if __name__ == '__main__':
    app = wx.App(False)
    ManagerFrame(None, "Quản lý Cấu hình Radio Online")
    app.MainLoop()
