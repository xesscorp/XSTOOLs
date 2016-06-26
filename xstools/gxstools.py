#!/usr/bin/python
# -*- coding: utf-8 -*-

# **********************************************************************
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
#   02111-1307, USA.
#
#   (c)2012 - X Engineering Software Systems Corp. (www.xess.com)
# **********************************************************************

# Python2 compatibility through future package
from builtins import super

import os
from threading import Thread


import wx
import wx.html
import wx.lib
import wx.lib.agw.flatnotebook as fnb
import wx.lib.filebrowsebutton as fbb
import wx.lib.platebtn as pbtn
from pubsub import pub
from wx.lib import intctrl

from xstools import __version__, install_dir
from xstools import xsboard, xserror, xsusb

# ********************* Globals ***********************************
ACTIVE_BOARD = None
PORT_THREAD = None


# ===============================================================
# Utility routines for connecting and disconnecting the USB port.
# ===============================================================


def disconnect():
    if ACTIVE_BOARD is not None:
        ACTIVE_BOARD.xsusb.disconnect()


def reconnect():
    global ACTIVE_BOARD
    if ACTIVE_BOARD is not None:
        ACTIVE_BOARD = xsboard.XsBoard.get_xsboard(ACTIVE_BOARD.xsusb._xsusb_id)


def _path(fn):
    return os.path.join(install_dir, 'icons', fn)


def _bitmap(fn):
    # This stops warnings about the color profile of the PNG files.
    stop_logging = wx.LogNull()
    bm = wx.Bitmap(_path(fn), wx.BITMAP_TYPE_PNG)
    del stop_logging
    return bm


# ===============================================================
# GXSTOOLs About Box.
# ===============================================================


class GxsHtmlWindow(wx.html.HtmlWindow):
    def __init__(self, parent, id, size=(600, 400), ):
        super(GxsHtmlWindow, self).__init__(parent, id, size=size)
        if 'gtk2' in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())


class GxsAboutBox(wx.Dialog):
    def __init__(self):
        style = wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.TAB_TRAVERSAL
        super(GxsAboutBox, self).__init__(None, -1, 'About GXSTOOLs', style=style)
        hwin = GxsHtmlWindow(self, -1, size=(400, 200))
        about_text = """<p>Graphical XSTOOLs Utilities Version %s</p>"""
        hwin.SetPage(about_text % __version__)
        irep = hwin.GetInternalRepresentation()
        hwin.SetSize((irep.GetWidth() + 25, irep.GetHeight() + 10))
        self.SetClientSize(hwin.GetSize())
        self.CentreOnParent(wx.BOTH)
        self.SetFocus()


# ===============================================================
# Continually running timer that triggers periodic events.
# ===============================================================

class GxsTimer(wx.Timer):
    def __init__(self, *args, **kwargs):
        super(GxsTimer, self).__init__(*args, **kwargs)
        pub.subscribe(self.start, "Timer.Start")
        pub.subscribe(self.stop, "Timer.Stop")
        pub.sendMessage("Timer.Start")
        self.Start(milliseconds=100, oneShot=False)

    def start(self):
        self.Start(milliseconds=100, oneShot=False)

    def stop(self):
        self.Stop()

    def Notify(self):
        pub.sendMessage("Port.Check", force_check=False)
        pub.sendMessage("Progress.Pulse")


# ===============================================================
# Status bar.
# ===============================================================

class GxsStatusBar(wx.StatusBar):
    fields = ("Port", "Board",)

    def __init__(self, *args, **kwargs):
        super(GxsStatusBar, self).__init__(*args, **kwargs)
        self.SetFieldsCount(len(self.fields))
        pub.subscribe(self.on_port_change, "Status.Port")
        pub.subscribe(self.on_board_change, "Status.Board")

    def on_port_change(self, port):
        self.change_status_bar(self.fields[0], port)

    def on_board_change(self, board):
        self.change_status_bar(self.fields[1], board)

    def change_status_bar(self, label, value):
        self.SetStatusText("%s: %s" % (label, value), self.fields.index(label))


# ===============================================================
# Progress dialog for long-running stuff.
# ===============================================================

class GxsProgressDialog(wx.ProgressDialog):
    def __init__(self, *args, **kwargs):
        self._value = 0
        if 'style' not in kwargs:
            kwargs['style'] = wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE | wx.PD_SMOOTH
        if 'message' not in kwargs:
            # This sets the width of the progress window.
            kwargs['message'] = " " * 80
        if 'maximum' not in kwargs:
            kwargs['maximum'] = 100
        pub.subscribe(self.on_phase_change, "Progress.Phase")
        pub.subscribe(self.on_progress_change, "Progress.Pct")
        pub.subscribe(self.on_pulse, "Progress.Pulse")
        super(GxsProgressDialog, self).__init__(*args, **kwargs)

    def Destroy(self, *args, **kwargs):
        pub.unsubscribe(self.on_phase_change, "Progress.Phase")
        pub.unsubscribe(self.on_progress_change, "Progress.Pct")
        pub.unsubscribe(self.on_pulse, "Progress.Pulse")
        wx.ProgressDialog.Destroy(self)

    def on_phase_change(self, phase):
        if not self.Update(value=self._value, newmsg=phase)[0]:
            self.close()

    def on_progress_change(self, value):
        self._value = value  # msg
        if not self.Update(value=value)[0]:
            self.close()

    def on_pulse(self):
        if not self.Pulse()[0]:
            self.close()

    def close(self):
        ACTIVE_BOARD.xsusb.terminate = True
        self.Destroy()


# ===============================================================
# File browser that maintains its history.
# ===============================================================

class DnDFilePickerCtrl(fbb.FileBrowseButtonWithHistory, wx.FileDropTarget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.SetDropTarget(self)
        # Show '+' icon when hovering over this field.
        # self.SetDefaultAction(wx.DragCopy)

    def GetPath(self, add_to_history=False):
        current_value = self.GetValue()
        if add_to_history:
            self.AddToHistory(current_value)
        return current_value

    def AddToHistory(self, value):
        if value == u'':
            return
        if type(value) == str:
            history = self.GetHistory()
            history.insert(0, value)
            history = tuple(set(history))
            self.SetHistory(history, 0)
            self.SetValue(value)
        elif type(value) in (list, tuple):
            for v in value:
                self.AddToHistory(v)

    def SetPath(self, path):
        self.AddToHistory(path)
        self.SetValue(path)

    def OnChanged(self, evt):
        event = wx.PyCommandEvent(wx.EVT_FILEPICKER_CHANGED.typeId, self.GetId())
        wx.PostEvent(self, event)

    def OnDropFiles(self, x, y, filenames):
        self.AddToHistory(filenames)
        event = wx.PyCommandEvent(wx.EVT_FILEPICKER_CHANGED.typeId, self.GetId())
        wx.PostEvent(self, event)


# ===============================================================
# Port setup panel.
# ===============================================================

class GxsPortPanel(wx.Panel):
    active_port_id = None

    def __init__(self, *args, **kwargs):
        super(GxsPortPanel, self).__init__(*args, **kwargs)

        global ACTIVE_BOARD
        ACTIVE_BOARD = None

        self.SetToolTip('Use this tab to select the port your XESS board is '
                        'attached to.')

        self._port_list = wx.Choice(self)
        self._port_list.SetToolTip('Select a port with an attached XESS board')
        self._port_list.Bind(wx.EVT_CHOICE, self.on_port_change)

        self._blink_button = wx.Button(self, label='Blink')
        self._blink_button.SetToolTip('Click to blink LED on the board '
                                      'attached to the selected port')
        self._blink_button.Bind(wx.EVT_BUTTON, self.on_blink)
        self._blink_button.Disable()

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)
        hsizer.Add(wx.StaticText(self, label='Port: '), 0,
                   wx.ALIGN_CENTER_VERTICAL)
        hsizer.Add(self._port_list, 0, wx.ALIGN_CENTER_VERTICAL)
        hsizer.AddSpacer(5)
        hsizer.Add(self._blink_button, 0, wx.ALIGN_CENTER_VERTICAL)
        hsizer.AddSpacer(5)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(hsizer)
        vsizer.AddSpacer(5)

        self.SetSizer(vsizer)

        pub.subscribe(self.check_port_connections, "Port.Check")

    def check_port_connections(self, force_check):
        """Handles connections/disconnections of boards to/from USB ports"""

        # Only check the USB port if no child thread is using it.
        global PORT_THREAD
        if PORT_THREAD is not None:
            if PORT_THREAD.is_alive() is False:
                PORT_THREAD = None
                force_check = True
        if PORT_THREAD is not None:
            return

        global ACTIVE_BOARD

        xsusb_ports = xsusb.XsUsb.get_xsusb_ports()
        num_boards = len(xsusb_ports)
        # print "# boards = %d" % num_boards

        if num_boards != self._port_list.GetCount() or force_check:
            # A board has been connected or disconnected from a USB port, or a
            # check of connected boards is being forced to occur.
            if num_boards == 0:
                # print "active board = ", str(active_board)
                # if active_board is not None:
                # active_board.xsusb.disconnect()
                self._port_list.Clear()
                if ACTIVE_BOARD is not None:
                    ACTIVE_BOARD = None
                event = wx.PyCommandEvent(wx.EVT_CHOICE.typeId, wx.ID_ANY)
                wx.PostEvent(self._port_list, event)
            else:
                self._port_list.Clear()
                for i in range(0, num_boards):
                    self._port_list.Append('USB%d' % i)
                if ACTIVE_BOARD is None:
                    # The active board must have been disconnected, so make the
                    # first remaining board in the list active.
                    self._port_list.SetSelection(0)
                else:
                    xsusb_id = ACTIVE_BOARD.get_xsusb_id()
                    if xsusb_id is None:
                        self._port_list.SetSelection(0)
                    else:
                        self._port_list.SetSelection(xsusb_id)
                ACTIVE_BOARD = xsboard.XsBoard.get_xsboard(
                    self._port_list.GetSelection())
                event = wx.PyCommandEvent(wx.EVT_CHOICE.typeId, wx.ID_ANY)
                wx.PostEvent(self._port_list, event)
                disconnect()

    def on_port_change(self, event):

        # Only check the USB port if no child thread is using it.
        global PORT_THREAD
        if PORT_THREAD is not None:
            if PORT_THREAD.is_alive() is False:
                PORT_THREAD = None
        if PORT_THREAD is not None:
            return

        global ACTIVE_BOARD

        port_id = self._port_list.GetSelection()
        if port_id == wx.NOT_FOUND:
            GxsPortPanel.active_port_id = None
            active_port_name = ''
        else:
            GxsPortPanel.active_port_id = port_id
            active_port_name = 'USB%d' % GxsPortPanel.active_port_id
        ACTIVE_BOARD = xsboard.XsBoard.get_xsboard(GxsPortPanel.active_port_id)
        active_board_name = getattr(ACTIVE_BOARD, 'name', '')
        if hasattr(ACTIVE_BOARD, 'micro'):
            self._blink_button.Enable()
        else:
            self._blink_button.Disable()
        pub.sendMessage("Status.Port", port=active_port_name)
        pub.sendMessage("Status.Board", board=active_board_name)
        pub.sendMessage('Status.Change', dummy=None)
        disconnect()

    def on_blink(self, event):
        reconnect()
        port_id = self._port_list.GetSelection()
        if port_id != wx.NOT_FOUND:
            ACTIVE_BOARD.get_board_info()
        disconnect()


# ===============================================================
# Flash upload/download panel.
# ===============================================================

class GxsFlashPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(GxsFlashPanel, self).__init__(*args, **kwargs)

        mem_type = 'Flash'

        self.SetToolTip(
            'Use this tab to transfer data to/from the %s on your XESS board.' % mem_type)

        file_wildcard = 'Xilinx bitstream (*.bit)|*.bit|Intel Hex (*.hex)|*.hex'

        # self._dnld_file_picker = DnDFilePickerCtrl(self, wildcard=file_wildcard,
        # style=wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST | wx.FLP_USE_TEXTCTRL | wx.FLP_SMALL)
        # self._dnld_file_picker.SetToolTip('File to download to %s' % mem_type)
        kwargs = dict(parent=self, labelText='', buttonText='Browse', fileMask=file_wildcard)
        # Download file picker
        down_kwargs = kwargs.copy()
        down_kwargs['toolTip'] = 'File to download to %s' % mem_type
        down_kwargs['dialogTitle'] = 'Select file to download to %s' % mem_type
        down_kwargs['fileMode'] = wx.FD_OPEN
        self._dnld_file_picker = DnDFilePickerCtrl(**down_kwargs)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.handle_download_button, self._dnld_file_picker)
        # Upload file picker
        up_kwargs = kwargs.copy()
        up_kwargs['toolTip'] = 'File to upload from %s' % mem_type
        up_kwargs['dialogTitle'] = 'Select file to store %s contents' % mem_type
        up_kwargs['fileMode'] = wx.FD_SAVE
        self._upld_file_picker = DnDFilePickerCtrl(**up_kwargs)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.handle_upload_button, self._upld_file_picker)

        down_arrow_bmp = _bitmap('down_arrow.png')
        down_arrow_disabled_bmp = _bitmap('down_arrow_disabled.png')

        self._dnld_button = pbtn.PlateButton(self)
        self._dnld_button.SetBitmap(down_arrow_bmp)
        self._dnld_button.SetBitmapDisabled(down_arrow_disabled_bmp)
        self._dnld_button.SetToolTip('Start download to %s' % mem_type)
        self.Bind(wx.EVT_BUTTON, self.on_download, self._dnld_button)
        pub.subscribe(self.handle_download_button, 'Status.Change')
        self.handle_download_button(dummy=None)

        self._upld_button = pbtn.PlateButton(self)
        self._upld_button.SetBitmap(down_arrow_bmp)
        self._upld_button.SetBitmapDisabled(down_arrow_disabled_bmp)
        self._upld_button.SetToolTip('Start upload from %s' % mem_type)
        self.Bind(wx.EVT_BUTTON, self.on_upload, self._upld_button)
        pub.subscribe(self.handle_upload_button, 'Status.Change')
        self.handle_upload_button(dummy=None)

        self._erase_button = wx.Button(self, label='Erase')
        self._erase_button.SetToolTip(
            'Click to erase %s between the upper and lower addresses' % mem_type)
        self._erase_button.Bind(wx.EVT_BUTTON, self.on_erase)
        pub.subscribe(self.handle_erase_button, 'Status.Change')
        self.handle_erase_button(dummy=None)

        self._hi_addr_ctrl = intctrl.IntCtrl(self)
        self._hi_addr_ctrl.SetToolTip('Enter upper %s address here' % mem_type)
        self._lo_addr_ctrl = intctrl.IntCtrl(self)
        self._lo_addr_ctrl.SetToolTip('Enter lower %s address here' % mem_type)

        addr_vsizer = wx.BoxSizer(wx.VERTICAL)
        addr_vsizer.Add(self._hi_addr_ctrl)
        addr_vsizer.Add(wx.StaticText(self, label='Upper Address'), 0,
                        wx.CENTER)
        addr_vsizer.AddStretchSpacer()
        addr_vsizer.AddSpacer(10)
        addr_vsizer.Add(self._erase_button)
        addr_vsizer.AddSpacer(10)
        addr_vsizer.AddStretchSpacer()
        addr_vsizer.Add(wx.StaticText(self, label='Lower Address'), 0,
                        wx.CENTER)
        addr_vsizer.Add(self._lo_addr_ctrl)

        flash_bmp = _bitmap('serial_flash.png')
        flash_stbmp = wx.StaticBitmap(self, label=flash_bmp)

        chip_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        chip_hsizer.Add(flash_stbmp)
        chip_hsizer.AddSpacer(5)
        chip_hsizer.Add(addr_vsizer, 1, wx.ALIGN_CENTER)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(self._dnld_file_picker, 0, wx.EXPAND)
        vsizer.Add(self._dnld_button, 0, wx.ALIGN_CENTER)
        vsizer.Add(chip_hsizer, 0, wx.ALIGN_CENTER)
        vsizer.Add(self._upld_button, 0, wx.ALIGN_CENTER)
        vsizer.Add(self._upld_file_picker, 0, wx.EXPAND)
        vsizer.AddSpacer(5)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)
        chip_hsizer.Hide(addr_vsizer)
        hsizer.Add(vsizer, 1, wx.GROW)
        chip_hsizer.Show(addr_vsizer)
        hsizer.AddSpacer(5)

        self.SetSizer(hsizer)

    def handle_download_button(self, dummy):
        if self._dnld_file_picker.GetPath() and hasattr(ACTIVE_BOARD,
                                                        'cfg_flash'):
            self._dnld_button.Enable()
        else:
            self._dnld_button.Disable()

    def on_download(self, event):
        pub.subscribe(self.cleanup, "Flash.Cleanup")
        self._progress = GxsProgressDialog(title="Downloading to Flash",
                                           parent=self)
        GxsFlashDownloadThread(
            self._dnld_file_picker.GetPath(add_to_history=True))

    def set_upload_file(self, event):
        if event.GetEventObject().GetPath():
            self._upld_button.Enable()
        else:
            self._upld_button.Disable()

    def handle_upload_button(self, dummy):
        if self._upld_file_picker.GetPath() and hasattr(ACTIVE_BOARD,
                                                        'cfg_flash'):
            self._upld_button.Enable()
        else:
            self._upld_button.Disable()

    def on_upload(self, event):
        pub.subscribe(self.cleanup, "Flash.Cleanup")
        self._progress = GxsProgressDialog(title="Uploading from Flash",
                                           parent=self)
        GxsFlashUploadThread(self._upld_file_picker.GetPath(add_to_history=True),
                             self._lo_addr_ctrl.GetValue(),
                             self._hi_addr_ctrl.GetValue())

    def handle_erase_button(self, dummy):
        if hasattr(ACTIVE_BOARD, 'cfg_flash'):
            self._erase_button.Enable()
        else:
            self._erase_button.Disable()

    def on_erase(self, event):
        pub.subscribe(self.cleanup, "Flash.Cleanup")
        self._progress = GxsProgressDialog(title="Erasing Flash", parent=self)
        GxsFlashEraseThread(self._lo_addr_ctrl.GetValue(),
                            self._hi_addr_ctrl.GetValue())

    def cleanup(self):
        pub.unsubscribe(self.cleanup, "Flash.Cleanup")
        self._progress.Destroy()


# ===============================================================
# Thread for running Flash download operation.
# ===============================================================

class GxsFlashDownloadThread(Thread):
    def __init__(self, dnld_file):
        Thread.__init__(self)
        self._dnld_file = dnld_file
        self.start()

    def run(self):
        msg_box_title = 'Flash Download Result'
        try:
            reconnect()
            ACTIVE_BOARD.write_cfg_flash(self._dnld_file)
            wx.MessageBox('Success!', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate:
            wx.MessageBox('Cancelled.', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            pub.sendMessage('Flash.Cleanup')
            disconnect()


# ===============================================================
# Thread for running Flash upload operation.
# ===============================================================
class GxsFlashUploadThread(Thread):
    def __init__(self, upld_file, low_addr, high_addr):
        Thread.__init__(self)
        self._upld_file = upld_file
        self._low_addr = low_addr
        self._high_addr = high_addr
        self.start()

    def run(self):
        msg_box_title = 'Flash Upload Result'
        try:
            reconnect()
            ACTIVE_BOARD.read_cfg_flash(self._low_addr, self._high_addr).tofile(
                self._upld_file, format='hex')
            wx.MessageBox('Success!', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate as e:
            wx.MessageBox('Cancelled.', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            pub.sendMessage("Flash.Cleanup")
            disconnect()


# ===============================================================
# Thread for running Flash erase operation.
# ===============================================================
class GxsFlashEraseThread(Thread):
    def __init__(self, low_addr, high_addr):
        Thread.__init__(self)
        self._low_addr = low_addr
        self._high_addr = high_addr
        self.start()

    def run(self):
        msg_box_title = 'Flash Erase Result'
        try:
            reconnect()
            ACTIVE_BOARD.erase_cfg_flash(self._low_addr, self._high_addr)
            wx.MessageBox('Success!', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate as e:
            wx.MessageBox('Cancelled.', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            pub.sendMessage("Flash.Cleanup")
            disconnect()


# ===============================================================
# SDRAM upload/download panel.
# ===============================================================

class GxsSdramPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(GxsSdramPanel, self).__init__(*args, **kwargs)

        mem_type = 'SDRAM'

        tt_fmt = 'Use this tab to transfer data to/from the %s on your XESS board.'
        self.SetToolTip(tt_fmt % mem_type)

        # file_wildcard = 'Intel Hex (*.hex)|*.hex|Motorola EXO (*.exo)|*.exo|XESS (*.xes)|*.xes'
        file_wildcard = 'Intel Hex (*.hex)|*.hex'
        kwargs = dict(parent=self, labelText='', buttonText='Browse', fileMask=file_wildcard)
        # Download file picker
        down_kwargs = kwargs.copy()
        down_kwargs['toolTip'] = 'File to download to %s' % mem_type
        down_kwargs['dialogTitle'] = 'Select file to download to %s' % mem_type
        down_kwargs['fileMode'] = wx.FD_OPEN
        self._dnld_file_picker = DnDFilePickerCtrl(**down_kwargs)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.handle_download_button,
                  self._dnld_file_picker)
        # Upload file picker
        up_kwargs = kwargs.copy()
        up_kwargs['toolTip'] = 'File to upload from %s' % mem_type
        up_kwargs['dialogTitle'] = 'Select file to store %s contents' % mem_type
        up_kwargs['fileMode'] = wx.FD_SAVE
        self._upld_file_picker = DnDFilePickerCtrl(**up_kwargs)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.handle_upload_button,
                  self._upld_file_picker)

        down_arrow_bmp = _bitmap('down_arrow.png')
        down_arrow_disabled_bmp = _bitmap('down_arrow_disabled.png')

        self._dnld_button = pbtn.PlateButton(self)
        self._dnld_button.SetBitmap(down_arrow_bmp)
        self._dnld_button.SetBitmapDisabled(down_arrow_disabled_bmp)
        self._dnld_button.SetToolTip('Start download to %s' % mem_type)
        self.Bind(wx.EVT_BUTTON, self.on_download, self._dnld_button)
        pub.subscribe(self.handle_download_button, 'Status.Change')
        self.handle_download_button(dummy=None)

        self._upld_button = pbtn.PlateButton(self)
        self._upld_button.SetBitmap(down_arrow_bmp)
        self._upld_button.SetBitmapDisabled(down_arrow_disabled_bmp)
        self._upld_button.SetToolTip('Start upload from %s' % mem_type)
        self.Bind(wx.EVT_BUTTON, self.on_upload, self._upld_button)
        pub.subscribe(self.handle_upload_button, 'Status.Change')
        self.handle_upload_button(dummy=None)

        self._hi_addr_ctrl = intctrl.IntCtrl(self)
        self._hi_addr_ctrl.SetToolTip(
            'Enter upper %s address here' % mem_type)
        self._lo_addr_ctrl = intctrl.IntCtrl(self)
        self._lo_addr_ctrl.SetToolTip(
            'Enter lower %s address here' % mem_type)

        addr_vsizer = wx.BoxSizer(wx.VERTICAL)
        addr_vsizer.Add(self._hi_addr_ctrl)
        addr_vsizer.Add(wx.StaticText(self, label='Upper Address'), 0,
                        wx.CENTER)
        addr_vsizer.AddStretchSpacer()
        addr_vsizer.Add(wx.StaticText(self, label='Lower Address'), 0,
                        wx.CENTER)
        addr_vsizer.Add(self._lo_addr_ctrl)

        sdram_bmp = _bitmap('sdram.png')
        sdram_stbmp = wx.StaticBitmap(self, label=sdram_bmp)

        chip_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        chip_hsizer.Add(sdram_stbmp)
        chip_hsizer.AddSpacer(5)
        chip_hsizer.Add(addr_vsizer, 1, wx.GROW)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(self._dnld_file_picker, 0, wx.EXPAND)
        vsizer.Add(self._dnld_button, 0, wx.ALIGN_CENTER)
        vsizer.Add(chip_hsizer, 0, wx.ALIGN_CENTER)
        vsizer.Add(self._upld_button, 0, wx.ALIGN_CENTER)
        vsizer.Add(self._upld_file_picker, 0, wx.EXPAND)
        vsizer.AddSpacer(5)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)
        chip_hsizer.Hide(addr_vsizer)
        hsizer.Add(vsizer, 1, wx.GROW)
        chip_hsizer.Show(addr_vsizer)
        hsizer.AddSpacer(5)

        self.SetSizer(hsizer)

    def handle_download_button(self, dummy):
        if self._dnld_file_picker.GetPath() and hasattr(ACTIVE_BOARD, 'sdram'):
            self._dnld_button.Enable()
        else:
            self._dnld_button.Disable()

    def on_download(self, event):
        pub.subscribe(self.cleanup, "Sdram.Cleanup")
        self._progress = GxsProgressDialog(title='Downloading to SDRAM',
                                           parent=self)
        GxsSdramDownloadThread(
            self._dnld_file_picker.GetPath(add_to_history=True))

    def handle_upload_button(self, dummy):
        if self._upld_file_picker.GetPath() and hasattr(ACTIVE_BOARD, 'sdram'):
            self._upld_button.Enable()
        else:
            self._upld_button.Disable()

    def on_upload(self, event):
        pub.subscribe(self.cleanup, "Sdram.Cleanup")
        self._progress = GxsProgressDialog(title="Uploading from SDRAM",
                                           parent=self)
        GxsSdramUploadThread(self._upld_file_picker.GetPath(add_to_history=True),
                             self._lo_addr_ctrl.GetValue(),
                             self._hi_addr_ctrl.GetValue())

    def handle_erase_button(self, dummy):
        if hasattr(ACTIVE_BOARD, 'sdram'):
            self._erase_button.Enable()
        else:
            self._erase_button.Disable()

    def on_erase(self, event):
        pub.subscribe(self.cleanup, "Sdram.Cleanup")
        self._progress = GxsProgressDialog(title="Erasing SDRAM", parent=self)
        GxsSdramEraseThread(self._lo_addr_ctrl.GetValue(),
                            self._hi_addr_ctrl.GetValue())

    def cleanup(self):
        pub.unsubscribe(self.cleanup, "Sdram.Cleanup")
        self._progress.Destroy()


# ===============================================================
# Thread for running SDRAM download operation.
# ===============================================================
class GxsSdramDownloadThread(Thread):
    def __init__(self, dnld_file):
        Thread.__init__(self)
        self._dnld_file = dnld_file
        self.start()

    def run(self):
        msg_box_title = 'SDRAM Download Result'
        try:
            reconnect()
            ACTIVE_BOARD.write_sdram(self._dnld_file)
            wx.MessageBox('Success!', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate as e:
            wx.MessageBox('Cancelled.', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            pub.sendMessage("Sdram.Cleanup")
            disconnect()


# ===============================================================
# Thread for running SDRAM upload operation.
# ===============================================================
class GxsSdramUploadThread(Thread):
    def __init__(self, upld_file, low_addr, high_addr):
        Thread.__init__(self)
        self._upld_file = upld_file
        self._low_addr = low_addr
        self._high_addr = high_addr
        self.start()

    def run(self):
        msg_box_title = 'SDRAM Upload Result'
        try:
            reconnect()
            ACTIVE_BOARD.read_sdram(self._low_addr, self._high_addr).tofile(
                self._upld_file, format='hex')
            wx.MessageBox('Success!', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate as e:
            wx.MessageBox('Cancelled.', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            pub.sendMessage("Sdram.Cleanup")
            disconnect()


# ===============================================================
# Thread for running SDRAM erase operation.
# ===============================================================
class GxsSdramEraseThread(Thread):
    def __init__(self, low_addr, high_addr):
        Thread.__init__(self)
        self._low_addr = low_addr
        self._high_addr = high_addr
        self.start()

    def run(self):
        msg_box_title = 'SDRAM Erase Result'
        try:
            reconnect()
            ACTIVE_BOARD.erase_sdram(self._low_addr, self._high_addr)
            wx.MessageBox('Success!', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate as e:
            wx.MessageBox('Cancelled.', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            pub.sendMessage("Sdram.Cleanup")
            disconnect()


# ===============================================================
# FPGA configuration panel.
# ===============================================================

class GxsFpgaConfigPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(GxsFpgaConfigPanel, self).__init__(*args, **kwargs)

        self.SetToolTip('Use this tab to download bitstreams to the FPGA on '
                        'your XESS board.')

        file_wildcard = 'Xilinx bitstreams (*.bit)|*.bit'

        kwargs = dict(parent=self,
                      labelText='',
                      buttonText='Browse',
                      toolTip='Bitstream file to download to FPGA',
                      dialogTitle='Select bitstream file to download to FPGA',
                      fileMask=file_wildcard,
                      fileMode=wx.FD_OPEN)
        self._dnld_file_picker = DnDFilePickerCtrl(**kwargs)
        self.Bind(wx.EVT_FILEPICKER_CHANGED,
                  self.handle_download_button,
                  self._dnld_file_picker)

        down_arrow_bmp = _bitmap('down_arrow.png')
        down_arrow_disabled_bmp = _bitmap('down_arrow_disabled.png')

        self._dnld_button = pbtn.PlateButton(self)
        self._dnld_button.SetBitmap(down_arrow_bmp)
        self._dnld_button.SetBitmapDisabled(down_arrow_disabled_bmp)
        self._dnld_button.SetToolTip('Start download to FPGA')
        self._dnld_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.on_download, self._dnld_button)
        pub.subscribe(self.handle_download_button, 'Status.Change')
        self.handle_download_button(dummy=None)

        fpga_bmp = _bitmap('fpga.png')
        fpga_stbmp = wx.StaticBitmap(self, label=fpga_bmp)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(self._dnld_file_picker, 0, wx.EXPAND)
        vsizer.Add(self._dnld_button, 0, wx.ALIGN_CENTER)
        vsizer.Add(fpga_stbmp, 0, wx.ALIGN_CENTER)
        vsizer.AddSpacer(5)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)
        hsizer.Add(vsizer, 1, wx.GROW)
        hsizer.AddSpacer(5)

        self.SetSizer(hsizer)

    def handle_download_button(self, dummy):
        # if self._dnld_file_picker.GetPath() and hasattr(active_board, 'fpga'):
        #     self._dnld_button.Enable()
        # else:
        self._dnld_button.Disable()

    def on_download(self, event):
        pub.subscribe(self.cleanup, 'Fpga.Cleanup')
        self._download_progress = GxsProgressDialog(
            title="Download Bitstream to FPGA", parent=self)
        GxsFpgaDownloadThread(self._dnld_file_picker.GetPath(add_to_history=True))

    def cleanup(self):
        pub.unsubscribe(self.cleanup, 'Fpga.Cleanup')
        self._download_progress.Destroy()


# ===============================================================
# Thread for running FPGA configuration.
# ===============================================================
class GxsFpgaDownloadThread(Thread):
    def __init__(self, config_file):
        Thread.__init__(self)
        self._config_file = config_file
        self.start()

    def run(self):
        msg_box_title = 'FPGA Bitstream Download Result'
        try:
            reconnect()
            ACTIVE_BOARD.configure(self._config_file)
            wx.MessageBox('Success!', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate:
            wx.MessageBox('Cancelled.', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            pub.sendMessage('Fpga.Cleanup')
            disconnect()


# ===============================================================
# Microcontroller panel.
# ===============================================================


class GxsMicrocontrollerPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(GxsMicrocontrollerPanel, self).__init__(*args, **kwargs)

        self.SetToolTip('Use this tab to download new firmware to the '
                        'microcontroller flash on your XESS board.')

        file_wildcard = 'object file (*.hex)|*.hex'

        kwargs = dict(parent=self,
                      labelText='',
                      buttonText='Browse',
                      toolTip='Hex object file to download to microcontroller',
                      dialogTitle='Select hex object file to download to microcontroller',
                      fileMask=file_wildcard,
                      fileMode=wx.FD_OPEN)
        self._dnld_file_picker = DnDFilePickerCtrl(**kwargs)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.handle_download_button, self._dnld_file_picker)

        down_arrow_bmp = _bitmap('down_arrow.png')
        down_arrow_disabled_bmp = _bitmap('down_arrow_disabled.png')

        self._dnld_button = pbtn.PlateButton(self)
        self._dnld_button.SetBitmap(down_arrow_bmp)
        self._dnld_button.SetBitmapDisabled(down_arrow_disabled_bmp)
        self._dnld_button.SetToolTip(
            'Start download to microcontroller flash')
        self.Bind(wx.EVT_BUTTON, self.on_download, self._dnld_button)
        pub.subscribe(self.handle_download_button, 'Status.Change')
        self.handle_download_button(dummy=None)

        uc_bmp = _bitmap('uC.png')
        uc_stbmp = wx.StaticBitmap(self, label=uc_bmp)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(self._dnld_file_picker, 0, wx.EXPAND)
        vsizer.Add(self._dnld_button, 0, wx.ALIGN_CENTER)
        vsizer.Add(uc_stbmp, 0, wx.ALIGN_CENTER)
        vsizer.AddSpacer(5)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)
        hsizer.Add(vsizer, 1, wx.GROW)
        hsizer.AddSpacer(5)

        self.SetSizer(hsizer)

    def handle_download_button(self, dummy):
        if self._dnld_file_picker.GetPath() and hasattr(ACTIVE_BOARD, 'micro'):
            self._dnld_button.Enable()
        else:
            self._dnld_button.Disable()

    def on_download(self, event):
        confirm_dlg = wx.MessageDialog(parent=self,
                                       caption="WARNING!",
                                       message="""WARNING!

It's possible to render the board inoperable if you download the wrong firmware
into the microcontroller.

ARE YOU SURE YOU WANT TO DO THIS!?!?
""",
                                       style=wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        confirm_dnld = confirm_dlg.ShowModal()
        confirm_dlg.Destroy()
        if confirm_dnld != wx.ID_OK:
            # print "ABORTING!"
            return
        pub.subscribe(self.cleanup, "Micro.Cleanup")
        self._upd_fmw_progress = GxsProgressDialog(
            title="Update Microcontroller Flash", parent=self)

        global PORT_THREAD
        PORT_THREAD = GxsMcuDownloadThread(
            self._dnld_file_picker.GetPath(add_to_history=True))

    def cleanup(self):
        pub.unsubscribe(self.cleanup, "Micro.Cleanup")
        self._upd_fmw_progress.Destroy()


# ===============================================================
# Thread for running uC firmware update.
# ===============================================================
class GxsMcuDownloadThread(Thread):
    def __init__(self, fmw_obj_file):
        Thread.__init__(self)
        self._fmw_obj_file = fmw_obj_file
        self.start()

    def run(self):
        msg_box_title = 'Microcontroller Flash Update Result'
        try:
            reconnect()
            ACTIVE_BOARD.update_firmware(self._fmw_obj_file)
            # Update flag settings because of new uC firmware.
            pub.sendMessage('Status.Change', dummy=None)
            wx.MessageBox('Success!', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate as e:
            wx.MessageBox('Cancelled.', msg_box_title,
                          wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            pub.sendMessage("Micro.Cleanup")
            disconnect()


# ===============================================================
# Board test diagnostic panel.
# ===============================================================

class GxsBoardTestPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(GxsBoardTestPanel, self).__init__(*args, **kwargs)

        self.SetToolTip('Use this tab to run a diagnostic on your XESS board.')

        self._test_button = wx.Button(self, label='Test')
        self._test_button.SetToolTip('Test the board attached to the selected '
                                     'port')
        self.Bind(wx.EVT_BUTTON, self.on_test, self._test_button)
        pub.subscribe(self.handle_test_button, 'Status.Change')
        self.handle_test_button(dummy=None)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)
        hsizer.Add(self._test_button, 0, wx.ALIGN_CENTER_VERTICAL)
        hsizer.AddSpacer(5)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(hsizer)
        vsizer.AddSpacer(5)

        self.SetSizer(vsizer)

    def handle_test_button(self, dummy):
        if hasattr(ACTIVE_BOARD, 'fpga'):
            self._test_button.Enable()
        else:
            self._test_button.Disable()

    def on_test(self, event):
        pub.subscribe(self.cleanup, "Test.Cleanup")
        self._test_progress = GxsProgressDialog(title="Run Board Diagnostic",
                                                parent=self)
        GxsBoardTestThread()

    def cleanup(self):
        pub.unsubscribe(self.cleanup, "Test.Cleanup")
        self._test_progress.Destroy()


# ===============================================================
# Thread for running board diagnostic.
# ===============================================================

class GxsBoardTestThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.start()

    def run(self):
        msg_box_title = 'Board Diagnostic Result'
        try:
            reconnect()
            ACTIVE_BOARD.do_self_test()
            wx.MessageBox('Success!', msg_box_title, wx.OK | wx.ICON_INFORMATION)
        except xserror.XsTerminate:
            wx.MessageBox('Cancelled.', msg_box_title, wx.OK | wx.ICON_INFORMATION)
        except xserror.XsError as e:
            wx.MessageBox(str(e), msg_box_title, wx.OK | wx.ICON_ERROR)
        finally:
            disconnect()
            pub.sendMessage('Test.Cleanup')


# ===============================================================
# Board flags panel.
# ===============================================================

class GxsBoardFlagsPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super(GxsBoardFlagsPanel, self).__init__(*args, **kwargs)

        self.SetToolTip('Use this tab to set the flag bits in your XESS board.')

        self._aux_jtag_flag = wx.CheckBox(self,
                                          label='Enable auxiliary JTAG header')
        self._aux_jtag_flag.SetToolTip('Check to enable the auxiliary JTAG '
                                       'interface through the four-pin header')
        self.Bind(wx.EVT_CHECKBOX, self.on_aux_jtag, self._aux_jtag_flag)
        pub.subscribe(self.handle_aux_jtag_flag, 'Status.Change')
        self.handle_aux_jtag_flag(dummy=None)

        lbl = 'Enable FPGA access to the configuration flash'
        self._flash_flag = wx.CheckBox(self, label=lbl)
        self._flash_flag.SetToolTip('Check to allow the FPGA to read/write the '
                                    'configuration flash')
        self.Bind(wx.EVT_CHECKBOX, self.on_flash, self._flash_flag)
        pub.subscribe(self.handle_flash_flag, 'Status.Change')
        self.handle_flash_flag(dummy=None)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(self._aux_jtag_flag, 0, wx.ALIGN_CENTER_VERTICAL)
        vsizer.AddSpacer(5)
        vsizer.Add(self._flash_flag, 0, wx.ALIGN_CENTER_VERTICAL)
        vsizer.AddSpacer(5)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddSpacer(5)
        hsizer.Add(vsizer, 0, wx.ALIGN_TOP)
        hsizer.AddSpacer(5)

        self.SetSizer(hsizer)

    def handle_aux_jtag_flag(self, dummy):
        reconnect()
        if hasattr(ACTIVE_BOARD, 'micro'):
            self._aux_jtag_flag.Enable()
            self._aux_jtag_flag.SetValue(ACTIVE_BOARD.get_aux_jtag_flag())
        else:
            self._aux_jtag_flag.Disable()
            self._aux_jtag_flag.SetValue(False)
        disconnect()

    def handle_flash_flag(self, dummy):
        reconnect()
        if hasattr(ACTIVE_BOARD, 'micro'):
            self._flash_flag.Enable()
            self._flash_flag.SetValue(ACTIVE_BOARD.get_flash_flag())
        else:
            self._flash_flag.Disable()
            self._flash_flag.SetValue(False)
        disconnect()

    def on_aux_jtag(self, event):
        reconnect()
        self._aux_jtag_flag.SetValue(ACTIVE_BOARD.toggle_aux_jtag_flag())
        disconnect()
        # Because port will change if JTAG feature changes.
        pub.sendMessage('Port.Check', force_check=True)

    def on_flash(self, event):
        reconnect()
        self._flash_flag.SetValue(ACTIVE_BOARD.toggle_flash_flag())
        disconnect()


# ===============================================================
# GXSTOOLs FlatNotebook for holding tabs.
# ===============================================================
class GxsFlatNotebook(fnb.FlatNotebook):
    def __init__(self, parent):
        mystyle = fnb.FNB_FF2 | fnb.FNB_NO_X_BUTTON | fnb.FNB_NO_NAV_BUTTONS | fnb.FNB_SMART_TABS
        super(GxsFlatNotebook, self).__init__(parent, agwStyle=mystyle)
        self._port_panel = GxsPortPanel(self)
        self.AddPage(self._port_panel, 'Ports')
        self._fpga_panel = GxsFpgaConfigPanel(self)
        self.AddPage(self._fpga_panel, 'FPGA')
        self._sdram_panel = GxsSdramPanel(self)
        self.AddPage(self._sdram_panel, 'SDRAM')
        self._flash_panel = GxsFlashPanel(self)
        self.AddPage(self._flash_panel, 'Flash')
        self._test_panel = GxsBoardTestPanel(self)
        self.AddPage(self._test_panel, 'Test')
        self._flags_panel = GxsBoardFlagsPanel(self)
        self.AddPage(self._flags_panel, 'Flags')
        self._uc_panel = GxsMicrocontrollerPanel(self)
        self.AddPage(self._uc_panel, 'uC')


class MyFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title='', pos=wx.DefaultPosition,
                 size=(600, 400), style=wx.DEFAULT_FRAME_STYLE,
                 name='MyFrame', ):
        super(MyFrame, self).__init__(parent, id, title, pos, size, style,
                                      name, )

        self.menu_bar = wx.MenuBar()

        file_menu = wx.Menu()
        # file_menu.Append(wx.ID_NEW)
        # file_menu.Append(wx.ID_OPEN)
        # file_menu.Append(wx.ID_SAVE)
        # file_menu.Append(wx.ID_SAVEAS)
        # file_menu.Append(wx.ID_CLOSE)
        m_exit = file_menu.Append(wx.ID_EXIT, 'E&xit\tAlt-X',
                                  'Close window and exit program.')
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        self.menu_bar.Append(file_menu, 'File')

        help_menu = wx.Menu()
        # help_menu.Append(wx.ID_HELP)
        m_about = help_menu.Append(wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_about, m_about)
        self.menu_bar.Append(help_menu, 'Help')
        self.SetMenuBar(self.menu_bar)

        self.SetStatusBar(GxsStatusBar(self))

    def on_exit(self, _):
        self.Close()

    def on_about(self, _):
        dlg = GxsAboutBox()
        dlg.ShowModal()
        dlg.Destroy()


class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, title='XESS Board Tools')
        self.notebook = GxsFlatNotebook(self.frame)
        self.SetTopWindow(self.frame)
        self.frame.Show()
        self.timer = GxsTimer()
        return True


def gxstools():
    app = MyApp(False)
    app.MainLoop()


if __name__ == '__main__':
    gxstools()
