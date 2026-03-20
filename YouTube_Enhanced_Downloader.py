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

class YouTubeEnhancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube音乐/视频下载器 & 播放器")
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
        title_label = ttk.Label(main_frame, text="🎵 YouTube音乐/视频下载器 & 流媒体播放器", 
                               font=('Microsoft YaHei', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # URL Input section
        url_frame = ttk.LabelFrame(main_frame, text="🔗 URL输入", padding="10")
        url_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=('Microsoft YaHei', 11))
        url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        url_entry.bind('<Return>', lambda e: self.process_url())
        
        url_btn = ttk.Button(url_frame, text="处理URL", command=self.process_url)
        url_btn.grid(row=0, column=1, padx=5)
        
        cancel_btn = ttk.Button(url_frame, text="取消", command=self.cancel_url_processing)
        cancel_btn.grid(row=0, column=2, padx=5)
        
        # Search section
        search_frame = ttk.LabelFrame(main_frame, text="🔍 搜索", padding="10")
        search_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(0, weight=1)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Microsoft YaHei', 11))
        search_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        search_entry.bind('<Return>', lambda e: self.search_videos())
        
        search_btn = ttk.Button(search_frame, text="搜索", command=self.search_videos)
        search_btn.grid(row=0, column=1, padx=5)
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="📋 结果", padding="10")
        results_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Create treeview for results
        columns = ('Title', 'Channel', 'Duration', 'Views')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='tree headings', height=8)
        
        # Configure columns
        self.results_tree.heading('#0', text='序号')
        self.results_tree.heading('Title', text='标题')
        self.results_tree.heading('Channel', text='频道')
        self.results_tree.heading('Duration', text='时长')
        self.results_tree.heading('Views', text='观看次数')
        
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
        action_frame = ttk.LabelFrame(main_frame, text="🎯 操作选项", padding="10")
        action_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        action_frame.columnconfigure(1, weight=1)
        
        # Format selection
        ttk.Label(action_frame, text="格式:").grid(row=0, column=0, sticky=tk.W)
        
        self.format_var = tk.StringVar(value="audio")
        audio_radio = ttk.Radiobutton(action_frame, text="🎵 音频 (MP3)", 
                                      variable=self.format_var, value="audio")
        audio_radio.grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        
        video_radio = ttk.Radiobutton(action_frame, text="🎬 视频 (MP4)", 
                                      variable=self.format_var, value="video")
        video_radio.grid(row=0, column=2, sticky=tk.W)
        
        # Action selection
        ttk.Label(action_frame, text="操作:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        self.action_var = tk.StringVar(value="stream")
        stream_radio = ttk.Radiobutton(action_frame, text="🎧 流媒体播放", 
                                       variable=self.action_var, value="stream")
        stream_radio.grid(row=1, column=1, sticky=tk.W, padx=(10, 20), pady=(10, 0))
        
        download_radio = ttk.Radiobutton(action_frame, text="💾 下载", 
                                        variable=self.action_var, value="download")
        download_radio.grid(row=1, column=2, sticky=tk.W, pady=(10, 0))
        
        # Action buttons
        button_frame = ttk.Frame(action_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        stream_btn = ttk.Button(button_frame, text="▶️ 流媒体播放", 
                               command=self.stream_media, style='Accent.TButton')
        stream_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        download_btn = ttk.Button(button_frame, text="⬇️ 下载", 
                                command=self.download_video)
        download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Player controls
        player_frame = ttk.LabelFrame(main_frame, text="🎮 播放器控制", padding="10")
        player_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        player_frame.columnconfigure(1, weight=1)
        
        self.playback_status = tk.StringVar(value="未播放")
        status_label = ttk.Label(player_frame, textvariable=self.playback_status, font=('Microsoft YaHei', 9))
        status_label.grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="📊 进度", padding="10")
        progress_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="准备就绪...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var, font=('Microsoft YaHei', 9))
        progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, font=('Microsoft YaHei', 8))
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def format_duration(self, duration):
        """Convert seconds to readable format"""
        if not duration:
            return "未知"
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
            return "未知"
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
            messagebox.showwarning("警告", "请输入URL！")
            return
        
        # Validate URL format
        if not self.validate_youtube_url(url):
            messagebox.showerror("URL错误", 
                "无效的YouTube URL格式！\n\n支持的格式：\n" +
                "• https://www.youtube.com/watch?v=VIDEO_ID\n" +
                "• https://youtu.be/VIDEO_ID\n" +
                "• https://m.youtube.com/watch?v=VIDEO_ID\n\n" +
                "请确保URL包含11位的视频ID")
            return
        
        # Check if already processing
        if self.url_thread and self.url_thread.is_alive():
            messagebox.showwarning("警告", "正在处理URL中！")
            return
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.videos = []
        self.cancel_requested = False
        self.progress_var.set(f"🔗 处理URL: {url[:50]}...")
        self.progress_bar.start()
        self.status_var.set("处理URL中...")
        
        # Run URL processing in separate thread with timeout
        self.url_thread = threading.Thread(target=self._process_url_thread, args=(url,))
        self.url_thread.daemon = True
        self.url_thread.start()
        
        # Schedule timeout check
        self.root.after(30000, self._check_url_timeout)  # 30 second timeout
    
    def cancel_url_processing(self):
        """Cancel URL processing"""
        self.cancel_requested = True
        self.progress_var.set("⏹️ 正在取消...")
        self.status_var.set("取消中")
        self.progress_bar.stop()
        
        if self.url_thread and self.url_thread.is_alive():
            # Note: We can't forcefully kill a thread in Python, but we can set a flag
            messagebox.showinfo("取消", "URL处理已请求取消，请等待当前操作完成")
    
    def _check_url_timeout(self):
        """Check if URL processing has timed out"""
        if self.url_thread and self.url_thread.is_alive():
            if not self.cancel_requested:
                self.progress_bar.stop()
                self.progress_var.set("⏰ URL处理超时！")
                self.status_var.set("处理超时")
                messagebox.showwarning("超时", "URL处理超时！请尝试：\n1. 检查网络连接\n2. 验证URL是否正确\n3. 稍后重试")
    
    def _process_url_thread(self, url):
        """Process URL in separate thread"""
        try:
            # Check for cancellation before starting
            if self.cancel_requested:
                return
            
            # Update progress
            self.root.after(0, lambda: self.progress_var.set(f"🔗 正在连接YouTube: {url[:50]}..."))
            
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
            
            self.root.after(0, lambda: self.progress_var.set("🔍 正在提取视频信息..."))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Test basic extraction first
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as extract_error:
                    self.root.after(0, lambda: self.progress_var.set(f"❌ 提取失败: {str(extract_error)[:100]}"))
                    raise extract_error
            
            # Check for cancellation after processing
            if self.cancel_requested:
                return
            
            # Validate the extracted info
            if not info:
                raise Exception("无法获取视频信息")
            
            if 'title' not in info:
                raise Exception("视频信息不完整")
            
            # Update UI in main thread
            self.root.after(0, self._display_single_result, info)
            
        except Exception as e:
            if not self.cancel_requested:
                error_msg = str(e)
                print(f"URL Processing Error: {error_msg}")  # Debug print
                
                # Categorize errors
                if "HTTP Error 404" in error_msg:
                    error_msg = "❌ 视频不存在或URL错误\n请检查URL是否正确"
                elif "HTTP Error 403" in error_msg:
                    error_msg = "❌ 访问被拒绝\n视频可能受地区限制或需要登录"
                elif "bot" in error_msg.lower() or "captcha" in error_msg.lower():
                    error_msg = "❌ YouTube检测到机器人行为\n请稍后重试或使用其他视频"
                elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    error_msg = "❌ 连接超时\n请检查网络连接"
                elif "Private video" in error_msg:
                    error_msg = "❌ 私人视频\n无法访问私人内容"
                elif "Video unavailable" in error_msg:
                    error_msg = "❌ 视频不可用\n视频可能已被删除或设为私人"
                else:
                    error_msg = f"❌ 处理失败\n{error_msg[:200]}"
                
                self.root.after(0, self._search_error, error_msg)
    
    def _display_single_result(self, video):
        """Display single video from URL"""
        self.progress_bar.stop()
        
        if not video:
            self.progress_var.set("❌ 无法处理URL！")
            self.status_var.set("URL处理失败")
            messagebox.showerror("错误", "无法处理此URL！")
            return
        
        self.videos = [video]
        
        title = video.get('title', '未知标题')[:60]
        if len(video.get('title', '')) > 60:
            title += "..."
        
        channel = video.get('uploader', '未知频道')[:20]
        duration = self.format_duration(video.get('duration'))
        views = self.format_views(video.get('view_count'))
        
        self.results_tree.insert('', 'end', text='1', 
                               values=(title, channel, duration, views))
        
        self.progress_var.set(f"✅ URL处理完成: {title}")
        self.status_var.set("URL处理完成")
    
    def search_videos(self):
        """Search for videos on YouTube"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("警告", "请输入搜索关键词！")
            return
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.videos = []
        self.progress_var.set(f"🔎 正在搜索: {query}")
        self.progress_bar.start()
        self.status_var.set("搜索中...")
        
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
                error_msg = "YouTube检测到机器人行为，请稍后重试"
            self.root.after(0, self._search_error, error_msg)
    
    def _display_results(self, videos):
        """Display search results"""
        self.progress_bar.stop()
        
        if not videos:
            self.progress_var.set("❌ 未找到结果！")
            self.status_var.set("无结果")
            messagebox.showinfo("信息", "未找到结果！请尝试其他关键词。")
            return
        
        self.videos = videos
        
        for i, video in enumerate(videos, 1):
            title = video.get('title', '未知标题')[:60]
            if len(video.get('title', '')) > 60:
                title += "..."
            
            channel = video.get('uploader', '未知频道')[:20]
            duration = self.format_duration(video.get('duration'))
            views = self.format_views(video.get('view_count'))
            
            self.results_tree.insert('', 'end', text=str(i), 
                                   values=(title, channel, duration, views))
        
        self.progress_var.set(f"📋 找到 {len(videos)} 个结果")
        self.status_var.set(f"找到 {len(videos)} 个视频")
    
    def _search_error(self, error_msg):
        """Handle search error"""
        self.progress_bar.stop()
        self.progress_var.set(f"❌ 搜索错误: {error_msg}")
        self.status_var.set("搜索失败")
        messagebox.showerror("搜索错误", f"搜索失败: {error_msg}")
    
    def stream_media(self):
        """Stream selected media without downloading"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要播放的视频！")
            return
        
        if not self.videos:
            messagebox.showwarning("警告", "没有可用视频！请先搜索或输入URL。")
            return
        
        # Get selected video
        item = self.results_tree.item(selection[0])
        video_index = int(item['text']) - 1
        
        if 0 <= video_index < len(self.videos):
            self.selected_video = self.videos[video_index]
            
            # Check if already streaming
            if self.stream_thread and self.stream_thread.is_alive():
                messagebox.showwarning("警告", "正在播放中！")
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
            title = self.selected_video.get('title', '视频')
            
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
                error_msg = f"流媒体失败 - YouTube检测到机器人行为\n请尝试：\n1. 稍后重试\n2. 选择其他视频\n3. 使用下载功能\n\n原始错误: {error_msg}"
            self.root.after(0, self._stream_error, error_msg)
    
    def _stream_start(self, title):
        """Update UI when streaming starts"""
        format_type = "🎵 音频" if self.format_var.get() == 'audio' else "🎬 视频"
        self.progress_var.set(f"{format_type} 正在准备流媒体: {title}")
        self.progress_bar.start()
        self.status_var.set("准备流媒体...")
        self.playback_status.set("准备中...")
    
    def _play_file(self, filepath, title):
        """Play the downloaded file"""
        try:
            self.progress_bar.stop()
            self.progress_var.set(f"🎧 正在播放: {title}")
            self.status_var.set("播放中")
            self.playback_status.set(f"播放: {title[:30]}...")
            
            # Open with system default player
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.Popen(['open', filepath] if sys.platform == 'darwin' else ['xdg-open', filepath])
            
            messagebox.showinfo("播放", f"正在播放: {title}\n文件将在系统默认播放器中打开")
            
        except Exception as e:
            self.progress_var.set(f"❌ 播放错误: {str(e)}")
            self.status_var.set("播放失败")
            self.playback_status.set("播放失败")
    
    def _stream_error(self, error_msg):
        """Handle streaming error"""
        self.progress_bar.stop()
        self.progress_var.set(f"❌ 流媒体错误: {error_msg}")
        self.status_var.set("流媒体失败")
        self.playback_status.set("流媒体失败")
        messagebox.showerror("流媒体错误", f"流媒体失败: {error_msg}")
    
    def download_video(self):
        """Download selected video"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要下载的视频！")
            return
        
        if not self.videos:
            messagebox.showwarning("警告", "没有可用视频！请先搜索或输入URL。")
            return
        
        # Get selected video
        item = self.results_tree.item(selection[0])
        video_index = int(item['text']) - 1
        
        if 0 <= video_index < len(self.videos):
            self.selected_video = self.videos[video_index]
            
            # Check if already downloading
            if self.download_thread and self.download_thread.is_alive():
                messagebox.showwarning("警告", "正在下载中！")
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
            title = self.selected_video.get('title', '视频')
            
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
                error_msg = f"下载失败 - YouTube检测到机器人行为\n请尝试：\n1. 稍后重试\n2. 选择其他视频\n3. 检查网络连接\n\n原始错误: {error_msg}"
            self.root.after(0, self._download_error, error_msg)
    
    def _download_start(self, title):
        """Update UI when download starts"""
        format_type = "🎵 音频" if self.format_var.get() == 'audio' else "🎬 视频"
        self.progress_var.set(f"{format_type} 正在下载: {title}")
        self.progress_bar.start()
        self.status_var.set("下载中...")
    
    def _progress_hook(self, d):
        """Download progress callback"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()
            progress_text = f"⬇️ {percent} | 🚀 {speed} | ⏱️ {eta}"
            self.root.after(0, self._update_progress, progress_text)
        elif d['status'] == 'finished':
            filename = d.get('filename', '未知文件')
            self.root.after(0, self._update_progress, f"✅ 处理中: {os.path.basename(filename)}")
    
    def _update_progress(self, text):
        """Update progress text"""
        self.progress_var.set(text)
    
    def _download_complete(self):
        """Handle download completion"""
        self.progress_bar.stop()
        self.progress_var.set("✅ 下载完成！")
        self.status_var.set("下载完成")
        messagebox.showinfo("成功", "下载成功完成！")
    
    def _download_error(self, error_msg):
        """Handle download error"""
        self.progress_bar.stop()
        self.progress_var.set(f"❌ 下载失败: {error_msg}")
        self.status_var.set("下载失败")
        messagebox.showerror("下载错误", f"下载失败: {error_msg}")
    
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
    app = YouTubeEnhancedGUI(root)
    
    # Handle window closing
    def on_closing():
        app.cleanup_temp_files()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
