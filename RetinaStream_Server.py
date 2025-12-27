import subprocess
import cv2
import numpy as np
import shutil
import platform
import sys
import threading
import queue
import time
import pyaudio

RTMP_PORT = 1935
WIDTH = 1280
HEIGHT = 720
FPS = 60
APP_NAME = "RTMP Preview"
AUDIO_RATE = 44100
AUDIO_CHANNELS = 2
AUDIO_FORMAT = pyaudio.paInt16
AUDIO_CHUNK = 1024

# -------- Ensure ffmpeg is installed --------
def ensure_ffmpeg():
    if shutil.which("ffmpeg"):
        return
    system = platform.system().lower()
    if system == "windows":
        print("Installing ffmpeg via winget...")
        subprocess.run(["winget", "install", "ffmpeg"], shell=True)
    elif system == "linux":
        print("Installing ffmpeg via apt...")
        subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"])
    else:
        print("Please install ffmpeg manually (macOS)")
        sys.exit(1)

# -------- Audio playback thread --------
def play_audio(audio_queue):
    p = pyaudio.PyAudio()
    stream = p.open(format=AUDIO_FORMAT,
                    channels=AUDIO_CHANNELS,
                    rate=AUDIO_RATE,
                    output=True)
    try:
        while True:
            if audio_queue.empty():
                time.sleep(0.001)
                continue
            data = audio_queue.get()
            stream.write(data)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# -------- Main RTMP preview --------
def main():
    ensure_ffmpeg()
    print(f"Starting RTMP server on 0.0.0.0:{RTMP_PORT}")
    print(f"RTMP ingest URL: rtmp://<this-ip>:{RTMP_PORT}/live/<anykey>")

    # Queues for buffering
    audio_queue = queue.Queue(maxsize=20)
    video_queue = queue.Queue(maxsize=10)

    # Start audio FFmpeg process
    ffmpeg_audio = subprocess.Popen([
        "ffmpeg",
        "-listen", "1",
        "-i", f"rtmp://0.0.0.0:{RTMP_PORT}/live",
        "-f", "s16le",
        "-ac", str(AUDIO_CHANNELS),
        "-ar", str(AUDIO_RATE),
        "pipe:1"
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    # Start audio thread
    audio_thread = threading.Thread(target=play_audio, args=(audio_queue,))
    audio_thread.daemon = True
    audio_thread.start()

    # Start video FFmpeg process
    ffmpeg_video = subprocess.Popen([
        "ffmpeg",
        "-listen", "1",
        "-i", f"rtmp://0.0.0.0:{RTMP_PORT}/live",
        "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "pipe:1"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Start video buffering thread
    def buffer_video():
        while True:
            raw_frame = ffmpeg_video.stdout.read(WIDTH * HEIGHT * 3)
            if not raw_frame:
                continue
            frame = np.frombuffer(raw_frame, np.uint8).reshape((HEIGHT, WIDTH, 3))
            if video_queue.full():
                continue
            video_queue.put(frame)

    threading.Thread(target=buffer_video, daemon=True).start()

    # Start audio buffering thread
    def buffer_audio():
        while True:
            data = ffmpeg_audio.stdout.read(AUDIO_CHUNK * AUDIO_CHANNELS * 2)
            if not data:
                continue
            if audio_queue.full():
                continue
            audio_queue.put(data)

    threading.Thread(target=buffer_audio, daemon=True).start()

    # Simple sync: delay video slightly to match audio
    VIDEO_DELAY_SEC = 0.1  # adjust this if needed
    video_buffer_list = []

    try:
        while True:
            if video_queue.empty():
                time.sleep(0.001)
                continue

            # collect frames for delay
            video_buffer_list.append(video_queue.get())
            if len(video_buffer_list) < int(VIDEO_DELAY_SEC * FPS):
                continue

            # show delayed frame
            frame = video_buffer_list.pop(0)
            cv2.imshow(APP_NAME, frame)

            if cv2.waitKey(1) == 27:  # ESC to exit
                break

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ffmpeg_video.kill()
        ffmpeg_audio.kill()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
