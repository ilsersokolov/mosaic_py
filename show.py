import logging
import os
import sys
import time
import tkinter

from PIL import Image, ImageTk

UPDATE_TIME = 1*1000
LOG_FILE = 'show.log'
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

log_formatter = logging.Formatter(FORMAT)
logger = logging.getLogger('show')
logger.setLevel(logging.INFO)

fh = logging.FileHandler(LOG_FILE)
fh.setFormatter(log_formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(log_formatter)
logger.addHandler(ch)


class App():
    def __init__(self):
        self.root = tkinter.Tk()
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.w = w
        self.h = h
        self.root.overrideredirect(1)
        self.root.geometry("%dx%d+0+0" % (w, h))
        self.root.focus_set()
        self.root.bind("<Escape>", lambda e: (
            e.widget.withdraw(), e.widget.quit()))
        self.canvas = tkinter.Canvas(self.root, width=w, height=h)
        self.canvas.pack()
        self.canvas.configure(background='black')
        # image = self.resize()
        self.resize()
        self.imagesprite = self.canvas.create_image(w/2, h/2, image=self.image)
        # self.imagesprite = canvas.create_image(0, 0, image=image)
        self.root.after(UPDATE_TIME, self.redraw)
        self.root.mainloop()

    def redraw(self):
        logger.info('Redraw mosaic')
        # self.canvas.delete(self.imagesprite)
        # w = self.w
        # h = self.h
        # image = 
        self.resize()
        # self.imagesprite = self.canvas.create_image(w/2,h/2,image=image)
        self.canvas.itemconfig(self.imagesprite, image=self.image)
        self.root.after(UPDATE_TIME, self.redraw)

    def resize(self):
        w = self.w
        h = self.h
        try:
            pilImage = Image.open('data/mosaic.png')
            imgWidth, imgHeight = pilImage.size
            if imgWidth > w or imgHeight > h:
                ratio = min(w/imgWidth, h/imgHeight)
                imgWidth = int(imgWidth*ratio)
                imgHeight = int(imgHeight*ratio)
                pilImage = pilImage.resize((imgWidth, imgHeight), Image.ANTIALIAS)
            image = ImageTk.PhotoImage(pilImage)
            self.image = image
        except OSError:
            pass

    def quit(self):
        self.root.destroy()


def main():
    print('Press Ctrl+C to exit')
    try:
        logger.info('Show mosaic')
        App()
        logger.info('Done!')
        # time.sleep(UPDATE_TIME)
        # app.quit()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    logger.info('Start')
    # main()
    try:
        main()
    except Exception as ex:
        logger.error('Unknown error')
        logger.error(str(ex))
        sys.exit(1)
    logger.info('Finished!')
