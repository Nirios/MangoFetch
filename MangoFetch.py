from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import subprocess
import threading
import sys
import os
import queue
import json
import uuid


# Add those to your browser bookmarks
# URLs for videos, with and without alert
# javascript:fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href)).then(r=>r.text()).then(alert)
# javascript:fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href))
# URLs for audio only, with and without alert
# javascript:fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href)+'&mode=audio').then(r=>r.text()).then(alert)
# javascript:fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href)+'&mode=audio')


REQUIRED_KEYS = ["port", "audio_path", "video_path"]
download_status = {}
pending_ids = []
current_id = [None]


try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    print(f"Error loading config.json: {e}")
    sys.exit(1)


missing = [k for k in REQUIRED_KEYS if k not in config or not config[k]]
if missing:
    print(f"Error: Missing or empty config keys: {', '.join(missing)}")
    sys.exit(1)


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
            break
        url, mode, download_id = item
        current_id[0] = download_id
        if download_id in pending_ids:
            pending_ids.remove(download_id)
        download_status[download_id] = "downloading"
        try:
            Handler.download_video(url, mode)
            download_status[download_id] = "completed"
        except Exception as e:
            download_status[download_id] = f"failed: {e}"
        current_id[0] = None
        download_queue.task_done()


worker_thread = threading.Thread(target=queue_worker, daemon=True)
worker_thread.start()


def delete_vtt_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".vtt"):
            file_path = os.path.join(directory, filename)

            try:
                os.remove(file_path)
                
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
        pass
        # if self.command != "OPTIONS":
        #     super().log_message(format, *args)


    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)

        if self.path.startswith("/status"):
            download_id = params.get("id", [None])[0]
            status = download_status.get(download_id, "unknown id")

            # Check if it's downloading
            if download_id == current_id[0]:
                # Show how many are left after this one
                pos = 1
                total = 1 + len(pending_ids)
                status += f" ({pos} of {total})"

            elif download_id in pending_ids:
                pos = 1 + pending_ids.index(download_id) + (1 if current_id[0] else 0)
                total = (1 if current_id[0] else 0) + len(pending_ids)
                status += f" ({pos} of {total})"

            elif status.startswith("completed") or status.startswith("failed"):
                pass  # No queue info needed

            else:
                status += " (not in queue)"

            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', 'https://www.youtube.com')
            self.end_headers()
            self.wfile.write(status.encode("utf-8"))
            return

        if 'url' in params:
            url = params['url'][0]
            mode = params.get('mode', ['video'])[0]
            download_id = str(uuid.uuid4())
            download_status[download_id] = "queued"
            pending_ids.append(download_id)
            download_queue.put((url, mode, download_id))
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', 'https://www.youtube.com')
            self.end_headers()
            self.wfile.write(f"Download queued. ID: {download_id}".encode("utf-8"))

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

