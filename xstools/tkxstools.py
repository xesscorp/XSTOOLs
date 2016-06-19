from tkinter import *


def do_nothing():
    print('do nothing called')

if __name__ == '__main__':
    root = Tk()

    menu = Menu(root)
    root.config(menu=menu)

    root.mainloop()
