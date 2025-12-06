import argparse
import logging
import os
from pathlib import Path
import re
import subprocess
import time

from f5_tts.api import F5TTS


# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
import sys


sys.path.insert(0, str(PROJECT_ROOT))

from train.config.loader import load_config


logging.basicConfig(level=logging.INFO)


class AgentF5TTS:
    def __init__(self, ckpt_file, vocoder_local_path=None, vocab_file="", delay=0, device=None):
        """
        Initialize the F5-TTS Agent.

        :param ckpt_file: Path to the safetensors model checkpoint.
        :param vocoder_local_path: Path to local vocoder (None uses default from HuggingFace).
        :param delay: Delay in seconds between audio generations.
        :param device: Device to use ("cpu", "cuda", None for auto-detect).
        """
        self.model = F5TTS(
            ckpt_file=ckpt_file,
            vocoder_local_path=vocoder_local_path,
            vocab_file=vocab_file,
            device=device,
            use_ema=True,
            # ode_method="euler",
            # delay=delay,
        )
        self.delay = delay  # Delay in seconds

    def generate_emotion_speech(
        self, text_file, output_audio_file, speaker_emotion_refs, convert_to_mp3=False
    ):
        """
        Generate speech using the F5-TTS model.

        :param text_file: Path to the input text file.
        :param output_audio_file: Path to save the combined audio output.
        :param speaker_emotion_refs: Dictionary mapping (speaker, emotion) tuples to reference audio paths.
        :param convert_to_mp3: Boolean flag to convert the output to MP3.
        """
        try:
            with open(text_file, encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            logging.error(f"Text file not found: {text_file}")
            return

        if not lines:
            logging.error("Input text file is empty.")
            return

        temp_files = []
        os.makedirs(os.path.dirname(output_audio_file), exist_ok=True)

        for i, line in enumerate(lines):

            speaker, emotion = self._determine_speaker_emotion(line)
            ref_audio = speaker_emotion_refs.get((speaker, emotion))
            line = re.sub(r"\[speaker:.*?\]\s*", "", line)
            if not ref_audio or not os.path.exists(ref_audio):
                logging.error(
                    f"Reference audio not found for speaker '{speaker}', emotion '{emotion}'."
                )
                continue

            ref_text = ""  # Placeholder or load corresponding text
            temp_file = f"{output_audio_file}_line{i + 1}.wav"

            try:
                logging.info(
                    f"Generating speech for line {i + 1}: '{line}' with speaker '{speaker}', emotion '{emotion}'"
                )
                self.model.infer(
                    ref_file=ref_audio,
                    ref_text=ref_text,
                    gen_text=line,
                    file_wave=temp_file,
                    remove_silence=True,
                )
                temp_files.append(temp_file)
                time.sleep(self.delay)
            except Exception as e:
                logging.error(f"Error generating speech for line {i + 1}: {e}")

        self._combine_audio_files(temp_files, output_audio_file, convert_to_mp3)

    def generate_speech(self, text_file, output_audio_file, ref_audio, convert_to_mp3=False):
        try:
            with open(text_file, encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            logging.error(f"Text file not found: {text_file}")
            return

        if not lines:
            logging.error("Input text file is empty.")
            return

        temp_files = []
        os.makedirs(os.path.dirname(output_audio_file), exist_ok=True)

        for i, line in enumerate(lines):

            if not ref_audio or not os.path.exists(ref_audio):
                logging.error("Reference audio not found for speaker.")
                continue
            temp_file = f"{output_audio_file}_line{i + 1}.wav"

            try:
                logging.info(f"Generating speech for line {i + 1}: '{line}'")
                self.model.infer(
                    ref_file=ref_audio,  # No reference audio
                    ref_text="",  # No reference text
                    gen_text=line,
                    file_wave=temp_file,
                )
                temp_files.append(temp_file)
            except Exception as e:
                logging.error(f"Error generating speech for line {i + 1}: {e}")

        # Combine temp_files into output_audio_file if needed
        self._combine_audio_files(temp_files, output_audio_file, convert_to_mp3)

    def _determine_speaker_emotion(self, text):
        """
        Extract speaker and emotion from the text using regex.
        Default to "speaker1" and "neutral" if not specified.
        """
        speaker, emotion = "speaker1", "neutral"  # Default values

        # Use regex to find [speaker:speaker_name, emotion:emotion_name]
        match = re.search(r"\[speaker:(.*?), emotion:(.*?)\]", text)
        if match:
            speaker = match.group(1).strip()
            emotion = match.group(2).strip()

        logging.info(f"Determined speaker: '{speaker}', emotion: '{emotion}'")
        return speaker, emotion

    def _combine_audio_files(self, temp_files, output_audio_file, convert_to_mp3):
        """Combine multiple audio files into a single file using FFmpeg."""
        if not temp_files:
            logging.error("No audio files to combine.")
            return

        list_file = "file_list.txt"
        with open(list_file, "w") as f:
            for temp in temp_files:
                f.write(f"file '{temp}'\n")

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_file,
                    "-c",
                    "copy",
                    output_audio_file,
                ],
                check=True,
            )
            if convert_to_mp3:
                mp3_output = output_audio_file.replace(".wav", ".mp3")
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        output_audio_file,
                        "-codec:a",
                        "libmp3lame",
                        "-qscale:a",
                        "2",
                        mp3_output,
                    ],
                    check=True,
                )
                logging.info(f"Converted to MP3: {mp3_output}")
            for temp in temp_files:
                os.remove(temp)
            os.remove(list_file)
        except Exception as e:
            logging.error(f"Error combining audio files: {e}")


# Example usage, remove from this line on to import into other agents.
# make sure to adjust the paths to yourr files.
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="F5-TTS Inference with Unified Config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic inference with default checkpoint
  python -m train.scripts.AgentF5TTSChunk
  
  # Custom checkpoint and input
  python -m train.scripts.AgentF5TTSChunk --checkpoint model_50000.pt --input my_text.txt
  
  # Override device
  python -m train.scripts.AgentF5TTSChunk --device cpu
        """,
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        default="model_last.pt",
        help="Checkpoint filename (default: model_last.pt)",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="input_text.txt",
        help="Input text file (default: input_text.txt)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="final_output_emo.wav",
        help="Output audio file (default: final_output_emo.wav)",
    )
    parser.add_argument("--ref-audio", type=str, help="Reference audio for emotion/speaker")
    parser.add_argument(
        "--device", type=str, choices=["cuda", "cpu", "auto"], help="Device (default: from config)"
    )
    parser.add_argument(
        "--delay", type=int, default=6, help="Delay between generations (default: 6)"
    )
    parser.add_argument("--mp3", action="store_true", help="Convert output to MP3")

    args = parser.parse_args()

    # Load unified config
    cli_overrides = {}
    if args.device:
        cli_overrides["hardware"] = {"device": args.device}

    config = load_config(cli_overrides=cli_overrides if cli_overrides else None)

    # Resolve paths from config
    output_dir = PROJECT_ROOT / config.paths.output_dir
    vocab_file = PROJECT_ROOT / config.paths.vocab_file

    # Checkpoint path
    checkpoint_path = output_dir / args.checkpoint
    if not checkpoint_path.exists():
        logging.error(f"Checkpoint not found: {checkpoint_path}")
        logging.info(f"Available in {output_dir}:")
        if output_dir.exists():
            for f in sorted(output_dir.glob("*.pt")):
                logging.info(f"  - {f.name}")
        sys.exit(1)

    # Vocoder path (from config or hardcoded fallback)
    if config.vocoder.is_local and config.vocoder.local_path:
        vocoder_path = PROJECT_ROOT / config.vocoder.local_path
    else:
        # Fallback to known location
        vocoder_path = (
            PROJECT_ROOT
            / "models/f5tts/models--charactr--vocos-mel-24khz/snapshots/0feb3fdd929bcd6649e0e7c5a688cf7dd012ef21/"
        )

    # Input/output paths
    input_file = PROJECT_ROOT / "train" / args.input
    output_file = PROJECT_ROOT / "train" / args.output

    # Reference audio
    if args.ref_audio:
        ref_audio_path = Path(args.ref_audio)
        if not ref_audio_path.is_absolute():
            ref_audio_path = output_dir / "samples" / args.ref_audio
    else:
        # Default: use latest sample from output dir
        samples_dir = output_dir / "samples"
        if samples_dir.exists():
            ref_files = sorted(samples_dir.glob("*_ref.wav"))
            ref_audio_path = ref_files[-1] if ref_files else None
        else:
            ref_audio_path = None

    # Speaker emotion refs
    if ref_audio_path and ref_audio_path.exists():
        speaker_emotion_refs = {
            ("speaker1", "happy"): str(ref_audio_path),
        }
    else:
        logging.warning("No reference audio found, using default")
        speaker_emotion_refs = {}

    # Print config
    logging.info("=" * 80)
    logging.info("F5-TTS INFERENCE")
    logging.info("=" * 80)
    logging.info(f"Checkpoint: {checkpoint_path}")
    logging.info(f"Vocab: {vocab_file}")
    logging.info(f"Vocoder: {vocoder_path}")
    logging.info(f"Device: {config.hardware.device}")
    logging.info(f"Input: {input_file}")
    logging.info(f"Output: {output_file}")
    if ref_audio_path:
        logging.info(f"Reference: {ref_audio_path}")
    logging.info("=" * 80)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    # Create agent
    agent = AgentF5TTS(
        ckpt_file=str(checkpoint_path),
        vocoder_local_path=str(vocoder_path) if vocoder_path.exists() else None,
        vocab_file=str(vocab_file),
        delay=args.delay,
        device=config.hardware.device if config.hardware.device != "auto" else None,
    )

    # Generate
    if speaker_emotion_refs:
        agent.generate_emotion_speech(
            text_file=str(input_file),
            output_audio_file=str(output_file),
            speaker_emotion_refs=speaker_emotion_refs,
            convert_to_mp3=args.mp3,
        )
    else:
        logging.error("No reference audio configured")
        sys.exit(1)

    # agent.generate_speech(
    #     text_file="input_text2.txt",
    #     output_audio_file="output/final_output.wav",
    #     ref_audio="ref_audios/refaudio.mp3",
    #     convert_to_mp3=True,
    # )
