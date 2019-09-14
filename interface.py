from tkinter import filedialog
from tkinter import font
from tkinter import ttk
from tkinter.tix import *
from tkinter.messagebox import showinfo
import socket
import xmlParser
import os
from shutil import copyfile
import DRO
import handleCommand


testcount = 0


# constructor
class Window(Frame):
    # Constructor//Globals
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.listboxFrame = Frame(self, width=200, height=400)
        self.listboxFrame.pack(side=LEFT)
        self.dataFrame = Frame(self, width=590, height=300)
        self.dataFrame.pack(pady=125)
        self.master = master
        self.window()
        self.myFile = None
        self.tempFile = open("xmltempdata.xml", 'w')
        self.SOCK = None
        self.Connected = False
        self.isSaved = False

    # main window objects
    def window(self):
        self.master.title("Tyler's App")
        self.pack(fill=BOTH, expand=True)

        global machineName
        Label(text=("Connected to: " + machineName)).place(x=650)

        # connect button, triggers Connect function
        self.connectedLabel = Label(text="Status: Not Connected")
        self.connectedLabel.place(x=5, y=660)
        self.connectButton = Button(self, text="Connect", command=self.connect, height=2, width=10)
        self.connectButton.place(x=340, y=640)

        # menu bar
        menu = Menu(self.master)
        self.master.config(menu=menu)
        file = Menu(menu)
        file.add_command(label="Export XML", command=self.saveas)
        file.add_command(label="Quit", command=self.exit_client)
        menu.add_cascade(label="File", menu=file)


    def exit_client(self):
        self.master.destroy()

    # Creates XML file to write Verisurf Responses
    def saveas(self):
        fileTypes = [('XML Files', '*.xml')]
        file = filedialog.asksaveasfile(mode='a', filetypes=fileTypes, defaultextension=fileTypes)
        try:
            self.lbl.configure(text="File path: " + file.name)

            if self.isSaved == False:
                self.myFile = open(file.name, "w+")
                self.tempFile.close()
                self.myFile.close()
                copyfile('xmltempdata.xml', file.name)
                self.isSaved = True
                # os.remove(self.tempFile)
                self.myFile = open(file.name, "a")
                base = os.path.basename(self.tempFile.name)
                os.remove(base)
            else:
                self.myFile.close()
                tempcopy = open(file.name, "w+")
                tempcopy.close()
                copyfile(self.myFile.name, file.name)
                self.myFile = open(file.name, "a")

        except AttributeError:
            None
            # do nothing, file was not saved.

    # Connects to Verisurf.
    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        global ipnum
        host = ipnum
        port = 33666
        try:
            if self.Connected == False:
                s.connect((host, port))
                self.SOCK = s
                tm = s.recv(1024)
                self.tm = tm.decode('ascii')
                self.connectedLabel.configure(text="Status: Connected")
                handleCommand.writeFiles(self, self.tm)
                self.Connected = True
                self.connectButton.configure(text="Disconnect")
                self.layOut()
            else:
                self.Connected = False
                self.SOCK.close()
                self.connectButton.configure(text="Connect")
                self.connectedLabel.configure(text="Status: Not Connected")
                for widget in self.listboxFrame.winfo_children():
                    widget.destroy()
                for widget in self.dataFrame.winfo_children():
                    widget.destroy()
        except ConnectionError:
            self.connectedLabel.configure(text="Unable to Connect")
            self.Connected = False

    def layOut(self):
        self.getPlans()
        self.objType = StringVar()
        Button(self, text="DRO", command=lambda: DRO.dispDevice(self)).place(x=260, y=600)
        menu = ttk.Combobox(self, values=['Point', 'Line', 'Circle', 'Ellipse',
                                          'Slot', 'Plane', 'Sphere', 'Cylinder','Spline',
                                          'Cone', 'Parabaloid', 'Torus', 'Analysis'],
                            textvariable=self.objType)
        menu.place(x=300,y=100)
        menu.current(0)
        menu.bind("<<ComboboxSelected>>", self.selection)

    def selection(self, event):
        non = handleCommand.sendCommand(self, "<Measure_"+self.objType.get() + " />\n")


    def resize_top(self, event):
        size = self.topwin.winfo_height()
        self.font1['size'] = int(size/20)


    # Asks verisurf for plan names. Creates drop down box to select each plan
    def getPlans(self):
        Label(text="Active Plan").place(x=0, y=50)
        sender = "<Inspect_Plan_List />\n"
        received = handleCommand.sendCommand(self, sender)
        self.Plans = xmlParser.ParseXML(received, "plan", "id", None)

        # CREATE DROP DOWN
        self.selected = StringVar()
        menu = ttk.Combobox(self, values=[*self.Plans], textvariable=self.selected)
        menu.current(0)
        menu.place(x=0, y=80)
        menu.bind("<<ComboboxSelected>>", self.userSelection)
        self.planDetails(0)


    # Required tkinter function to detect selection
    def userSelection(self, event):
        for widget in self.listboxFrame.winfo_children():
            widget.destroy()
        for widget in self.dataFrame.winfo_children():
            widget.destroy()
        self.planDetails(self.Plans.index(self.selected.get()))

    # Gets plan details - objects in plan
    def planDetails(self, planNumber):
        try:
            send = "<Inspect_Plan_Info id = \"" + str(planNumber) + "\" />\n"
            received = handleCommand.sendCommand(self, send)
            self.parsedList = xmlParser.ParseXML(received, "plan_object", "object_id", None)

            # CREATE DROP DOWN

            self.listboxFrame.scrollbar = Scrollbar(self.listboxFrame, orient="vertical")
            self.listboxFrame.scrollbar.pack(side=RIGHT, fill=Y)

            self.listboxFrame.objects = Listbox(self.listboxFrame, height=20)
            self.listboxFrame.objects.pack(side=LEFT, expand=True, fill=Y)
            self.listboxFrame.objects.config(yscrollcommand=self.listboxFrame.scrollbar.set)
            self.listboxFrame.objects.bind("<<ListboxSelect>>", self.ObjectSelect)
            self.listboxFrame.scrollbar.config(command=self.listboxFrame.objects.yview)

            x=1
            for items in self.parsedList:
                self.listboxFrame.objects.insert(END, items)
                x+=1
            ranger = len(self.parsedList)
            isOOT = self.checkOOT(ranger)
            x=0
            for i in isOOT:
                if i == True:
                    self.listboxFrame.objects.itemconfig(x, bg="red")
                elif i == None:
                    self.listboxFrame.objects.itemconfig(x, bg="white")
                else:
                    self.listboxFrame.objects.itemconfig(x, bg="green")
                x+=1
        except:
            showinfo("No data", "Selected plan has no objects.")

    def checkOOT(self, num):
        indexOOT = []
        for i in range(0, num):
            isOOT = False
            sender = "<Inspect_Object_Info id=\"" + str(i) + "\" />\n"
            received = handleCommand.sendCommand(self, sender)
            taglist = ["name", "nominal", "measured", "deviation", "tolmin", "tolmax"]
            list = xmlParser.ParseXML(received, "property", "none", taglist)
            for items in list:
                if items['measured'] == 0:
                    isOOT = None
                    break
                elif items['deviation'] > items['tolmax'] or items['deviation'] < items['tolmin']:
                    isOOT = True
                    break
            indexOOT.insert(i, isOOT)
        return indexOOT

    # Tkinter function needed to detect when dropdown has changed
    def ObjectSelect(self, event):
        for widget in self.dataFrame.winfo_children():
            widget.destroy()
        widget = event.widget
        selection = widget.curselection()
        value = widget.get(selection[0])
        self.objectDetails(self.parsedList.index(value))

    def objectDetails(self, num):
        sender = "<Inspect_Object_Info id=\"" + str(num) + "\" />\n"
        received = handleCommand.sendCommand(self, sender)

        taglist = ["name", "nominal", "measured", "deviation", "tolmin", "tolmax"]
        self.objectList = xmlParser.ParseXML(received, "property", "none", taglist)
        self.img = PhotoImage(file="sizeicon.png")
        resultsbtn = Button(self, command=self.showResults, image=self.img, height=20, width=20)
        resultsbtn.image = self.img
        resultsbtn.place(x=650, y=585)
        resultsTip = Balloon()
        resultsTip.bind_widget(resultsbtn, balloonmsg="Expand Results")
        self.placeResults()

    def placeResults(self):

        frameName = self.dataFrame
        xpad = 40
        ypad = 5
        fontsize = 10

        self.font1 = font.Font(self.master, family="Helvetica", size=fontsize, weight="bold")
        frameName.actual = Label(frameName, text="Act", font=self.font1)
        frameName.actual.grid(row=0, column=1, padx=xpad)
        frameName.meas = Label(frameName, text="Meas", font=self.font1)
        frameName.meas.grid(row=0, column=2, padx=xpad)
        frameName.dev = Label(frameName, text="Dev", font=self.font1)
        frameName.dev.grid(row=0, column=3, padx=xpad)

        inTol = "green"
        outTol = "red"
        self.isOOT = False
        rows = 1
        # generates values to display
        for items in self.objectList:
            frameName.nameLabel = Label(frameName, text=items['name'], font=self.font1)
            frameName.nameLabel.grid(row=rows, column=0, padx=xpad, pady=ypad, sticky=W)
            frameName.nomLabel = Label(frameName, text="{:.3f}".format(items['nominal']), font=self.font1, fg=inTol)
            frameName.nomLabel.grid(row=rows, column=1, padx=xpad, pady=ypad, sticky=W)
            frameName.devLabel = Label(frameName, text="{:.3f}".format(items['deviation']), font=self.font1, fg=inTol)
            frameName.devLabel.grid(row=rows, column=3, padx=xpad, pady=ypad, sticky=W)

            # Logic to determine if OOT. changes to red if so
            if items['deviation'] > items['tolmax'] or items['deviation'] < items['tolmin']:
                frameName.measLabel = Label(frameName, text="{:.3f}".format(items['measured']), font=self.font1,
                                            fg=outTol)
                self.isOOT = True
            else:
                frameName.measLabel = Label(frameName, text="{:.3f}".format(items['measured']), font=self.font1,
                                            fg=inTol)
            frameName.measLabel.grid(row=rows, column=2, padx=xpad, pady=ypad, sticky=W)

            rows += 1

    def showResults(self):
        self.font = font.Font(self.master, family="Helvetica", size=20, weight="bold")

        self.top = Toplevel(master=None, height=750, width=750, relief="sunken")
        for x in range(0, len(self.objectList)):
            self.top.grid_rowconfigure(x, weight=1)
            self.top.grid_columnconfigure(x, weight=1)
        # Default headers for information
        actual = Label(self.top, text="Act", font=self.font)
        actual.grid(row=0, column=1)
        meas = Label(self.top, text="Meas", font=self.font)
        meas.grid(row=0, column=2)
        dev = Label(self.top, text="Dev", font=self.font)
        dev.grid(row=0, column=3)

        inTol = "green"
        outTol = "red"

        rows = 1
        # generates values to display
        for items in self.objectList:
            nameLabel = Label(self.top, text=items['name'], font=self.font)
            nameLabel.grid(row=rows, column=0, padx=40, pady=20, sticky=W)
            nomLabel = Label(self.top, text="{:.3f}".format(items['nominal']), font=self.font, fg=inTol)
            nomLabel.grid(row=rows, column=1, padx=100, pady=20, sticky=W)
            devLabel = Label(self.top, text="{:.3f}".format(items['deviation']), font=self.font, fg=inTol)
            devLabel.grid(row=rows, column=3, padx=100, pady=20, sticky=W)

            # Logic to determine if OOT. changes to red if so
            if items['deviation'] > items['tolmax'] or items['deviation'] < items['tolmin']:
                measLabel = Label(self.top, text="{:.3f}".format(items['measured']), font=self.font, fg=outTol)
            else:
                measLabel = Label(self.top, text="{:.3f}".format(items['measured']), font=self.font, fg=inTol)
            measLabel.grid(row=rows, column=2, padx=100, pady=20, sticky=W)

            rows += 1

        self.update()
        self.top.bind('<Configure>', self.resize)

    # handles window resizing event. adjusts font size accordingly.
    def resize(self, event):
        try:
            size = len(self.objectList) * 14
            self.font['size'] = int(((self.top.winfo_height() + self.top.winfo_width()) / size))
        except TclError:
            # do nothing
            None


def runWindow(ip, name):
    global ipnum
    global machineName
    machineName = name
    ipnum = ip

    root = Tk()
    root.geometry("800x700")
    root.resizable(False, False)
    app = Window(root)
    root.mainloop()


ipnum = None
machineName = None

runWindow("127.0.0.1", "Tyler")
