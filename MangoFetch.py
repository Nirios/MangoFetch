from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import subprocess
import threading
import os
import queue
import json


# Add those to your browser bookmarks
# URLs for videos, with and without alert
# javascript:fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href)).then(r=>r.text()).then(alert)
# javascript:fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href))
# URLs for audio only, with and without alert
# javascript:fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href)+'&mode=audio').then(r=>r.text()).then(alert)
# javascript:fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href)+'&mode=audio')


with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


def ensure_trailing_sep(path):
    return path if path.endswith(os.sep) else path + os.sep


PORT = config["port"]
audio_path = ensure_trailing_sep(config["audio_path"])
video_path = ensure_trailing_sep(config["video_path"])
os.makedirs(audio_path, exist_ok=True)
os.makedirs(video_path, exist_ok=True)


download_queue = queue.Queue()
def queue_worker():
    while True:
        item = download_queue.get()
        if item is None:
            break  # Allows for clean shutdown if you ever want it
        url, mode = item
        Handler.download_video(url,mode)
        download_queue.task_done()


worker_thread = threading.Thread(target=queue_worker, daemon=True)
worker_thread.start()


def delete_vtt_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".vtt"):
            file_path = os.path.join(directory, filename)
            try:
                os.remove(file_path)
                # print(f"Deleted subtitle file: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")


class Handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', 'https://www.youtube.com')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()


    def log_message(self, format, *args):
        if self.command != "OPTIONS":
            super().log_message(format, *args)


    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'url' in params:
            url = params['url'][0]
            mode = params.get('mode', ['video'])[0]
            download_queue.put((url,mode))
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', 'https://www.youtube.com')
            self.end_headers()
            self.wfile.write(b'Download started')

        else:
            self.send_response(400)
            self.send_header('Access-Control-Allow-Origin', 'https://www.youtube.com')
            self.end_headers()


    @staticmethod
    def get_video_title(url):

        result = subprocess.run(
            ["yt-dlp", "--get-title", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

        return result.stdout.strip() if result.returncode == 0 else "Unknown Title"


    @staticmethod
    def download_video(url, mode):
        title = Handler.get_video_title(url)

        if mode == "audio":
            subprocess.run([
                "yt-dlp",
                "-o", f"{audio_path}%(title)s.%(ext)s",
                "-f", "bestaudio/best",
                "--sponsorblock-remove", "music_offtopic",
                "-x", "--audio-format", "mp3",
                "--embed-thumbnail",
                "--add-metadata",
                url
            ])
        
        else:
            subprocess.run([
                "yt-dlp",
                "-o", f"{video_path}%(title)s.%(ext)s",
                "--write-subs",
                "--sub-lang", "en.*",
                "--embed-subs",
                "-f", "bestvideo+bestaudio/best",
                url
            ])

            delete_vtt_files(video_path)

        print(f"Download finished for: {title} ({url})")
        print(f"\n" + " "*20 + "-"*80)
        print()


if __name__ == '__main__':

    server = HTTPServer(('localhost', PORT), Handler)
    print(f"Server running on port {PORT}")
    server.serve_forever()

