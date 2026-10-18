import os
import time
import threading
import urllib.parse
import cv2

def normalize_camera_source(src):
    """
    Normalizes camera input string or integer:
    - Digits ('0', '1') -> int(0), int(1)
    - IP Webcam URLs (e.g. 'http://10.241.76.161:8080' or without '/video') -> appends '/video'
    - Autocorrects dot before port e.g. 10.241.76.161.8080 -> 10.241.76.161:8080/video
    - RTSP URLs -> trimmed
    """
    if isinstance(src, int):
        return src

    if isinstance(src, str):
        s = src.strip()
        if s.isdigit():
            return int(s)

        # Autocorrect IP with dot instead of colon for port e.g. 10.241.76.161.8080 -> 10.241.76.161:8080
        import re
        s = re.sub(r'(\d+\.\d+\.\d+\.\d+)\.(\d{2,5})', r'\1:\2', s)

        # HTTP / HTTPS IP Camera streams
        if s.startswith("http://") or s.startswith("https://"):
            parsed = urllib.parse.urlparse(s)
            path = parsed.path.lower()
            # If path is empty, '/', or doesn't end with a video stream endpoint
            if path in ["", "/"] or not any(ep in path for ep in ["video", "mjpeg", "shot", "feed", "live"]):
                if s.endswith("/"):
                    s = s + "video"
                else:
                    s = s + "/video"
            return s

        return s

    return 0


def is_network_camera_reachable(url, timeout=1.0):
    """
    Fast pre-flight network reachability check for IP/RTSP camera hosts.
    Prevents OpenCV from hanging for 30+ seconds on unreachable endpoints.
    """
    try:
        import socket
        parsed = urllib.parse.urlparse(str(url))
        host = parsed.hostname
        port = parsed.port
        if not port:
            port = 443 if parsed.scheme == "https" else 80
        if not host:
            return False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            return True
    except Exception:
        return False


class ThreadedCamera:
    """
    Threaded RTSP / IP Camera / Webcam stream capture.
    Prevents OpenCV buffer buildup and network latency lag by continuously reading
    the freshest frame in a background daemon thread.
    """
    def __init__(self, src=0):
        self.raw_src = src
        self.src = normalize_camera_source(src)
        self.cap = None
        self.grabbed = False
        self.frame = None
        self.is_running = False
        self.lock = threading.Lock()
        self.thread = None
        self.error_msg = ""
        self.open_camera()

    def open_camera(self):
        source_val = self.src

        # Network pre-flight check to eliminate OpenCV freezes
        if isinstance(source_val, str) and any(source_val.lower().startswith(p) for p in ["http://", "https://", "rtsp://"]):
            if not is_network_camera_reachable(source_val, timeout=1.2):
                self.error_msg = f"Network camera endpoint is offline or unreachable: {source_val}"
                self.is_running = False
                return

        # 1. Local Webcam (integer)
        if isinstance(source_val, int):
            self.cap = cv2.VideoCapture(source_val, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(source_val)

        # 2. RTSP CCTV Stream
        elif isinstance(source_val, str) and source_val.lower().startswith("rtsp://"):
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
            self.cap = cv2.VideoCapture(source_val, cv2.CAP_FFMPEG)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(source_val)

        # 3. HTTP / IP Webcam Stream (e.g. Android IP Webcam)
        else:
            # Clear any conflicting RTSP environment variables for standard HTTP MJPEG
            if "OPENCV_FFMPEG_CAPTURE_OPTIONS" in os.environ:
                del os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]
            self.cap = cv2.VideoCapture(source_val)

        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.grabbed, self.frame = self.cap.read()
            self.is_running = True
            self.thread = threading.Thread(target=self._update_loop, daemon=True)
            self.thread.start()
        else:
            self.is_running = False

    def _update_loop(self):
        while self.is_running:
            if self.cap and self.cap.isOpened():
                grabbed, frame = self.cap.read()
                if grabbed and frame is not None:
                    with self.lock:
                        self.grabbed = grabbed
                        self.frame = frame
                else:
                    time.sleep(0.015)
            else:
                break

    def read(self):
        with self.lock:
            if self.frame is not None:
                return self.grabbed, self.frame.copy()
            return False, None

    def release(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.3)
        if self.cap:
            self.cap.release()
            self.cap = None

    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()
