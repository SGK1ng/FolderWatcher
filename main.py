import os
from tkinter import Tk
from gui import Window

def main():
    root = Tk()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, 'logo.ico')
    if not os.path.isfile(icon_path):
        pass
    else:
        root.iconbitmap(icon_path)
    
    app = Window(root)
    root.mainloop()

if __name__ == "__main__":
    main()