from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *

from PIL import ImageTk

from xstools import xsboard

_BLUE = '#2c4484'
_YELLOW = '#fadd67'
_GOLDEN_YELLOW = '#c09853'


def do_nothing():
    print('do nothing called')


def on_blink():
    # TODO: Avoid exception if nothing connected
    board = xsboard.XsBoard.get_xsboard(xsusb_id=0, xsboard_name='xula2-lx25')
    print(board)
    print(board.get_board_info())


def about_dialog():
    title = 'About GXSTOOLs'
    msg = 'Graphical XSTOOLs Utilities Version 0.1.31'
    msg_box = messagebox.showinfo(title, msg)
    return msg_box


def port_frame(master):
    frame = Frame(master=master)
    var = StringVar(master=master)
    usb0 = 'USB0'
    var.set(usb0)
    port_optmenu = OptionMenu(frame, var, usb0)
    port_optmenu.pack(side=LEFT)
    blink_button = Button(master=frame, text='Blink', command=on_blink)
    blink_button.pack(side=LEFT)
    return frame


def fpga_frame(master):
    frame = Frame(master=master)
    photo = ImageTk.PhotoImage(file='icons/fpga.png')
    photo_label = Label(master=frame, image=photo)
    photo_label.config()
    photo_label.image = photo
    photo_label.pack(side=TOP)
    return frame


def application(master):
    master.title('XESS Board Tools')

    menu = Menu(master=master)
    master.config(menu=menu)

    children = menu.children

    sub_menu = Menu()
    menu.add_cascade(label='XSTools', menu=sub_menu)
    sub_menu.add_command(label='About', command=about_dialog)

    # TODO: Write coroutine (generator) to check for boards while maintaining
    # GUI responsiveness

    tab_texts = [
        ('Ports', port_frame),
        ('FPGA', fpga_frame),
        ('SDRAM', None),
        ('Flash', None),
        ('Test', None),
        ('Flags', None),
        ('uC', None),
    ]

    nb = Notebook(master=master, width=100, height=100)  # , activefg=_YELLOW
    for tab_text, fn in tab_texts:
        if fn is None:
            tab = Frame(master=master)
        else:
            tab = fn(master=master)
        nb.add(tab, text=tab_text)
    nb.pack(side=TOP)

    status_kwargs = dict(relief=SUNKEN, anchor=W)  # bg=_BLUE, bd=1, fg='white',
    txt = 'Port: USB0 Board: XuLA2-LX25'
    status = Label(master=master, text=txt, **status_kwargs)
    status.pack(side=BOTTOM, fill=X)

if __name__ == '__main__':
    root = Tk()
    application(master=root)
    root.mainloop()
