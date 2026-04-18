import os
import uuid
import ffmpeg
from yt_dlp import YoutubeDL

target_filename = "compressed_"

YTDL_OPTS = {
    'format': 'mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'merge_output_format': 'mp4',
    'quiet': True,
    'no_warnings': True,
}


def download(url):
    """
    Downloads a TikTok video for a given URL.
    Returns the filename on success, None on failure.
    """
    try:
        uid = str(uuid.uuid4())[:8]
        filename = f"tiktok_{uid}.mp4"
        opts = dict(YTDL_OPTS)
        opts['outtmpl'] = filename

        with YoutubeDL(opts) as ydl:
            ydl.download([url])

        if os.path.exists(filename):
            return filename
        # yt-dlp may append extension even if specified
        for ext in ('mp4', 'webm', 'mkv'):
            candidate = f"tiktok_{uid}.{ext}"
            if os.path.exists(candidate):
                return candidate

        print("TikTok download: file not found after download.")
        return None
    except Exception as e:
        print("TikTok download error:", e)
        return None


def compress(filename):
    output_filename = f"{target_filename}{filename}"
    compress_video(filename, output_filename, 8 * 1000)
    return output_filename


def compress_video(video_full_path, output_file_name, target_size):
    min_audio_bitrate = 32000
    max_audio_bitrate = 256000

    probe = ffmpeg.probe(video_full_path)
    duration = float(probe['format']['duration'])
    audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
    audio_bitrate = float(audio_stream['bit_rate']) if audio_stream and 'bit_rate' in audio_stream else 128000
    target_total_bitrate = (target_size * 1024 * 8) / (1.073741824 * duration)

    if 10 * audio_bitrate > target_total_bitrate:
        audio_bitrate = target_total_bitrate / 10
        if audio_bitrate < min_audio_bitrate < target_total_bitrate:
            audio_bitrate = min_audio_bitrate
        elif audio_bitrate > max_audio_bitrate:
            audio_bitrate = max_audio_bitrate

    video_bitrate = target_total_bitrate - audio_bitrate

    i = ffmpeg.input(video_full_path)
    ffmpeg.output(i, os.devnull,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 1, 'f': 'mp4'}
                  ).overwrite_output().run()
    ffmpeg.output(i, output_file_name,
                  **{'c:v': 'libx264', 'b:v': video_bitrate, 'pass': 2, 'c:a': 'aac', 'b:a': audio_bitrate}
                  ).overwrite_output().run()
