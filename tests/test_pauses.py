import numpy as np                                                                                                                                         
import soundfile as sf                                    
import sounddevice as sd

# Create 60 seconds of sine wave test audio (no TTS)                                                                                                       
sr = 24000
duration = 60                                                                                                                                              
t = np.linspace(0, duration, sr * duration)               
audio = 0.3 * np.sin(2 * np.pi * 1000 * t).astype(np.float32)                                                                                              
                                                                                                                                                            
# Save and play
sf.write('/tmp/test_audio.wav', audio, sr)                                                                                                                 
                                                        
print("Playing 60 seconds of pure sine wave...")                                                                                                           
print("Listen for ANY pauses or stuttering. Press Ctrl+C to stop.\n")
                                                                                                                                                            
import time                                               
time.sleep(2)                                                                                                                                              
                                                        
try:                                                                                                                                                       
    data, sr = sf.read('/tmp/test_audio.wav')
    start = time.time()                                                                                                                                    
    sd.play(data, sr, latency='low')                      
    sd.wait()                                                                                                                                              
    elapsed = time.time() - start
    print(f"\n✓ Completed smoothly in {elapsed:.1f}s")                                                                                                     
except KeyboardInterrupt:                                                                                                                                  
    sd.stop()
    elapsed = time.time() - start                                                                                                                          
    print(f"\nStopped after {elapsed:.1f}s")