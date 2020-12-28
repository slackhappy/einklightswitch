#!/usr/bin/python3
import sys
import argparse
import queue
from http.server import HTTPServer, SimpleHTTPRequestHandler
from PIL import Image

render_queue = queue.Queue(1)

class LightswitchRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            super().do_GET()
        else:
            self.send_response(404)

    def do_POST(self):
        if not self.path == '/image':
            self.send_response(404)
        img = Image.open(self.rfile)
        put(img)
        self.send_response(200)

class LightswitchImage:
    pass

def put(image):
    if (render_queue.full()):
        try:
            # attempt to steal the old item and throw away
            render_queue.get_nowait()
            render_queue.task_done()
        except queue.Empty:
            pass
    try:
        render_queue.put(image, False)
    except queue.Full:
        print('Could not enqueue image')


def run(args):
    server_address = ('', 8000) # INADDR_ANY, port 80
    handler =  LightswitchRequestHandler
    with HTTPServer(server_address, handler) as httpd:
        httpd.serve_forever()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="lightswitch http server")
    args = parser.parse_args()
    run(args)

    

