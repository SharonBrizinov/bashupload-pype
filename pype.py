#!/usr/bin/env python3

###########################################
#                                         #
#                 "Pype"                  #
#       Simple file sharing server,       #
#       to upload and download file       #
#                from  CLI                #
#                                         #
#             Etienne  SELLAN             #
#               17/10/2018                #
#                                         #
###########################################

import sys
import time
import signal
import threading
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import os
import binascii
import shutil
import base64
import math
import hashlib

# SETTINGS BEGIN
settings = {}
settings["url"] = "http://" + sys.argv[1] # url
settings["listen_address"] = "0.0.0.0"
settings["port"] = 80
settings["directory"] = "/tmp"
settings["delete_limit"] = 24  # hours
settings["cleaning_interval"] = 24  # hours
settings["id_length"] = 2  # bytes
settings["max_name_length"] = 200  # chars
settings["max_file_size"] =  (5 * 1024*1024*1024)  # 5gb
SECRET = "SECRET111222"
# SETTINGS END

def settings_initialisation():
    for setting in settings:
        # Take environment settings if defined
        if ("pype_"+setting) in os.environ:
            settings[setting] = os.environ[("pype_"+setting)]
    settings["current_directory"] = os.path.dirname(os.path.realpath(__file__))

def path_to_array(path):
    # Split path
    path_array = path.split('/')
    # Remove empty elements
    path_array = [element for element in path_array if element]
    return path_array


def array_to_path(path_array):
    # Join array
    path = '/' + '/'.join(path_array)
    return path


def path_initialisation():
    global directory
    directory = path_to_array(settings["directory"])
    directory.append("pype")
    # Create directory for Pype if not exist
    if not os.path.exists(array_to_path(directory)):
        os.makedirs(array_to_path(directory), 666)


def initialisation():
    settings_initialisation()
    path_initialisation()


class request_handler(BaseHTTPRequestHandler):
    def do_GET(self):  # For home page and download
        # Check for options
        if '?' in self.path:
            # Split options of request
            self.option = self.path.split('?')[1]
            self.request_path = self.path.split('?')[0]
        else:
            # No options
            self.option = None
            self.request_path = self.path
        
        path_digest = hashlib.sha512(self.request_path.encode('utf-8')).hexdigest()
        # Convert path of request to array for easy manipulation
        self.request_path = path_to_array(self.request_path)
        # Construct full path of the file
        self.file_path = directory+[path_digest]

        if len(self.request_path) > 0:
            if self.request_path[0] == SECRET+"help":
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(settings["current_directory"]+'/'+'help.txt', 'r') as help_file:
                    self.wfile.write(str.encode(help_file.read().replace("[url]", settings["url"])+"\n"))
            elif self.request_path[0] == SECRET+"install":
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open(settings["current_directory"]+'/'+'alias.sh', 'r') as alias_file:
                    self.wfile.write(str.encode(alias_file.read().replace("[url]", settings["url"])+"\n"))
            elif self.request_path[0] == "out" and len(self.request_path) == 2:
                self.send_response(200)
                self.send_header('Content-type', 'application/x-binary')
                self.end_headers()
                with open(settings["current_directory"]+'/'+'out/' + self.request_path[1], 'rb') as alias_file:
                    self.wfile.write(alias_file.read())
            elif self.request_path[0] == SECRET+"Github-ribbon.png":
                with open(settings["current_directory"]+'/'+'Github-ribbon.png', 'rb') as image:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/png')
                    self.end_headers()
                    self.wfile.write(image.read())
            elif os.path.exists(array_to_path(self.file_path)):
                with open(array_to_path(self.file_path), 'rb') as self.file:
                    # Load file stats
                    self.file.stat = os.fstat(self.file.fileno())
                    if self.option == "info":
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.response = "Name: {}\nSize: {}\nCountdown: {} \n"
                        self.file.countdown = round(((int(settings["delete_limit"]) * 3600) + self.file.stat.st_ctime) - time.time())
                        # Place data in response
                        self.response = self.response.format(self.request_path[-1], human_readable(self.file.stat.st_size), human_readable_time(self.file.countdown))
                        # Send response
                        self.wfile.write(str.encode(self.response))
                    else:
                        self.send_response(200)
                        self.send_header("Content-Type", 'application/octet-stream')
                        contentDisposition = 'attachment; filename="{}"'
                        contentDisposition = contentDisposition.format(self.request_path[-1])
                        self.send_header("Content-Disposition", contentDisposition)
                        self.send_header("Content-Length", str(self.file.stat.st_size))
                        self.end_headers()
                        shutil.copyfileobj(self.file, self.wfile)
                        # If user want deleted file after download
                        if self.option == "delete":
                            os.remove(array_to_path(self.file_path))
                            print("{} deleted !\n".format(array_to_path(self.file_path)))
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.response = "File not found \n"
                self.wfile.write(str.encode(self.response))
        # else:
        #     if "curl" in self.headers['User-Agent'].lower():
        #         self.send_response(200)
        #         self.send_header('Content-type', 'text/html')
        #         self.end_headers()
        #         with open(settings["current_directory"]+'/'+'help.txt', 'r') as help_file:
        #             self.wfile.write(str.encode(help_file.read().replace("[url]", settings["url"])+"\n"))
        #     else:
        #         # Open HTML homepage file
        #         with open(settings["current_directory"]+'/'+'index.html', 'r') as homepage:
        #             self.send_response(200)
        #             self.send_header('Content-type', 'text/html')
        #             self.end_headers()
        #             # Send HTML page with replaced data
        #             self.wfile.write(str.encode(homepage.read().replace("[url]", settings["url"])))
        return

    def do_PUT(self):  # For upload
        # Get the request size in header
        self.file_size = int(self.headers['Content-Length'])
        self.file_name = self.path.split("/")[-1]  # Only take the file name
        if len(self.file_name) > int(settings["max_name_length"]):  # Check file name length
            self.send_response(400)  # Send error header
            self.send_header('Content-type', 'text/plain')  # Send mime
            self.end_headers()  # Close header
            HTML_error = "Error: Too long file name (max {} chars)\n"
            HTML_error = HTML_error.format(settings["max_name_length"])
            self.wfile.write(str.encode(HTML_error))  # Return error
            return
        if self.file_size > int(settings["max_file_size"]):  # Check file size
            self.send_response(400)  # Send error header
            self.send_header('Content-type', 'text/plain')  # Send mime
            self.end_headers()  # Close header
            HTML_error = "Error: Too big file (max {})\n"
            HTML_error = HTML_error.format(human_readable(int(settings["max_file_size"])))
            self.wfile.write(str.encode(HTML_error))  # Return error
            return
        # Read content from request
        content = self.rfile.read(self.file_size)
        # Loop for generating uniq token
        while "Bad token":
            # Get random token from urandom
            random_token = binascii.hexlify(os.urandom(int(settings["id_length"]))).decode()
            # If directory not exist -> token free
            path_digest = hashlib.sha512(('/'+random_token+'/'+self.file_name).encode('utf-8')).hexdigest()
            if not os.path.isfile(array_to_path(directory+[path_digest])):
                break
        
        # Concat the new file full path
        self.file_path = directory+[path_digest]

        # Open tmp new file to write binary data
        current_file = open(array_to_path(self.file_path), "wb")
        # Write content of request
        current_file.write(content)
        current_file.close()

        self.send_response(200)  # Send success header
        self.send_header('Content-type', 'text/html')  # Send mime
        self.end_headers()  # Close header
        # Return new file url to user
        self.wfile.write(str.encode(settings["url"]+"/"+random_token+"/"+self.file_name+"\n"))
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def run_on(port):
    print("\n")
    print("/-------------------------------\\")
    print("|  Starting Pype on port {}  |".format(str(settings["port"]).rjust(5, " ")))
    print("\\-------------------------------/")
    print("\n")
    print("Reminder : \n")
    print("To upload   :      curl -T file.txt {}".format(settings["url"]))
    print("To download :      curl {}/[id]/file.txt > files.txt".format(settings["url"]))
    print("\n\nLogs : \n")
    server_address = (settings["listen_address"], int(settings["port"]))
    httpd = ThreadedHTTPServer(server_address, request_handler)
    httpd.serve_forever()


def human_readable(bytes):  # Convert bytes to human readable string format
    units = ['o', 'Ko', 'Mo', 'Go', 'To', 'Po']
    cursor = 0
    while bytes > 1024:
        bytes /= 1024
        cursor += 1
    value = str(bytes).split('.')
    value[1] = value[1][:2]
    value = '.'.join(value)
    return value+' '+units[cursor]


def human_readable_time(seconds):  # Convert time in seconds to human readable string format
    units = ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']
    maximum_values = [60, 60, 24, 7, 4, 12, 99]
    cursor = 0
    while seconds > maximum_values[cursor]:
        seconds /= maximum_values[cursor]
        cursor += 1
    value = math.ceil(seconds)
    unit = units[cursor]
    if float(value) > 1:
        unit += 's'
    return str(value)+' '+unit


def set_interval(func, time):
    e = threading.Event()
    while not e.wait(time):
        func()


def clean_files():
    # Create list of deleted files
    removed = []
    now = time.time()
    # Compute the limit_date from setings
    limit_date = now - (int(settings["delete_limit"]) * 3600)
    
    for file in os.listdir(array_to_path(directory)):
        if os.path.isfile(array_to_path(directory+[file])):
            # Get informations about this file
            stats = os.stat(array_to_path(directory+[file]))
            timestamp = stats.st_ctime
            if timestamp < limit_date:
                removed.append(file)
                os.remove(array_to_path(directory+[file]))

    if len(removed) > 0:
        print("Files removed : {}".format(', '.join(removed)))


if __name__ == "__main__":
    server = Thread(target=run_on, args=[int(settings["port"])])
    server.daemon = True
    server.start()
    initialisation()
    # Launch auto cleaning interval
    set_interval(clean_files, (int(settings["cleaning_interval"]) * 3600))
    signal.pause()
