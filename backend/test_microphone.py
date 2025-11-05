#!/usr/bin/env python3
"""
Test script to verify microphone access and speech recognition.
"""

import speech_recognition as sr
import sys

def test_microphone():
    """Test microphone access and basic speech recognition."""
    print("Testing microphone access...")
    
    # Initialize recognizer
    r = sr.Recognizer()
    
    # List available microphones
    print("\nAvailable microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  {index}: {name}")
    
    # Test microphone access
    try:
        with sr.Microphone() as source:
            print(f"\nUsing microphone: {source.device_index}")
            print("Adjusting for ambient noise... (this may take a moment)")
            r.adjust_for_ambient_noise(source, duration=1)
            print(f"Energy threshold set to: {r.energy_threshold}")
            
            print("\nTesting audio capture for 2 seconds...")
            audio = r.listen(source, timeout=2, phrase_time_limit=2)
            print(f"Audio captured successfully! Duration: {len(audio.frame_data)} bytes")
            
            # Test recognition (offline first)
            try:
                print("\nTesting offline recognition...")
                # This will fail but we can see if the audio format is correct
                text = r.recognize_sphinx(audio)
                print(f"Offline recognition result: {text}")
            except sr.UnknownValueError:
                print("Offline recognition: Could not understand audio (this is normal)")
            except sr.RequestError as e:
                print(f"Offline recognition error: {e}")
            except Exception as e:
                print(f"Offline recognition not available: {e}")
            
            # Test Google recognition
            try:
                print("\nTesting Google Speech Recognition...")
                text = r.recognize_google(audio, language='en-US')
                print(f"Google recognition result: {text}")
            except sr.UnknownValueError:
                print("Google recognition: Could not understand audio")
            except sr.RequestError as e:
                print(f"Google recognition error: {e}")
            except Exception as e:
                print(f"Google recognition failed: {e}")
                
    except Exception as e:
        print(f"Microphone access failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_microphone()
    sys.exit(0 if success else 1)