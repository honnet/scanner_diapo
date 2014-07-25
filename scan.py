# coding: utf-8
# Copyright 2011 Christophe Combelles <ccomb@gorfou.fr>
# Ce programme est distribué selon les termes de la licence GNU GPL v3
# Voir http://www.gnu.org/licenses/gpl.html
from Tkinter import *
import tkMessageBox
import tkFileDialog, tkMessageBox
import sys, serial, time, os
import psutil
from pywinauto import application, timings, MatchError
timings.Timings.Fast()
timings.Timings.window_find_timeout = 1

VERSION="1.1"
PORT = 'COM5'

class Scan(Frame):

    def __init__(self, master):
        self.master = master
        Frame.__init__(self, self.master)
        self.grid()

        # widgets

        self.title = Label(self, text=u"scan version %s" % VERSION)

        self.port_label = Label(self, text=u"Port")
        self.port = StringVar()
        self.port.set(PORT)
        self.port_entry = Entry(self, textvariable=self.port)

        self.zero_button = Button(self, text=u"Return to zero",
                                    command = self._zero)
        self.scan_button = Button(self, text=u"Scan",
                                    command = self._scan)
        self.path = None
        self.directory = StringVar()
        self.directory.set(u"Répertoire destination")
        if os.path.exists('saved_dir.txt'):
            self.path = open('saved_dir.txt').read()
            self.directory.set(self.path)
        self.path_label = Label(self, text=u"Sélectionnez le même répertoire d'images\n"
                                           u"que dans le programme Kodak")
        self.path_button = Button(self, textvariable=self.directory,
                                  command = self._choose_path)

        self.nbtours_label = Label(self, text=u"Nb de tours moteur par image")
        self.nbtours = IntVar()
        self.nbtours.set(1)
        self.nbtours_entry = Entry(self, width=3, textvariable=self.nbtours)

        self.delay_label = Label(self, text=u"Nb secondes d'attente à la fin du scan")
        self.delay = IntVar()
        self.delay.set(1)
        self.delay_entry = Entry(self, width=3, textvariable=self.delay)

        self.images = StringVar()
        self.images.set('1-3,10-13')
        self.images_label = Label(self, text=u"Séquence d'images")
        self.images_entry = Entry(self, textvariable=self.images)

        self.ice_label = Label(self, text=u"Traitement infrarouge ICE\n(Il faut sélectionner ICE aussi sur HR Scanner)")
        self.ice = StringVar()
        self.ice.set('no')
        self.ice_checkbutton = Checkbutton(self, variable=self.ice, onvalue="yes", offvalue="no")

        self.position = IntVar()
        self.position.set(0)
        self.position_label = Label(self, text=u"Position supposée")
        self.position_entry = Entry(self, width=6, textvariable=self.position, state='disabled')

        
        # layout
        self.title.grid(column=0, row=0, columnspan=3)
        self.path_label.grid(column=1, row=1, padx=15, pady=15)
        self.path_button.grid(column=2, row=1, padx=15, pady=15)
        self.port_label.grid(column=1, row=2, padx=15, pady=15)
        self.port_entry.grid(column=2, row=2, padx=15, pady=15)
        self.nbtours_label.grid(column=1, row=3, padx=15, pady=15)
        self.nbtours_entry.grid(column=2, row=3, padx=15, pady=15)
        self.delay_label.grid(column=1, row=4, padx=15, pady=15)
        self.delay_entry.grid(column=2, row=4, padx=15, pady=15)
        self.images_label.grid(column=1, row=5, padx=15, pady=15)
        self.images_entry.grid(column=2, row=5, padx=15, pady=15)
        self.ice_label.grid(column=1, row=6, padx=15, pady=15)
        self.ice_checkbutton.grid(column=2, row=6, padx=15, pady=15)
        self.position_label.grid(column=1, row=7, padx=15, pady=15)
        self.position_entry.grid(column=2, row=7, padx=15, pady=15)
        self.scan_button.grid(column=3, row=8, padx=15, pady=15)
        self.zero_button.grid(column=0, row=8, padx=15, pady=15)

        self.app = application.Application()
        try:
            # pour trouver la fenetre : app.a.a.a
            self.scanclic = self.app.window_(title_re='Job*').window_(title_re='Scan*').Click
            #self.scanclic() # once to init (!)
        except:
            tkMessageBox.showerror(u"Erreur", u"Démarrez et préparez le programme HR Scanner")
            sys.exit()
        #tkMessageBox.showwarning(u"Attention", u"Effectuez au moins 1 scan pour que la fenêtre s'appelle Job...")
        self.usb = serial.Serial(self.port.get(), 9600, timeout=10)


    def _zero(self):
        """Return to zero
        """
        print('go' + str(-self.position.get()))
        self.usb.write('go' + str(-self.position.get()))
        self.position.set(0)
        print('position='+str(self.position.get()))
        # wait until we get the signal from the arduino
        resp = ''
        while '\n' not in resp:
            resp = self.usb.readline()
            print('1 - arduino response ='+resp)


    def _scan(self):
        time.sleep(2) # necessary sleep on Windows :'(
        if not self.path or not os.path.exists(self.path):
            tkMessageBox.showwarning(u"Erreur", u"Sélectionnez le répertoire où les images sont scannées")
            return
        if not (1 <= self.nbtours.get() <=9):
            tkMessageBox.showwarning(u"Erreur", u"Le nombre de tours doit être entre 1 et 9")
            return

        ranges = self.images.get().replace(' ', '').split(',')
        print(ranges)
        # process each image range
        for r in ranges:
            self.master.update_idletasks()
            # move to the first image
            first, last = [int(i) for i in r.split('-')]
            # the absolute position depends on the nb of laps per image
            first *= self.nbtours.get()
            last *= self.nbtours.get()
            print('go' + str(int(first) - self.position.get()))
            self.usb.write('go' + str(int(first) - self.position.get()))
            self.position.set(int(first))
            print('position='+str(self.position.get()))
            # wait until we get the signal from the arduino
            resp = ''
            while '\n' not in resp:
                resp = self.usb.readline()
                print('1 - arduino response ='+resp)

            os.chdir(self.path)
            # start the scan procedure until the last image
            while self.position.get() <= last:
                self.master.update_idletasks()
                # start the scan
                print('scan')
                self.scanclic()
                self.scanclic()

                files = set(os.listdir('.'))
                # tell the arduino to start the full procedure
                print('start for %s laps' % str(self.nbtours.get()))
                arduino_command = 'ic' if self.ice.get() == 'yes' else 'ok'
                self.usb.write(arduino_command + str(self.nbtours.get()))

                # wait until we get the signal from the arduino
                resp = ''
                while 'finished' not in resp:
                    resp = self.usb.readline()
                    print('2 - arduino response = '+resp)

                # wait until the scan saves the image
                attempts = 0
                print 'waiting for new file to appear'
                while len(os.listdir('.')) == len(files):
                    self.master.update_idletasks()
                    attempts += 1
                    time.sleep(1)
                    if attempts > 15:
                        tkMessageBox.showerror(u"Erreur", u"Aucune image reçue du scanner. Avez-vous sélectionné le bon dossier d'images ?")
                        sys.exit()
                    print 'waiting for new file to appear'
                newfile = (set(os.listdir('.')) - files).pop()
                previous_size = os.stat(newfile)[6]
                time.sleep(1)
                while os.stat(newfile)[6] != previous_size:
                    self.master.update_idletasks()
                    print 'waiting for filesize to be the same (%s)' % previous_size
                    previous_size = os.stat(newfile)[6]
                    time.sleep(1)
                    
                print "waiting %s secs " % str(self.delay.get())
                time.sleep(self.delay.get())
                self.position.set(self.position.get() + self.nbtours.get())
                print('position='+str(self.position.get()))

    def _choose_path(self):
        self.path = tkFileDialog.askdirectory(
            parent=root,
            title=u'Sélectionnez le répertoire où le programme Kodak stocke les images scannées')
        self.directory.set(os.path.basename(self.path))
        with open('saved_dir.txt', 'w') as f:
            f.write(self.path)

    def quit_callback(self):
        print 'exiting...'
        self.usb.close()
        self.master.destroy()

if __name__ == '__main__':
    root = Tk()
    app = Scan(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_callback)
    root.mainloop()

