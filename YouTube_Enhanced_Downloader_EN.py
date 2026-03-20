import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import yt_dlp
import threading
import os
import tempfile
import subprocess
import webbrowser
import sys
from tkinter import filedialog
import urllib.parse
import re

class YouTubeEnhancedGUI_EN:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Music/Video Downloader & Player")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Variables
        self.videos = []
        self.selected_video = None
        self.download_thread = None
        self.stream_thread = None
        self.url_thread = None
        self.temp_files = []
        self.cancel_requested = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎵 YouTube Music/Video Downloader & Streaming Player", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # URL Input section
        url_frame = ttk.LabelFrame(main_frame, text="🔗 URL Input", padding="10")
        url_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Arial', 11))
        url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        url_entry.bind('<Return>', lambda e: self.process_url())
        
        url_btn = ttk.Button(url_frame, text="Process URL", command=self.process_url)
        url_btn.grid(row=0, column=1, padx=5)
        
        cancel_btn = ttk.Button(url_frame, text="Cancel", command=self.cancel_url_processing)
        cancel_btn.grid(row=0, column=2, padx=5)
        
        # Search section
        search_frame = ttk.LabelFrame(main_frame, text="🔍 Search", padding="10")
        search_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(0, weight=1)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 11))
        search_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        search_entry.bind('<Return>', lambda e: self.search_videos())
        
        search_btn = ttk.Button(search_frame, text="Search", command=self.search_videos)
        search_btn.grid(row=0, column=1, padx=5)
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="📋 Results", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Create treeview for results
        columns = ('Title', 'Channel', 'Duration', 'Views')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='tree headings', height=8)
        
        # Configure columns
        self.results_tree.heading('#0', text='#')
        self.results_tree.heading('Title', text='Title')
        self.results_tree.heading('Channel', text='Channel')
        self.results_tree.heading('Duration', text='Duration')
        self.results_tree.heading('Views', text='Views')
        
        self.results_tree.column('#0', width=40)
        self.results_tree.column('Title', width=300)
        self.results_tree.column('Channel', width=150)
        self.results_tree.column('Duration', width=80)
        self.results_tree.column('Views', width=80)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Action options
        action_frame = ttk.LabelFrame(main_frame, text="🎯 Action Options", padding="10")
        action_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        action_frame.columnconfigure(1, weight=1)
        
        # Format selection
        ttk.Label(action_frame, text="Format:").grid(row=0, column=0, sticky=tk.W)
        
        self.format_var = tk.StringVar(value="audio")
        audio_radio = ttk.Radiobutton(action_frame, text="🎵 Audio (MP3)", 
                                      variable=self.format_var, value="audio")
        audio_radio.grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        
        video_radio = ttk.Radiobutton(action_frame, text="🎬 Video (MP4)", 
                                      variable=self.format_var, value="video")
        video_radio.grid(row=0, column=2, sticky=tk.W)
        
        # Action selection
        ttk.Label(action_frame, text="Action:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        self.action_var = tk.StringVar(value="stream")
        stream_radio = ttk.Radiobutton(action_frame, text="🎧 Stream Play", 
                                       variable=self.action_var, value="stream")
        stream_radio.grid(row=1, column=1, sticky=tk.W, padx=(10, 20), pady=(10, 0))
        
        download_radio = ttk.Radiobutton(action_frame, text="💾 Download", 
                                        variable=self.action_var, value="download")
        download_radio.grid(row=1, column=2, sticky=tk.W, pady=(10, 0))
        
        # Action buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        stream_btn = ttk.Button(button_frame, text="▶️ Stream Play", 
                               command=self.stream_media, style='Accent.TButton')
        stream_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        download_btn = ttk.Button(button_frame, text="⬇️ Download", 
                                command=self.download_video)
        download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Player controls
        player_frame = ttk.LabelFrame(main_frame, text="🎮 Player Controls", padding="10")
        player_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        player_frame.columnconfigure(1, weight=1)
        
        self.playback_status = tk.StringVar(value="Not Playing")
        status_label = ttk.Label(player_frame, textvariable=self.playback_status, font=('Arial', 9))
        status_label.grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding="10")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, font=('Arial', 9))
        progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, font=('Arial', 8))
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def format_duration(self, duration):
        """Convert seconds to readable format"""
        if not duration:
            return "Unknown"
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def format_views(self, view_count):
        """Format view count"""
        if not view_count:
            return "Unknown"
        if view_count >= 1000000:
            return f"{view_count/1000000:.1f}M"
        elif view_count >= 1000:
            return f"{view_count/1000:.1f}K"
        else:
            return str(view_count)
    
    def validate_youtube_url(self, url):
        """Validate YouTube URL format"""
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube\.com/(watch\?v=|embed/|v/)|youtu\.be/|m\.youtube\.com/watch\?v=)([a-zA-Z0-9_-]{11})'
        )
        return bool(youtube_regex.match(url))
    
    def process_url(self):
        """Process direct URL input"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL!")
            return
        
        # Validate URL format
        if not self.validate_youtube_url(url):
            messagebox.showerror("URL Error", 
                "Invalid YouTube URL format!\n\nSupported formats:\n" +
                "• https://www.youtube.com/watch?v=VIDEO_ID\n" +
                "• https://youtu.be/VIDEO_ID\n" +
                "• https://m.youtube.com/watch?v=VIDEO_ID\n\n" +
                "Make sure the URL contains an 11-digit video ID")
            return
        
        # Check if already processing
        if self.url_thread and self.url_thread.is_alive():
            messagebox.showwarning("Warning", "Already processing URL!")
            return
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.videos = []
        self.cancel_requested = False
        self.progress_var.set(f"🔗 Processing URL: {url[:50]}...")
        self.progress_bar.start()
        self.status_var.set("Processing URL...")
        
        # Run URL processing in separate thread with timeout
        self.url_thread = threading.Thread(target=self._process_url_thread, args=(url,))
        self.url_thread.daemon = True
        self.url_thread.start()
        
        # Schedule timeout check
        self.root.after(30000, self._check_url_timeout)  # 30 second timeout
    
    def cancel_url_processing(self):
        """Cancel URL processing"""
        self.cancel_requested = True
        self.progress_var.set("⏹️ Cancelling...")
        self.status_var.set("Cancelling")
        self.progress_bar.stop()
        
        if self.url_thread and self.url_thread.is_alive():
            # Note: We can't forcefully kill a thread in Python, but we can set a flag
            messagebox.showinfo("Cancel", "URL processing cancellation requested. Please wait for current operation to complete.")
    
    def _check_url_timeout(self):
        """Check if URL processing has timed out"""
        if self.url_thread and self.url_thread.is_alive():
            if not self.cancel_requested:
                self.progress_bar.stop()
                self.progress_var.set("⏰ URL Processing Timeout!")
                self.status_var.set("Processing Timeout")
                messagebox.showwarning("Timeout", "URL processing timed out! Please try:\n1. Check network connection\n2. Verify URL is correct\n3. Try again later")
    
    def _process_url_thread(self, url):
        """Process URL in separate thread"""
        try:
            # Check for cancellation before starting
            if self.cancel_requested:
                return
            
            # Update progress
            self.root.after(0, lambda: self.progress_var.set(f"🔗 Connecting to YouTube: {url[:50]}..."))
            
            # Try simpler approach first
            ydl_opts = {
                'quiet': False,  # Enable verbose output for debugging
                'skip_download': True,
                'no_warnings': False,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'extract_flat': False,
                'no_check_certificate': True,
                'socket_timeout': 10,
                'retries': 2,
            }
            
            self.root.after(0, lambda: self.progress_var.set("🔍 Extracting video info..."))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Test basic extraction first
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as extract_error:
                    self.root.after(0, lambda: self.progress_var.set(f"❌ Extraction failed: {str(extract_error)[:100]}"))
                    raise extract_error
            
            # Check for cancellation after processing
            if self.cancel_requested:
                return
            
            # Validate the extracted info
            if not info:
                raise Exception("Unable to get video information")
            
            if 'title' not in info:
                raise Exception("Incomplete video information")
            
            # Update UI in main thread
            self.root.after(0, self._display_single_result, info)
            
        except Exception as e:
            if not self.cancel_requested:
                error_msg = str(e)
                print(f"URL Processing Error: {error_msg}")  # Debug print
                
                # Categorize errors
                if "HTTP Error 404" in error_msg:
                    error_msg = "❌ Video not found or URL error\nPlease check if the URL is correct"
                elif "HTTP Error 403" in error_msg:
                    error_msg = "❌ Access denied\nVideo may be region-restricted or require login"
                elif "bot" in error_msg.lower() or "captcha" in error_msg.lower():
                    error_msg = "❌ YouTube detected bot behavior\nPlease try again later or use a different video"
                elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    error_msg = "❌ Connection timeout\nPlease check your network connection"
                elif "Private video" in error_msg:
                    error_msg = "❌ Private video\nCannot access private content"
                elif "Video unavailable" in error_msg:
                    error_msg = "❌ Video unavailable\nVideo may have been deleted or set to private"
                else:
                    error_msg = f"❌ Processing failed\n{error_msg[:200]}"
                
                self.root.after(0, self._search_error, error_msg)
    
    def _display_single_result(self, video):
        """Display single video from URL"""
        self.progress_bar.stop()
        
        if not video:
            self.progress_var.set("❌ Unable to process URL!")
            self.status_var.set("URL processing failed")
            messagebox.showerror("Error", "Unable to process this URL!")
            return
        
        self.videos = [video]
        
        title = video.get('title', 'Unknown Title')[:60]
        if len(video.get('title', '')) > 60:
            title += "..."
        
        channel = video.get('uploader', 'Unknown Channel')[:20]
        duration = self.format_duration(video.get('duration'))
        views = self.format_views(video.get('view_count'))
        
        self.results_tree.insert('', 'end', text='1', 
                               values=(title, channel, duration, views))
        
        self.progress_var.set(f"✅ URL processing complete: {title}")
        self.status_var.set("URL processing complete")
    
    def search_videos(self):
        """Search for videos on YouTube"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter search keywords!")
            return
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.videos = []
        self.progress_var.set(f"🔎 Searching: {query}")
        self.progress_bar.start()
        self.status_var.set("Searching...")
        
        # Run search in separate thread
        thread = threading.Thread(target=self._perform_search, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _perform_search(self, query):
        """Perform the actual search"""
        try:
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'no_check_certificate': True,
                'socket_timeout': 30,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch10:{query}", download=False)
            
            videos = results.get('entries', [])
            
            # Update UI in main thread
            self.root.after(0, self._display_results, videos)
            
        except Exception as e:
            error_msg = str(e)
            if "HTTP Error" in error_msg or "bot" in error_msg.lower() or "captcha" in error_msg.lower():
                error_msg = "YouTube detected bot behavior, please try again later"
            self.root.after(0, self._search_error, error_msg)
    
    def _display_results(self, videos):
        """Display search results"""
        self.progress_bar.stop()
        
        if not videos:
            self.progress_var.set("❌ No results found!")
            self.status_var.set("No results")
            messagebox.showinfo("Info", "No results found! Please try other keywords.")
            return
        
        self.videos = videos
        
        for i, video in enumerate(videos, 1):
            title = video.get('title', 'Unknown Title')[:60]
            if len(video.get('title', '')) > 60:
                title += "..."
            
            channel = video.get('uploader', 'Unknown Channel')[:20]
            duration = self.format_duration(video.get('duration'))
            views = self.format_views(video.get('view_count'))
            
            self.results_tree.insert('', 'end', text=str(i), 
                                   values=(title, channel, duration, views))
        
        self.progress_var.set(f"📋 Found {len(videos)} results")
        self.status_var.set(f"Found {len(videos)} videos")
    
    def _search_error(self, error_msg):
        """Handle search error"""
        self.progress_bar.stop()
        self.progress_var.set(f"❌ Search error: {error_msg}")
        self.status_var.set("Search failed")
        messagebox.showerror("Search Error", f"Search failed: {error_msg}")
    
    def stream_media(self):
        """Stream selected media without downloading"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to play!")
            return
        
        if not self.videos:
            messagebox.showwarning("Warning", "No videos available! Please search or enter URL first.")
            return
        
        # Get selected video
        item = self.results_tree.item(selection[0])
        video_index = int(item['text']) - 1
        
        if 0 <= video_index < len(self.videos):
            self.selected_video = self.videos[video_index]
            
            # Check if already streaming
            if self.stream_thread and self.stream_thread.is_alive():
                messagebox.showwarning("Warning", "Already playing!")
                return
            
            # Start streaming
            format_type = self.format_var.get()
            self.stream_thread = threading.Thread(target=self._stream_media, args=(format_type,))
            self.stream_thread.daemon = True
            self.stream_thread.start()
    
    def _stream_media(self, format_type):
        """Perform the actual streaming"""
        try:
            url = self.selected_video['webpage_url']
            title = self.selected_video.get('title', 'Video')
            
            self.root.after(0, self._stream_start, title)
            
            # Create temporary file for streaming
            temp_dir = tempfile.gettempdir()
            temp_filename = f"temp_{hash(url) % 1000000}"
            
            # Configure streaming options with bot detection bypass
            ydl_opts = {
                'quiet': False,
                'no_warnings': False,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'no_check_certificate': True,
                'socket_timeout': 60,
                'retries': 3,
                'fragment_retries': 3,
            }
            
            if format_type == 'audio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, f"{temp_filename}.%(ext)s"),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'keepvideo': False,
                })
            else:
                ydl_opts.update({
                    'format': 'best[height<=720]/best',
                    'outtmpl': os.path.join(temp_dir, f"{temp_filename}.%(ext)s"),
                    'keepvideo': False,
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                # Apply post-processing if needed
                if format_type == 'audio':
                    # The actual file might be different after post-processing
                    for file in os.listdir(temp_dir):
                        if file.startswith(temp_filename) and file.endswith('.mp3'):
                            downloaded_file = os.path.join(temp_dir, file)
                            break
            
            self.temp_files.append(downloaded_file)
            
            # Open with system default player
            self.root.after(0, self._play_file, downloaded_file, title)
            
        except Exception as e:
            error_msg = str(e)
            if "HTTP Error" in error_msg or "bot" in error_msg.lower() or "captcha" in error_msg.lower():
                error_msg = f"Streaming failed - YouTube detected bot behavior\nPlease try:\n1. Try again later\n2. Select a different video\n3. Use download function\n\nOriginal error: {error_msg}"
            self.root.after(0, self._stream_error, error_msg)
    
    def _stream_start(self, title):
        """Update UI when streaming starts"""
        format_type = "🎵 Audio" if self.format_var.get() == 'audio' else "🎬 Video"
        self.progress_var.set(f"{format_type} Preparing stream: {title}")
        self.progress_bar.start()
        self.status_var.set("Preparing stream...")
        self.playback_status.set("Preparing...")
    
    def _play_file(self, filepath, title):
        """Play the downloaded file"""
        try:
            self.progress_bar.stop()
            self.progress_var.set(f"🎧 Now playing: {title}")
            self.status_var.set("Playing")
            self.playback_status.set(f"Playing: {title[:30]}...")
            
            # Open with system default player
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.Popen(['open', filepath] if sys.platform == 'darwin' else ['xdg-open', filepath])
            
            messagebox.showinfo("Playback", f"Now playing: {title}\nFile will open in your system's default player")
            
        except Exception as e:
            self.progress_var.set(f"❌ Playback error: {str(e)}")
            self.status_var.set("Playback failed")
            self.playback_status.set("Playback failed")
    
    def _stream_error(self, error_msg):
        """Handle streaming error"""
        self.progress_bar.stop()
        self.progress_var.set(f"❌ Streaming error: {error_msg}")
        self.status_var.set("Streaming failed")
        self.playback_status.set("Streaming failed")
        messagebox.showerror("Streaming Error", f"Streaming failed: {error_msg}")
    
    def download_video(self):
        """Download selected video"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a video to download!")
            return
        
        if not self.videos:
            messagebox.showwarning("Warning", "No videos available! Please search or enter URL first.")
            return
        
        # Get selected video
        item = self.results_tree.item(selection[0])
        video_index = int(item['text']) - 1
        
        if 0 <= video_index < len(self.videos):
            self.selected_video = self.videos[video_index]
            
            # Check if already downloading
            if self.download_thread and self.download_thread.is_alive():
                messagebox.showwarning("Warning", "Already downloading!")
                return
            
            # Start download
            format_type = self.format_var.get()
            self.download_thread = threading.Thread(target=self._download_video, args=(format_type,))
            self.download_thread.daemon = True
            self.download_thread.start()
    
    def _download_video(self, format_type):
        """Perform the actual download"""
        try:
            url = self.selected_video['webpage_url']
            title = self.selected_video.get('title', 'Video')
            
            self.root.after(0, self._download_start, title)
            
            # Configure download options with bot detection bypass
            ydl_opts = {
                'quiet': False,
                'no_warnings': False,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'no_check_certificate': True,
                'socket_timeout': 60,
                'retries': 3,
                'fragment_retries': 3,
                'progress_hooks': [self._progress_hook],
            }
            
            if format_type == 'audio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'outtmpl': '%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                ydl_opts.update({
                    'format': 'best[height<=720]/best',
                    'outtmpl': '%(title)s.%(ext)s',
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            self.root.after(0, self._download_complete)
            
        except Exception as e:
            error_msg = str(e)
            if "HTTP Error" in error_msg or "bot" in error_msg.lower() or "captcha" in error_msg.lower():
                error_msg = f"Download failed - YouTube detected bot behavior\nPlease try:\n1. Try again later\n2. Select a different video\n3. Check network connection\n\nOriginal error: {error_msg}"
            self.root.after(0, self._download_error, error_msg)
    
    def _download_start(self, title):
        """Update UI when download starts"""
        format_type = "🎵 Audio" if self.format_var.get() == 'audio' else "🎬 Video"
        self.progress_var.set(f"{format_type} Downloading: {title}")
        self.progress_bar.start()
        self.status_var.set("Downloading...")
    
    def _progress_hook(self, d):
        """Download progress callback"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()
            progress_text = f"⬇️ {percent} | 🚀 {speed} | ⏱️ {eta}"
            self.root.after(0, self._update_progress, progress_text)
        elif d['status'] == 'finished':
            filename = d.get('filename', 'Unknown file')
            self.root.after(0, self._update_progress, f"✅ Processing: {os.path.basename(filename)}")
    
    def _update_progress(self, text):
        """Update progress text"""
        self.progress_var.set(text)
    
    def _download_complete(self):
        """Handle download completion"""
        self.progress_bar.stop()
        self.progress_var.set("✅ Download complete!")
        self.status_var.set("Download complete")
        messagebox.showinfo("Success", "Download completed successfully!")
    
    def _download_error(self, error_msg):
        """Handle download error"""
        self.progress_bar.stop()
        self.progress_var.set(f"❌ Download failed: {error_msg}")
        self.status_var.set("Download failed")
        messagebox.showerror("Download Error", f"Download failed: {error_msg}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        self.temp_files.clear()
    
    def __del__(self):
        """Cleanup on exit"""
        self.cleanup_temp_files()

def main():
    root = tk.Tk()
    app = YouTubeEnhancedGUI_EN(root)
    
    # Handle window closing
    def on_closing():
        app.cleanup_temp_files()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
