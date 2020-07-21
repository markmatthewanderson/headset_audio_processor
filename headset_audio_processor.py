import pyaudio
import wave
import time
import sys
import queue
import numpy as np

# from here on,
# HS = headset
# CON = console

RATE=44100
WIDTH=2
UNSIGNED=False
STEREO=2
MONO=1
CON_INDEX=1
HP_INDEX=0
FORMAT=pyaudio.paInt16
FRAMES_PER_BUFFER=8192
#BIN_SHIFT=30
BIN_SHIFT=60

# create audio buffers
game_audio = queue.Queue()
chat_audio = queue.Queue()

# define callbacks (in/out with respect to RPi)
def con_in_callback(in_data, frame_count, time_info, status):
    game_audio.put(in_data)
    return (None, pyaudio.paContinue)
def con_out_callback(in_data, frame_count, time_info, status):
    #ignore in_data
    data = np.frombuffer(chat_audio.get(), dtype=np.int16)
    fft_data = np.fft.fft(data)
    #new_data = fft_data
    # testing stuff out
    #new_data = np.concatenate((fft_data[0:int(len(fft_data)/2)], np.flip(fft_data[0:int(len(fft_data)/2)])), axis=None)
    # high pitch
    new_data = np.concatenate((np.zeros(BIN_SHIFT), fft_data[:(int(len(fft_data)/2)-BIN_SHIFT)], fft_data[(int(len(fft_data)/2)+BIN_SHIFT):], np.zeros(BIN_SHIFT)), axis=None)
    # low pitch
    #new_data = np.concatenate((fft_data[BIN_SHIFT:(int(len(fft_data)/2))], np.zeros(BIN_SHIFT*2), fft_data[(int(len(fft_data)/2)):-BIN_SHIFT]), axis=None)
    processed_data = np.fft.ifft(new_data).astype(np.int16)
    return (processed_data, pyaudio.paContinue)
def hs_in_callback(in_data, frame_count, time_info, status):
    chat_audio.put(in_data)
    return (None, pyaudio.paContinue)
def hs_out_callback(in_data, frame_count, time_info, status):
    #ignore in_data
    data = game_audio.get()
    return (data, pyaudio.paContinue)

# create PyAudio object
p = pyaudio.PyAudio()

# open and start non-blocking streams (in/out with respect to RPi)
con_in_stream  = p.open(rate=RATE,
                        channels=MONO,
                        format=FORMAT,
                        input=True,
                        output=False,
                        input_device_index=CON_INDEX,
                        frames_per_buffer=FRAMES_PER_BUFFER,
                        stream_callback=con_in_callback)
con_out_stream = p.open(rate=RATE,
                        channels=MONO,
                        format=FORMAT,
                        input=False,
                        output=True,
                        output_device_index=CON_INDEX,
                        frames_per_buffer=FRAMES_PER_BUFFER,
                        stream_callback=con_out_callback)
hs_in_stream   = p.open(rate=RATE,
                        channels=MONO,
                        format=FORMAT,
                        input=True,
                        output=False,
                        input_device_index=HP_INDEX,
                        frames_per_buffer=FRAMES_PER_BUFFER,
                        stream_callback=hs_in_callback)
hs_out_stream  = p.open(rate=RATE,
                        channels=MONO,
                        format=FORMAT,
                        input=False,
                        output=True,
                        output_device_index=HP_INDEX,
                        frames_per_buffer=FRAMES_PER_BUFFER,
                        stream_callback=hs_out_callback)
con_in_stream.start_stream()
con_out_stream.start_stream()
hs_in_stream.start_stream()
hs_out_stream.start_stream()

# let streams run for 3 minutes 
#time.sleep(180)
# let streams run until enter key is hit
input("Press Enter to end stream.")
#print("Ending stream.")

# stop and close streams
con_in_stream.stop_stream()
con_in_stream.close()
con_out_stream.stop_stream()
con_out_stream.close()
hs_in_stream.stop_stream()
hs_in_stream.close()
hs_out_stream.stop_stream()
hs_out_stream.close()

# terminate PyAudio instance 
p.terminate()

