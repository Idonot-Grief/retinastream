import subprocess
import cv2
import numpy as np
import shutil
import platform
import sys
import threading
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
def play_audio(pipe):
    p = pyaudio.PyAudio()
    stream = p.open(format=AUDIO_FORMAT,
                    channels=AUDIO_CHANNELS,
                    rate=AUDIO_RATE,
                    output=True)
    try:
        while True:
            data = pipe.stdout.read(AUDIO_CHUNK * AUDIO_CHANNELS * 2)  # 2 bytes per sample
            if not data:
                continue
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

    # Start FFmpeg RTMP listener with video and audio
    ffmpeg = subprocess.Popen([
        "ffmpeg",
        "-listen", "1",
        "-i", f"rtmp://0.0.0.0:{RTMP_PORT}/live",
        "-vf", f"scale={WIDTH}:{HEIGHT},fps={FPS}",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "pipe:1",
        "-f", "s16le",  # raw PCM audio
        "-ac", str(AUDIO_CHANNELS),
        "-ar", str(AUDIO_RATE),
        "pipe:3"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, pass_fds=(3,))

    # Start audio playback thread
    audio_thread = threading.Thread(target=play_audio, args=(ffmpeg,))
    audio_thread.daemon = True
    audio_thread.start()

    print("Waiting for RTMP stream...")

    try:
        while True:
            raw_frame = ffmpeg.stdout.read(WIDTH * HEIGHT * 3)
            if not raw_frame:
                continue

            frame = np.frombuffer(raw_frame, np.uint8).reshape((HEIGHT, WIDTH, 3))
            cv2.imshow(APP_NAME, frame)

            if cv2.waitKey(1) == 27:  # ESC to exit
                break

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ffmpeg.kill()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
