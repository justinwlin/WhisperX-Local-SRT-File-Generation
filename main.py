import argparse
import os
import whisperx
import json

from WhisperXSRTGenerator.SRTWriter import SRTConverter
from runpod_whisperx_serverless_clientside_code.runpod_client_helper import convert_to_mono_mp3

class SRTConfig:
    '''
    wordsPerLine: Integer - Number of words per line
    highlightWord: Boolean - Highlight the word
    highlightColor: String - Color of the highlight
    fileFormat: "srt" | "itt" - Format of the file
    '''
    def __init__(self, wordsPerLine = 5, highlightWord = True, highlightColor = "yellow", fileFormat="srt", gap=3, frame_rate=24):
        self.wordsPerLine = wordsPerLine
        self.highlightWord = highlightWord
        self.highlightColor = highlightColor
        self.fileFormat = fileFormat
        self.gap = gap
        self.frame_rate = frame_rate


def save_word_segments_to_json(word_segments, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(word_segments, json_file)

def load_word_segments_from_json(file_path):
    with open(file_path, 'r') as json_file:
        return json.load(json_file)

def main(audio_file: str, srtConfig: SRTConfig = SRTConfig()):
    # Mac uses CPU
    device = "cpu"
    batch_size = 16
    # Mac uses ints
    compute_type = "int8"
    # Language is english
    language_code = "en"


    # Default name for the mono-audio file should be: mono-[audio_file]
    # Get rid of the extension of the audio file
    audio_file_no_extension = os.path.splitext(audio_file)[0]
    mono_audio_path = "mono-" + audio_file
    srt_audio_path = "srt-" + audio_file_no_extension + ".srt"
    itt_audio_path = "itt-" + audio_file_no_extension + ".itt"
    json_cache_path = audio_file + ".json"

    # Check if the mono_audio_path exists if not create it
    if not os.path.exists(mono_audio_path):
        # Create the mono audio file
        convert_to_mono_mp3(audio_file, mono_audio_path)

    # Check if the JSON cache file exists
    if os.path.exists(json_cache_path):
        # Load the word segments from the JSON file
        wordSegments = load_word_segments_from_json(json_cache_path)
    else:
        # Check if the srt_audio_path exists if not create it
        if not os.path.exists(srt_audio_path):
            model = whisperx.load_model(
                "small", device, compute_type=compute_type, language=language_code
            )
            # Load the audio file
            audio = whisperx.load_audio(audio_file)
            result = model.transcribe(
                audio, batch_size=batch_size, language=language_code, print_progress=True
            )

            model_a, metadata = whisperx.load_align_model(language_code=language_code, device=device)

            result = whisperx.align(result["segments"], model_a, metadata, audio, device)

            wordSegments = result["segments"]

            # Save the word segments to JSON file
            save_word_segments_to_json(wordSegments, json_cache_path)

    # Convert the word segments to SRT
    srtConverter = SRTConverter(wordSegments)
    # Adjust word per segment
    srtConverter.adjust_word_per_segment(srtConfig.wordsPerLine)

    # Apply highlight word effect if asked for it
    srtString = ''
    if srtConfig.highlightWord and srtConfig.fileFormat == "srt":
        srtString = srtConverter.to_srt_highlight_word(color=srtConfig.highlightColor)
    elif srtConfig.highlightWord and srtConfig.fileFormat=="itt":
        srtString = srtConverter.to_itt_highlight_word(color=srtConfig.highlightColor, gap=srtConfig.gap)
    else:
        srtString = srtConverter.to_srt_plain_text()
    # Convert to SRT file
    if(srtConfig.fileFormat == "srt"):
        print("Writing to ...srt file")
        srtConverter.write_to_file(srt_audio_path, srtString)
    elif(srtConfig.fileFormat == "itt"):
        print("Writing to ...itt file")
        srtConverter.write_to_file(itt_audio_path, srtString)
    print("Finished converting audio to captioning file")


if __name__ == "__main__":
    main("reel1.wav", SRTConfig(highlightWord=True, fileFormat="srt", gap=1))
