from pylab import *
from xsramio import *
import pickle

audio = pickle.load(open("audio.p","rb"))

sample_rate = 48000;
sample_period = 1.0/sample_rate
decimation = 1
t = arange(0.0, len(audio) * sample_period, sample_period)
signal = audio[::decimation]
t = t[::decimation]

# rms = []
# rms_t = []
# window_size = int(0.05 * sample_rate)
# window = signal[0:window_size]
# squared_sum = sum([a*a for a in window])
# avg_sum = sum(window)
# rms.append(sqrt(squared_sum - avg_sum*avg_sum / (window_size *window_size)) / sqrt(window_size))
# rms_t.append(t[int(window_size - window_size/2)])
# for i in range(window_size,len(signal)):
  # squared_sum -= signal[i-window_size] * signal[i-window_size]
  # squared_sum += signal[i] * signal[i]
  # avg_sum -= signal[i-window_size]
  # avg_sum += signal[i]
  # rms.append(sqrt(squared_sum - avg_sum*avg_sum / (window_size *window_size)) / sqrt(window_size))
  # rms_t.append(t[int(i -window_size/2)])
# for i in range(window_size, len(signal)):
  # if -rms[int(i-window_size)] < signal[i] < rms[int(i-window_size)]:
    # signal[i] = 0

#envelope = [abs(s) for s in signal]
envelope = signal[:]
envelope_t = t
max_signal = []
max_signal_t = []
for i in range(1,len(envelope)-1):
  if envelope[i-1] < envelope[i] >= envelope[i+1]:
    max_signal.append(envelope[i])
    max_signal_t.append(envelope_t[i])
for j in range(0,3):
  bigmax_signal = []
  bigmax_signal_t = []
  for i in range(1,len(max_signal)-1):
    if max_signal[i-1] < max_signal[i] > max_signal[i+1]:
      bigmax_signal.append(max_signal[i])
      bigmax_signal_t.append(max_signal_t[i])
  max_signal = bigmax_signal[:]
  max_signal_t = bigmax_signal_t[:]
  
segments = []
start_index = 0
for tt in max_signal_t:
  stop_index = int(tt / sample_period)
  segments.append(signal[start_index:stop_index])
  start_index = stop_index

expanded_signal = []
for s in segments:
  if len(s) != 0:
    expanded_signal.extend(s)
    expanded_signal.extend(s)
expanded_signal_t = [i*sample_period for i in range(0,len(expanded_signal))]

condensed_signal = []
for i in range(0,len(segments),2):
  condensed_signal.extend(segments[i])
condensed_signal_t = [i*sample_period for i in range(0,len(condensed_signal))]

output_signal = expanded_signal
output_signal_t = expanded_signal_t

import sys
from intelhex import IntelHex
ih = IntelHex()
for a in range(0,len(output_signal)):
  ih[2*a] = (output_signal[a]>>8) & 0xff
  ih[2*a+1] = output_signal[a] & 0xff
ih.tofile(sys.stdout, format="hex")
#exit(0)

#ram = XsRamIo(0,255)
#print "Address width = %d, Data width = %d" % ram._get_ram_widths()
#for a in range(0,10000):
#  ram.write(a,[expanded_signal[a]])
#ram.write(0, expanded_signal)
#exit(0)

# window_duration = 0.005
# window_size = int(window_duration * sample_rate)
# energy = []
# energy_t = []
# max_signal = []
# max_signal_t = []
# segment = signal[0:window_size]
# energy.append(sum([e*e for e in segment]))
# energy_t.append(t[window_size-1])
# for i in range(window_size,len(signal)):
  # energy.append(energy[-1] - signal[i-window_size]**2 + signal[i]**2)
  # energy_t.append(t[i])
# #  max_signal.append(max(segment))
# #  max_signal_t.append(t[segment.index(max_signal[-1])+i])
# e_avg = sqrt(sum(energy) / len(energy)) / 10
# energy = [e/(window_size * e_avg) for e in energy]
# delim = []
# delim_t = []
# for i in range(window_size,len(energy)):
  # if energy[i] > 10*min(energy[i-window_size:i]):
    # delim.append(signal[i+window_size])
    # delim_t.append(energy_t[i])
    
# diff = [0]
# diff_t = [0]
# max_diff = 0
# max_diff_t = 0
# delim = []
# delim_t = []
# for i in range(1, len(signal)):
    # diff.append(abs(signal[i]-signal[i-1]))
    # diff_t.append(t[i])
    # if diff[-1] > 0.8 * max_diff:
        # max_diff = diff[-1]
        # max_diff_t = diff_t[-1]
        # delim.append(signal[i])
        # delim_t.append(t[i])
    # elif t[i] - max_diff_t > 0.01:
        # max_diff = 0
        # max_diff_t = t[i]

# window_duration = 0.020
# window_size = int(window_duration * sample_rate)
# half_window_size = window_size >> 1
# delim = []
# delim_t = []
# for i in range(half_window_size, len(signal)):
    # max_signal = max(signal[i-half_window_size:i+half_window_size])
    # if signal[i] >= max_signal:
        # max_index = i
        # max_t = t[i]
        # delim.append(max_signal)
        # delim_t.append(max_t)

#plot(t,signal,env_t,env,linewidth=1.0)
#plot(t,signal,'b-',delim_t,delim,'r o')
#plot(t,signal,'b-',energy_t,energy,'r o')
#plot(output_signal_t, output_signal)
plot(t,signal,'b-',max_signal_t,max_signal,'r o',linewidth=1.0)
#plot(t,signal,'b-',max_signal_t,max_signal,'r o',output_signal_t,output_signal,'g .',linewidth=1.0)
#plot(t,signal,expanded_signal_t,expanded_signal,'r.',bigmax_signal_t,bigmax_signal,'g <',linewidth=1.0)
#plot(t,signal,expanded_signal_t,expanded_signal,linewidth=1.0)
xlabel('time')
ylabel('audio')
title('audio waveform')
grid(True)
show()

