audio-voice-celery  | [2025-12-01 23:28:03,278: INFO/MainProcess] Loaded F5-TTS quality profile: f5tts_431cb55ec24d
audio-voice-celery  | [2025-12-01 23:28:03,278: ERROR/MainProcess] F5-TTS synthesis failed: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/app/app/engines/f5tts_engine.py", line 387, in generate_dubbing
audio-voice-celery  |     raise FileNotFoundError(
audio-voice-celery  | FileNotFoundError: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | [2025-12-01 23:28:03,278: ERROR/MainProcess] Dubbing job job_fb17e796f8ba failed: TTS engine error: F5-TTS synthesis error: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/app/app/engines/f5tts_engine.py", line 387, in generate_dubbing
audio-voice-celery  |     raise FileNotFoundError(
audio-voice-celery  | FileNotFoundError: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | 
audio-voice-celery  | The above exception was the direct cause of the following exception:
audio-voice-celery  | 
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/app/app/processor.py", line 144, in process_dubbing_job
audio-voice-celery  |     audio_bytes, duration = await engine.generate_dubbing(
audio-voice-celery  |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/app/app/engines/f5tts_engine.py", line 478, in generate_dubbing
audio-voice-celery  |     raise TTSEngineException(f"F5-TTS synthesis error: {e}") from e
audio-voice-celery  | app.exceptions.TTSEngineException: TTS engine error: F5-TTS synthesis error: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | [2025-12-01 23:28:03,279: ERROR/MainProcess] ❌ Celery dubbing task failed: Dubbing error: TTS engine error: F5-TTS synthesis error: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/app/app/engines/f5tts_engine.py", line 387, in generate_dubbing
audio-voice-celery  |     raise FileNotFoundError(
audio-voice-celery  | FileNotFoundError: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | 
audio-voice-celery  | The above exception was the direct cause of the following exception:
audio-voice-celery  | 
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/app/app/processor.py", line 144, in process_dubbing_job
audio-voice-celery  |     audio_bytes, duration = await engine.generate_dubbing(
audio-voice-celery  |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/app/app/engines/f5tts_engine.py", line 478, in generate_dubbing
audio-voice-celery  |     raise TTSEngineException(f"F5-TTS synthesis error: {e}") from e
audio-voice-celery  | app.exceptions.TTSEngineException: TTS engine error: F5-TTS synthesis error: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | 
audio-voice-celery  | The above exception was the direct cause of the following exception:
audio-voice-celery  | 
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/app/app/celery_tasks.py", line 81, in _process
audio-voice-celery  |     job = await get_processor().process_dubbing_job(job, voice_profile)
audio-voice-celery  |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/app/app/processor.py", line 191, in process_dubbing_job
audio-voice-celery  |     raise DubbingException(str(e)) from e
audio-voice-celery  | app.exceptions.DubbingException: Dubbing error: TTS engine error: F5-TTS synthesis error: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | [2025-12-01 23:28:03,281: ERROR/MainProcess] Task app.celery_tasks.dubbing_task[job_fb17e796f8ba] raised unexpected: DubbingException('Dubbing error: TTS engine error: F5-TTS synthesis error: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.')
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/app/app/engines/f5tts_engine.py", line 387, in generate_dubbing
audio-voice-celery  |     raise FileNotFoundError(
audio-voice-celery  | FileNotFoundError: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | 
audio-voice-celery  | The above exception was the direct cause of the following exception:
audio-voice-celery  | 
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/app/app/processor.py", line 144, in process_dubbing_job
audio-voice-celery  |     audio_bytes, duration = await engine.generate_dubbing(
audio-voice-celery  |                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/app/app/engines/f5tts_engine.py", line 478, in generate_dubbing
audio-voice-celery  |     raise TTSEngineException(f"F5-TTS synthesis error: {e}") from e
audio-voice-celery  | app.exceptions.TTSEngineException: TTS engine error: F5-TTS synthesis error: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.
audio-voice-celery  | 
audio-voice-celery  | The above exception was the direct cause of the following exception:
audio-voice-celery  | 
audio-voice-celery  | Traceback (most recent call last):
audio-voice-celery  |   File "/usr/local/lib/python3.11/dist-packages/celery/app/trace.py", line 477, in trace_task
audio-voice-celery  |     R = retval = fun(*args, **kwargs)
audio-voice-celery  |                  ^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/usr/local/lib/python3.11/dist-packages/celery/app/trace.py", line 760, in __protected_call__
audio-voice-celery  |     return self.run(*args, **kwargs)
audio-voice-celery  |            ^^^^^^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/app/app/celery_tasks.py", line 99, in dubbing_task
audio-voice-celery  |     return run_async_task(_process())
audio-voice-celery  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/app/app/celery_tasks.py", line 52, in run_async_task
audio-voice-celery  |     return loop.run_until_complete(coro)
audio-voice-celery  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/usr/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
audio-voice-celery  |     return future.result()
audio-voice-celery  |            ^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/app/app/celery_tasks.py", line 81, in _process
audio-voice-celery  |     job = await get_processor().process_dubbing_job(job, voice_profile)
audio-voice-celery  |           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
audio-voice-celery  |   File "/app/app/processor.py", line 191, in process_dubbing_job
audio-voice-celery  |     raise DubbingException(str(e)) from e
audio-voice-celery  | app.exceptions.DubbingException: Dubbing error: TTS engine error: F5-TTS synthesis error: Voice profile audio file not found: uploads/clone_20251201015249453496.ogg. The voice profile may have expired or the file was deleted. Please re-upload the voice sample.