# WhisperX-Local-SRT-File-Generation
 Local way to generate SRT files for audio

# Requirements
1. Install whisperx
https://github.com/m-bain/whisperX

2. Install FFMPEG

2. Run the script:
```
if __name__ == "__main__":
    main("reel1.wav", SRTConfig())
```
Modify the main function to point to the audio file you want.

Modify the SRTConfig to set the parameters you want. 

Note that it does generate a .json file to cache results / a mono-channel audio file to make it faster when regenerating SRTConfigs. That way if you wanted to just change the SRTConfig you can just rerun the script with new parameters, and it won't have to go through retranscribing the whole audio file. And instead just use the cached results.