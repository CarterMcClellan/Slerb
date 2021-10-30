

import os
import sys

from pydub import AudioSegment
from pydub.playback import play

import numpy as np
import soundfile as sf
from pedalboard import Reverb

################################################################################
# INPUT PARAMS
################################################################################
filename = 'inputs/wav/holy_grail.wav'

if filename.endswith('wav'):
    base = os.path.basename(filename[:-len('.wav')])

elif filename.endswith('mp3'):
    base = os.path.basename(filename[:-len('.mp3')])

else:
    raise Exception('filetype unknown ')

REMOVE_AFTER_DEMO = DEMO = False
OUTPUT_FILE = '{}_w_reverb.wav'.format(base)

EXPORT_SIZE = 100 # in seconds
FULL_SONG = True

BUFFER_SIZE_SAMPLES = 1024 * 16
NOISE_FLOOR = 1e-4

################################################################################
# SLOW PARAMS
################################################################################
SLOW_RATE = .82

################################################################################
# REVERB PARAMS
################################################################################
# room size:
# 0.1 is a closet, .9 is a auditorium
ROOM_SIZE = 0.7

# how long should the higher frequencies last?
# lots of damping with a bright-sounding song to warm it up, 
# little damping if the song needs more “air”
DAMPING = 0.7

# how much effect should a song have 
WET_LEVEL = 0.33

# how much effect do we want to remove from the reverb
DRY_LEVEL = 0.8

# how long are the effects lasting in the background
# 0 width and things sound distant
WIDTH = 0.5

# not sure what this does
FREEZE_MODE = 0.0

################################################################################
# AMPLITUDE SHIFT
################################################################################

# if the sound is clipping, lower this
# the sound is too quiet, increase this
AMPLITUDE_ADJUST = -15.

################################################################################
# STEP 1) SLOW THE SONG
################################################################################

def speed_change(sound, speed=1.0):
    # Manually override the frame_rate. This tells the computer how many
    # samples to play per second
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
         "frame_rate": int(sound.frame_rate * speed)
      })
     # convert the sound with altered frame rate to a standard frame rate
     # so that regular playback programs will work right. They often only
     # know how to play audio at standard frame rate (like 44.1k)
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

# cut out the first 20.28 seconds of the song
if filename.endswith("mp3"):
    song = AudioSegment.from_mp3(filename)

elif filename.endswith("wav"):
    song = AudioSegment.from_wav(filename)

else:
    raise Exception("unknown filetype")


# new_start = (20.85 + 1.75) * 1000
# new_song = song[new_start:]
new_start = (6) * 1000
new_end = (94) * 1000
song = song[new_start:new_end]

song = speed_change(song, SLOW_RATE)

if not FULL_SONG:
    song = song[:(EXPORT_SIZE*1000)] 

song.export("{}_remix.wav".format(base), format="wav")
length = int(song.frame_count())

################################################################################
# STEP 2) ADD REVERB
# convolutional reverb algorithms: https://en.wikipedia.org/wiki/Convolution_reverb
################################################################################

reverb = Reverb(room_size=ROOM_SIZE, 
                damping=DAMPING, 
                wet_level=WET_LEVEL, 
                dry_level=DRY_LEVEL, 
                width=WIDTH, 
                freeze_mode=FREEZE_MODE)

with sf.SoundFile("{}_remix.wav".format(base)) as input_file:
    with sf.SoundFile(
        OUTPUT_FILE,
        'w',
        samplerate=input_file.samplerate,
        channels=input_file.channels,
    ) as output_file:
        length_seconds = length / input_file.samplerate
        for dry_chunk in input_file.blocks(BUFFER_SIZE_SAMPLES, frames=length):
            # Actually call Pedalboard here:
            # (reset=False is necessary to allow the reverb tail to
            # continue from one chunk to the next.)
            effected_chunk = reverb.process(
                dry_chunk, sample_rate=input_file.samplerate, reset=False
            )
            # print(effected_chunk.shape, np.amax(np.abs(effected_chunk)))
            output_file.write(effected_chunk)
        while True:
            # Pull audio from the effect until there's nothing left:
            effected_chunk = reverb.process(
                np.zeros((BUFFER_SIZE_SAMPLES, input_file.channels), np.float32),
                sample_rate=input_file.samplerate,
                reset=False,
            )
            if np.amax(np.abs(effected_chunk)) < NOISE_FLOOR:
                break
            output_file.write(effected_chunk)
sys.stderr.write("Generated file {}\n".format(OUTPUT_FILE))

os.remove("{}_remix.wav".format(base))

################################################################################
# OPTIONAL) Rescale Amplitude
###############################################################################
def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)

################################################################################
# OPTIONAL) Play the Demo Before Saving 
################################################################################
if DEMO:
    try:
        remade = AudioSegment.from_wav(OUTPUT_FILE)
        remade = match_target_amplitude(remade, AMPLITUDE_ADJUST)
        play(remade)
        if REMOVE_AFTER_DEMO:
            os.remove(OUTPUT_FILE)
    except KeyboardInterrupt:
        print("user interupt, exiting")
        if REMOVE_AFTER_DEMO:
            os.remove(OUTPUT_FILE)
