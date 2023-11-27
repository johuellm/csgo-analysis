import tkinter

root = tkinter.Tk()
root.wm_title("Embedding in Tk")

greeting = tkinter.Label(text="Hello, Tkinter")
greeting.pack()

button_quit = tkinter.Button(master=root, text="Quit", command=root.destroy)
button_quit.pack(side=tkinter.BOTTOM)

tkinter.mainloop()
