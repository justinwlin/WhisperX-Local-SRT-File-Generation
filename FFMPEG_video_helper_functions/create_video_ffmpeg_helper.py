import ffmpeg
import math
import shutil
import tempfile


def get_frame_rate(video_path):
    """
    Extracts and returns the frame rate of a video file.

    Parameters:
    video_path (str): Path to the video file.

    Returns:
    str: Frame rate of the video.

    Raises:
    ValueError: If no video stream is found in the file.
    """
    probe = ffmpeg.probe(video_path)
    video_stream = next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
    )
    if video_stream is None:
        raise ValueError("No video stream found")
    frame_rate = video_stream["avg_frame_rate"]
    return frame_rate


def speed_up_audio(
    input_audio_file_path, output_audio_file_path, under_speed_seconds=60
):
    """
    Speeds up an audio file to make its duration under a specified limit.

    Parameters:
    input_audio_file_path (str): Path to the input audio file.
    output_audio_file_path (str): Path to save the output (sped-up) audio file.
    under_speed_seconds (int, optional): Maximum allowed duration in seconds for the sped-up audio. Defaults to 60 seconds.

    Returns:
    None
    """
    probe_audio = ffmpeg.probe(input_audio_file_path)
    audio_duration = float(probe_audio["streams"][0]["duration"])

    speed_up_factor = 1
    if audio_duration > under_speed_seconds:
        print("Audio exceeds specified speed")
        speed_up_factor = audio_duration / under_speed_seconds
        speed_up_factor = math.ceil(speed_up_factor * 100) / 100

        temp_output_audio_file_path = tempfile.mktemp(suffix=".mp3")
        ffmpeg.input(input_audio_file_path).audio.filter(
            "atempo", speed_up_factor
        ).output(temp_output_audio_file_path).run(overwrite_output=True)

        shutil.copy(temp_output_audio_file_path, output_audio_file_path)
    else:
        print("Audio is under specified speed requirement")


def create_video_with_captions_and_audio(
    video_input,
    audio_input,
    srt_input,
    output,
    short_vertical_format=True,
    captionStyle={
        "Alignment": "2",  # Center alignment. Other values: 1 (Left), 3 (Right)
        "MarginV": "160",  # Vertical margin from the bottom of the video frame, in pixels.
        "Fontname": "Futura",  # Font name. Other common values: "Arial", "Times New Roman", etc.
        "BorderStyle": "1",  # Border style. 1 = Outline, 3 = Opaque Box behind the text.
        "Fontsize": "22",  # Font size, in points.
        "Outline": "2",  # Outline thickness, in pixels. Only applicable if BorderStyle is 1.
        "OutlineColour": "&H000000&",  # Semi-transparent blue color with 50% opacity.
        # Common color examples:
        # Black: &H000000&, White: &HFFFFFF&, Blue: &HFF0000&, Red: &H0000FF&
    },
):
    """
    Creates a video with embedded audio and captions. Background video is provided.

    Parameters:
    video_input (str): Path to the input video file.
    audio_input (str): Path to the input audio file.
    srt_input (str): Path to the SRT file containing subtitles.
    output (str): Path to save the output video file.
    short_vertical_format (bool, optional): If True, formats the video to a 9:16 aspect ratio. Defaults to True.
    captionStyle (dict, optional): Dictionary defining the style of the captions. Defaults to a preset style.

    Returns:
    None
    """

    # Probe the input video to get its dimensions
    probe = ffmpeg.probe(video_input)
    video_width = probe["streams"][0]["width"]
    video_height = probe["streams"][0]["height"]

    # Get the duration of the audio
    probe_audio = ffmpeg.probe(audio_input)
    audio_duration = float(probe_audio["streams"][0]["duration"])
    frame_rate = get_frame_rate(video_input)

    # Load the input video
    input_video = ffmpeg.input(
        video_input, ss=0, t=audio_duration, r=frame_rate
    )  # Assume 30 fps

    # If short_vertical_format is True, crop or pad the video to 9:16 aspect ratio (1080x1920)
    if short_vertical_format:
        if video_width / video_height > 9 / 16:
            # Crop to 9:16
            input_video = input_video.crop("(iw-ih*9/16)/2", "0", "ih*9/16", "ih")
        else:
            # Pad to 9:16
            input_video = input_video.crop("0", "(ih-iw*16/9)/2", "iw", "iw*16/9")

    # Convert the dictionary into the style_options string
    style_options = ",".join(f"{key}={value}" for key, value in captionStyle.items())

    # Overlay the SRT subtitles on the input video with style options
    video_with_subtitles = ffmpeg.filter(
        input_video, "subtitles", filename=srt_input, force_style=style_options
    )

    # Combine the input video with subtitles and the audio
    audio_stream = ffmpeg.input(audio_input).audio
    combined = ffmpeg.concat(video_with_subtitles, audio_stream, v=1, a=1).node
    out_stream = ffmpeg.output(
        combined[0], combined[1], output, vcodec="libx264", acodec="aac"
    )
    out_stream.run(overwrite_output=True)


def create_video_with_subtitles(video_path, srt_path, output_path, subtitle_style=None):
    """
    Creates a video file with subtitles overlaid on top of the original video using customizable styles.

    Parameters:
    video_path (str): Path to the input video file.
    srt_path (str): Path to the SRT file containing the subtitles.
    output_path (str): Path where the output video file will be saved.
    subtitle_style (dict, optional): Dictionary specifying style options for the subtitles. Default values are provided if None.

    Returns:
    None
    """
    if subtitle_style is None:
        subtitle_style = {
            "Alignment": "2",  # Center alignment. Other values: 1 (Left), 3 (Right)
            "MarginV": "140",  # Vertical margin from the bottom of the video frame, in pixels.
            "Fontname": "Futura",  # Font name. Other common values: "Arial", "Times New Roman", etc.
            "BorderStyle": "1",  # Border style. 1 = Outline, 3 = Opaque Box behind the text.
            "Fontsize": "22",  # Font size, in points.
            "Outline": "2",  # Outline thickness, in pixels. Only applicable if BorderStyle is 1.
            "OutlineColour": "&H000000&",  # Semi-transparent blue color with 50% opacity.
            # "Fontname": "Arial",
            # "Fontsize": "24",
            # "PrimaryColour": "&Hffffff&",  # White, in BGR Hex
            # "SecondaryColour": "&H000000&",  # Black, in BGR Hex
            # "BorderStyle": "1",  # Outline
            # "OutlineColour": "&H000000&",  # Black, in BGR Hex
            # "BackColour": "&H80000000&",  # Semi-transparent black
            # "Bold": "0",  # Normal weight
            # "Italic": "0",  # No italic
            # "Alignment": "5",  # Centered middle
            # "MarginL": "10",  # Left margin in pixels (optional for fine tuning)
            # "MarginR": "10",  # Right margin in pixels (optional for fine tuning)
            # "MarginV": "10",  # Vertical margin from the center (optional for fine tuning)
        }

    # Convert the dictionary into the style_options string for the subtitles filter
    style_options = ",".join(f"{key}={value}" for key, value in subtitle_style.items())

    # Load the video and subtitle files
    video_input = ffmpeg.input(video_path)

    # Overlay the subtitles on the video with custom styles
    video_with_subtitles = ffmpeg.filter(
        video_input, "subtitles", filename=srt_path, force_style=style_options
    )

    # Output the video with subtitles to a new file
    ffmpeg.output(video_with_subtitles, output_path, vcodec="libx264").run(
        overwrite_output=True
    )
