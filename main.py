#!/usr/bin/python3
import argparse
import glob
import io
import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from render import ImageProcessor
from PIL import Image

logger = logging.getLogger(__name__)

render_queue = queue.Queue(1)


class LightswitchRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(format, *args)

    def log_error(self, format, *args):
        logger.error(format, *args)

    def do_GET(self):
        if self.path == "/":
            super().do_GET()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if not self.path == "/image":
            self.send_response(404)
            self.end_headers()
        try:
            mimetype = self.headers.get("Content-Type", "")
            length = int(self.headers.get("Content-Length", "0"))
            logger.debug("mimetype %s len %s", mimetype, length)
            image_bytes_fp = io.BytesIO(self.rfile.read(length))
            timestamp = datetime.fromtimestamp(int(time.time()))
            img = Image.open(image_bytes_fp)
            img.filename = timestamp.isoformat()
            put(img)
            self.send_response(200)
            self.end_headers()
        except:
            logger.exception("failed post to /image")
            self.send_response(500)
            self.end_headers()


def put(image):
    logger.debug("putting 1")
    if render_queue.full():
        logger.debug("full")
        try:
            # attempt to steal the old item and throw away
            render_queue.get_nowait()
            render_queue.task_done()
        except queue.Empty:
            pass
    try:
        logger.debug("putting 2")
        render_queue.put(image, False)
    except queue.Full:
        print("Could not enqueue image")


def worker(savedir, epd):
    os.makedirs(savedir, exist_ok=True)
    processor = ImageProcessor(savedir)
    while True:
        image = render_queue.get()
        logger.debug("got an image")
        processor.save(image)
        logger.debug("quantizing")
        quantized = processor.quantize_3color(image)
        processor.save(quantized)
        logger.debug("separating")
        (b, r) = processor.separate_3color(quantized)
        processor.save(b)
        processor.save(r)
        if epd:
            logger.debug("displaying")
            epd.display(epd.getbuffer(b), epd.getbuffer(r))
            logger.debug("done")
        render_queue.task_done()


def run(args, epd):
    savedir = args.dir

    # turn-on the worker thread
    threading.Thread(target=worker, args=(savedir, epd), daemon=True).start()

    server_address = ("", args.port)  # INADDR_ANY, port 80
    handler = LightswitchRequestHandler

    if epd:
        logger.info("initializing device")
        epd.init()
        epd.Clear()

    try:
        with HTTPServer(server_address, handler) as httpd:
            logger.info("Server up on port %s", args.port)
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutting down, draining queue")
        render_queue.join()
        if epd:
            logger.info("stopping device")
            epd.Dev_exit()
        logger.info("done")


if __name__ == "__main__":
    devices = sorted(
        [os.path.basename(x)[:-3] for x in glob.glob("lib/waveshare_epd/epd*.py")]
    )
    parser = argparse.ArgumentParser(description="lightswitch http server")
    parser.add_argument("--debug", action="store_true", help="debug logging")
    parser.add_argument("--dir", default="img", help="savedir for images")
    parser.add_argument(
        "--port", type=int, default=8000, help="port to run server on (default 8000)"
    )
    parser.add_argument(
        "--device",
        default="",
        help="device to use. default none, supported: " + ",".join(devices),
    )
    args = parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s %(levelname)s: %(message)s",
        level=(logging.DEBUG if args.debug else logging.INFO),
    )

    epd = None
    if args.device:
        libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
        print(libdir)
        sys.path.append(os.path.join(libdir))
        try:
            module = getattr(__import__("waveshare_epd", fromlist=(args.device,)), args.device)
        except:
            logger.exception("Failed to load device %s", args.device)
            raise
        epd = module.EPD()
        logger.info("initialized device %s", args.device)

    run(args, epd)
