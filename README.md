# MangoFetch - YouTube Downloader Server

Smooth and tropical, just like your download experience.

This is a simple Python server that lets you queue YouTube video or audio downloads from your browser using a bookmarklet. It supports queueing, status reporting (including position in the queue), and automatically embeds thumbnails in MP3s. The download status is displayed directly on the YouTube page when you use the bookmarklet.

## MangoFetch Bookmarklets

**What is a bookmarklet?**  
A bookmarklet is a tiny JavaScript program saved as a bookmark in your browser’s bookmarks bar. When you’re on a page (like a YouTube video), you click the bookmarklet and it performs a special action—in this case, sending the video to your MangoFetch download server and showing a floating status box.

### How to add the MangoFetch bookmarklet

1. **Copy the code below for the bookmarklet you want.**
2. **Create a new bookmark** in your browser’s bookmarks bar.
3. **Paste the code** into the URL/location field of the bookmark.
4. **Name it** "MangoFetch Video" or "MangoFetch Audio".

#### MangoFetch Video

```
javascript:(function(){let old=document.getElementById('yt-dlp-status-box');if(old)old.remove();let box=document.createElement('div');box.id='yt-dlp-status-box';box.style.position='fixed';box.style.top='20px';box.style.right='20px';box.style.background='rgba(0,0,0,0.85)';box.style.color='#fff';box.style.padding='14px 20px';box.style.borderRadius='8px';box.style.zIndex=99999;box.style.fontSize='16px';box.style.boxShadow='0 2px 8px #0003';box.textContent='Sending download request...';document.body.appendChild(box);fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href)).then(r=>r.text()).then(function(t){let match=t.match(/ID:\s*([a-f0-9-]+)/i);if(!match){box.textContent='Server error: '+t;return;}let id=match[1];box.textContent='Download queued...';let poll=setInterval(function(){fetch('http://localhost:8000/status?id='+id).then(r=>r.text()).then(function(status){box.textContent='Download status: '+status;if(/completed|failed/i.test(status)){clearInterval(poll);box.textContent='Download status: '+status+' (This box will close in 10s)';setTimeout(()=>box.remove(),10000);}});},300);}).catch(e=>{box.textContent='Error: '+e;});})();
```

#### MangoFetch Audio

```
javascript:(function(){let old=document.getElementById('yt-dlp-status-box');if(old)old.remove();let box=document.createElement('div');box.id='yt-dlp-status-box';box.style.position='fixed';box.style.top='20px';box.style.right='20px';box.style.background='rgba(0,0,0,0.85)';box.style.color='#fff';box.style.padding='14px 20px';box.style.borderRadius='8px';box.style.zIndex=99999;box.style.fontSize='16px';box.style.boxShadow='0 2px 8px #0003';box.textContent='Sending download request...';document.body.appendChild(box);fetch('http://localhost:8000?url='+encodeURIComponent(window.location.href)+'&mode=audio').then(r=>r.text()).then(function(t){let match=t.match(/ID:\s*([a-f0-9-]+)/i);if(!match){box.textContent='Server error: '+t;return;}let id=match[1];box.textContent='Download queued...';let poll=setInterval(function(){fetch('http://localhost:8000/status?id='+id).then(r=>r.text()).then(function(status){box.textContent='Download status: '+status;if(/completed|failed/i.test(status)){clearInterval(poll);box.textContent='Download status: '+status+' (This box will close in 10s)';setTimeout(()=>box.remove(),10000);}});},300);}).catch(e=>{box.textContent='Error: '+e;});})();
```

## Features

- Download YouTube videos or extract audio as MP3 with embedded thumbnails.
- Queue multiple download requests; each request shows its position in the queue.
- Status reporting is displayed as a floating box directly on the YouTube page.
- Configurable download directories and server port via `config.json`.
- No browser extension required—just a bookmarklet.

## Requirements

- **[Python 3.9+](https://www.python.org/downloads/)**
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** (YouTube downloader)
- **[ffmpeg](https://ffmpeg.org/download.html)** (for audio extraction and thumbnail embedding)

## Installation

1. **Clone or download this repository.**

6. **Edit the `config.json` file to your preferred settings:**  
   ```
   {
     "port": 8000,
     "audio_path": "C:/yt-dlp/Music",
     "video_path": "C:/yt-dlp/Videos"
   }
   ```
   - Adjust the paths and port as you like.

## Usage

1. **Start the server:**
   ```
   py MangoFetch.py
   ```
   The server will print `Server running on port 8000`.

2. **Go to a YouTube video page and click the bookmarklet previously added.**
   - The download will be queued and you’ll see a floating status box showing progress and queue position.

3. **Downloaded files** will appear in the directories specified in your `config.json`.

## Notes

- Make sure the server is running before using the bookmarklet.
- The server only accepts requests from YouTube pages by default (CORS).
- If you use an adblocker or Brave browser, you may need to whitelist `localhost` for YouTube in your settings.
    - Add this line to your filters: `@@||localhost^$domain=youtube.com`
- For the program to work from anywhere, you should add both yt-dlp and ffmpeg to your system's PATH environment variable.
    This allows the server to call them without needing their full file paths.

    - On Windows, add the folders containing yt-dlp.exe and ffmpeg.exe to your PATH variable via System Properties → Environment Variables.

    - On Linux/macOS, make sure yt-dlp and ffmpeg are available in your terminal (which yt-dlp and which ffmpeg should return a path).

    If you don’t do this, you may get errors saying yt-dlp or ffmpeg are not found when downloading.

## Troubleshooting

- **"Failed to fetch" error:**  
  - Make sure the server is running and accessible at the configured port.
  - Check that firewall or antivirus is not blocking `localhost:8000`.
- **MP3s missing album art:**  
  - Ensure `ffmpeg` is installed and in your system PATH.

