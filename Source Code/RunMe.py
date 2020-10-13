import tkinter, os
from tkinter import *
from tkinter.filedialog import askopenfilename
from TFTPClientSide import TFTPClient

class TFTPGui(object):

    def __init__(self, root):
        self.host = tkinter.StringVar(root)
        self.browse_value = tkinter.StringVar()
        
        #labels
        self.server = tkinter.LabelFrame(root, text = "Server IP Address:" )
        self.block = tkinter.LabelFrame(root, text = "Block Size" )
        self.browse_upload = tkinter.LabelFrame(root, text = "Browse for file to Upload:" )
        self.remote_download = tkinter.LabelFrame(root, text = "Remote Filename of file to Download:" )
        self.pref_filename = tkinter.LabelFrame(root, text = "Preferred Filename:" )
        
        #entrys
        self._host = tkinter.Entry(self.server, takefocus = 1, width = 30 )
        self._block = tkinter.Entry(self.block, width = 8 )
        self.remote_file = tkinter.Entry(self.remote_download, width = 30 )
        self.local_file = tkinter.Entry(self.browse_upload, width = 30, textvariable=self.browse_value)
        self.alt_filename = tkinter.Entry(self.pref_filename, width = 30 )

        #buttons
        self.write = tkinter.Button(root, text = "Upload", padx = 23, pady = 15, command = self.cmd_upload  )
        self.read = tkinter.Button(root, text = "Download", padx = 15, pady = 15, command = self.cmd_download )
        self.browse = tkinter.Button(self.browse_upload, text = "Browse", command = self.browse_command)
        
        #fields
        self.server.grid( in_ = root, column = 1, row = 1, columnspan = 1, rowspan = 1, sticky = "news", padx=5, pady=5)
        self.block.grid( in_ = root, column = 2, row = 1, columnspan = 1, rowspan = 1, sticky = "news", padx=5, pady=5 )
        self.browse_upload.grid( in_ = root, column = 1, row = 2, columnspan = 1, rowspan = 1, sticky = "news", padx=5, pady=5 )
        self.remote_download.grid( in_ = root, column = 1, row = 3, columnspan = 1, rowspan = 1, sticky = "news", padx=5, pady=5 )
        self.pref_filename.grid( in_ = root, column = 1, row = 4, columnspan = 1, rowspan = 1, sticky = "news", padx=5, pady=5 )

        #row and column configure
        root.grid_rowconfigure(1, weight = 0, minsize = 40, pad = 0)
        root.grid_rowconfigure(2, weight = 0, minsize = 73, pad = 0)
        root.grid_rowconfigure(3, weight = 0, minsize = 25, pad = 0)
        root.grid_rowconfigure(4, weight = 0, minsize = 25, pad = 0)
        root.grid_columnconfigure(1, weight = 0, minsize = 100, pad = 0)
        root.grid_columnconfigure(2, weight = 0, minsize = 15, pad = 0)
        
        #layout
        self._host.grid( in_ = self.server, column = 1, row = 1, columnspan = 1, padx = 5, pady = 5, rowspan = 1, sticky = "ew")
        self._block.grid( in_ = self.block, column = 1, row = 1, columnspan = 1, padx = 5, pady = 5, rowspan = 1, sticky = "ew" )
        self.write.grid( in_ = root, column = 2, row = 2, columnspan = 1, padx = 5, pady = 5, rowspan = 1, sticky = "s" )
        self.read.grid( in_ = root, column = 2, row = 3, columnspan = 1, padx = 5, pady = 5, rowspan = 1, sticky = "s" )
        self.remote_file.grid( in_ = self.remote_download, column = 1, row = 1, padx = 5, pady = 5, columnspan = 1, rowspan = 1, sticky = "ew")
        self.local_file.grid( in_ = self.browse_upload, column = 1, row = 1, padx = 5, pady = 5, columnspan = 1, rowspan = 1, sticky = "ew")
        self.browse.grid( in_ = self.browse_upload, column = 1, row = 1, padx = 5, pady = 5, columnspan = 1, rowspan = 1, sticky = "e" )
        self.alt_filename.grid( in_ = self.pref_filename, column = 1, row = 1, columnspan = 1, padx = 5, pady = 5, rowspan = 1, sticky = "ew")

        self.server.grid_rowconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.server.grid_columnconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.block.grid_rowconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.block.grid_columnconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.browse_upload.grid_rowconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.browse_upload.grid_columnconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.remote_download.grid_rowconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.remote_download.grid_columnconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.pref_filename.grid_rowconfigure(1, weight = 0, minsize = 40, pad = 0)
        self.pref_filename.grid_columnconfigure(1, weight = 0, minsize = 40, pad = 0)
        

    def cmd_upload(self):
        toUpload = TFTPClient(self._host.get(), 69)
        file_name = self.local_file.get()
        alt_filename = self.alt_filename.get()
        blksize = self._block.get()
        if not os.path.isfile(file_name):
            raise Exception('File %s does not exist!' % file_name)
        else:
            if toUpload.upload(512 if len(blksize) <= 0 else int(blksize), file_name, os.path.basename(file_name) if len(alt_filename) <= 0 else alt_filename):
                print('Successful File Transfer. Closing Connection...')

    def cmd_download(self):
        toDownload = TFTPClient(self._host.get(), 69)
        file_name = self.remote_file.get()
        alt_filename = self.alt_filename.get()
        blksize = self._block.get()        
        if toDownload.download(512 if len(blksize) <= 0 else int(blksize), file_name, file_name if len(alt_filename) <= 0 else alt_filename):
            if os.path.isfile(file_name):
                print('Successful File Transfer. Closing Connection...')

    def browse_command(self):
        self.browse_value.set(askopenfilename())



def main():
    
    root = Tk()
    window = TFTPGui(root)
    root.title('TFTP Client by TRICIUH')
    root.resizable(width=FALSE, height=FALSE)
    
    try: 
        run()
    except NameError: 
        pass
    
    root.protocol('WM_DELETE_WINDOW', root.quit)
    root.mainloop()

if __name__ == '__main__': 
    main()
