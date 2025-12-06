#!/usr/bin/env python3
"""
F5-TTS Inference CLI

Quick testing tool for F5-TTS inference with unified API.

Usage:
    # Basic inference
    python -m train.cli.infer \\
        --checkpoint models/f5tts/model_last.pt \\
        --vocab train/config/vocab.txt \\
        --text "Olá, mundo!" \\
        --ref-audio ref.wav \\
        --output output.wav
    
    # With custom parameters
    python -m train.cli.infer \\
        --checkpoint models/f5tts/model_last.pt \\
        --vocab train/config/vocab.txt \\
        --text "Texto longo..." \\
        --ref-audio ref.wav \\
        --ref-text "Transcrição da referência" \\
        --nfe-step 64 \\
        --cfg-strength 2.5 \\
        --speed 1.0 \\
        --output output.wav
    
    # Using service layer (with caching)
    python -m train.cli.infer \\
        --checkpoint models/f5tts/model_last.pt \\
        --vocab train/config/vocab.txt \\
        --text "Primeira frase" \\
        --ref-audio ref.wav \\
        --output output1.wav \\
        --use-service
    
    # Second call reuses loaded model
    python -m train.cli.infer \\
        --checkpoint models/f5tts/model_last.pt \\
        --vocab train/config/vocab.txt \\
        --text "Segunda frase" \\
        --ref-audio ref.wav \\
        --output output2.wav \\
        --use-service

Author: F5-TTS Training Pipeline
Version: 1.0
Date: 2025-12-06
"""
from pathlib import Path
import sys

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import typer


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from train.inference.api import F5TTSInference
from train.inference.service import get_inference_service


app = typer.Typer(
    name="f5tts-infer", help="F5-TTS Inference CLI - Quick testing tool", add_completion=False
)
console = Console()


@app.command()
def infer(
    # Required arguments
    checkpoint: Path = typer.Option(
        ...,
        "--checkpoint",
        "-c",
        help="Path to F5-TTS checkpoint (.pt or .safetensors)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    vocab: Path = typer.Option(
        ...,
        "--vocab",
        "-v",
        help="Path to vocabulary file (vocab.txt)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    text: str = typer.Option(
        ...,
        "--text",
        "-t",
        help="Text to synthesize",
    ),
    ref_audio: Path = typer.Option(
        ...,
        "--ref-audio",
        "-r",
        help="Path to reference audio file (.wav)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output audio file path (.wav)",
    ),
    # Optional arguments
    ref_text: str | None = typer.Option(
        None,
        "--ref-text",
        help="Reference audio transcription (auto-transcribed if empty)",
    ),
    device: str = typer.Option(
        "cuda",
        "--device",
        "-d",
        help="Device to use (cuda, cpu, mps)",
    ),
    nfe_step: int = typer.Option(
        32,
        "--nfe-step",
        "-n",
        help="Number of function evaluations (higher = better quality, slower)",
        min=1,
        max=128,
    ),
    cfg_strength: float = typer.Option(
        2.0,
        "--cfg-strength",
        help="Classifier-free guidance strength (1.0-3.0)",
        min=1.0,
        max=3.0,
    ),
    sway_sampling_coef: float = typer.Option(
        -1.0,
        "--sway-sampling-coef",
        help="Sway sampling coefficient (-1.0 = auto)",
    ),
    speed: float = typer.Option(
        1.0,
        "--speed",
        "-s",
        help="Speech speed multiplier (0.5-2.0)",
        min=0.5,
        max=2.0,
    ),
    remove_silence: bool = typer.Option(
        False,
        "--remove-silence",
        help="Remove leading/trailing silence",
    ),
    use_service: bool = typer.Option(
        False,
        "--use-service",
        help="Use service layer with model caching (faster for multiple calls)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
):
    """
    Generate speech from text using F5-TTS.

    This tool provides a simple interface for testing F5-TTS inference
    with the unified API. Supports direct inference or service layer
    with model caching for batch processing.
    """
    # Setup logging
    import logging

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s: %(message)s"
    )

    # Validate inputs
    if not text.strip():
        console.print("[red]❌ Error: Text cannot be empty[/red]")
        raise typer.Exit(1)

    # Display parameters
    param_table = Table(title="🎛️  Inference Parameters", show_header=False)
    param_table.add_column("Parameter", style="cyan")
    param_table.add_column("Value", style="green")

    param_table.add_row("Checkpoint", str(checkpoint.name))
    param_table.add_row("Vocab", str(vocab.name))
    param_table.add_row("Text", text[:60] + "..." if len(text) > 60 else text)
    param_table.add_row("Reference Audio", str(ref_audio.name))
    if ref_text:
        param_table.add_row(
            "Reference Text", ref_text[:60] + "..." if len(ref_text) > 60 else ref_text
        )
    param_table.add_row("Device", device)
    param_table.add_row("NFE Steps", str(nfe_step))
    param_table.add_row("CFG Strength", str(cfg_strength))
    param_table.add_row("Speed", f"{speed}x")
    param_table.add_row("Remove Silence", "Yes" if remove_silence else "No")
    param_table.add_row("Use Service", "Yes (cached)" if use_service else "No (direct)")

    console.print(param_table)
    console.print()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:

            if use_service:
                # Use service layer (model caching)
                task = progress.add_task("⏳ Configuring service...", total=None)

                service = get_inference_service()
                if not service.is_configured():
                    service.configure(
                        checkpoint_path=checkpoint,
                        vocab_file=vocab,
                        device=device,
                    )

                progress.update(task, description="🎙️ Generating speech (service layer)...")

                audio = service.generate(
                    text=text,
                    ref_audio=ref_audio,
                    ref_text=ref_text or "",
                    nfe_step=nfe_step,
                    cfg_strength=cfg_strength,
                    sway_sampling_coef=sway_sampling_coef,
                    speed=speed,
                    remove_silence=remove_silence,
                )

                progress.update(task, description="💾 Saving audio...")
                service.save_audio(audio, output)

                # Show cache status
                console.print(f"[dim]ℹ️  Model cached in memory (service: {service})[/dim]")

            else:
                # Direct inference (no caching)
                task = progress.add_task("⏳ Loading model...", total=None)

                inference = F5TTSInference(
                    checkpoint_path=checkpoint,
                    vocab_file=vocab,
                    device=device,
                )

                progress.update(task, description="🎙️ Generating speech...")

                audio = inference.generate(
                    text=text,
                    ref_audio=ref_audio,
                    ref_text=ref_text or "",
                    nfe_step=nfe_step,
                    cfg_strength=cfg_strength,
                    sway_sampling_coef=sway_sampling_coef,
                    speed=speed,
                    remove_silence=remove_silence,
                )

                progress.update(task, description="💾 Saving audio...")
                inference.save_audio(audio, output)

            progress.stop()

        # Success message
        duration = len(audio) / 24000  # F5-TTS uses 24kHz
        file_size = output.stat().st_size / 1024  # KB

        success_panel = Panel(
            f"[green]✅ Success![/green]\n\n"
            f"📊 Duration: {duration:.2f}s\n"
            f"💾 File size: {file_size:.1f} KB\n"
            f"📁 Output: {output}",
            title="🎉 Generation Complete",
            border_style="green",
        )
        console.print(success_panel)

    except FileNotFoundError as e:
        console.print(f"[red]❌ File not found: {e}[/red]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]❌ Invalid parameter: {e}[/red]")
        raise typer.Exit(1)
    except RuntimeError as e:
        console.print(f"[red]❌ Runtime error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def info(
    checkpoint: Path = typer.Option(
        ...,
        "--checkpoint",
        "-c",
        help="Path to F5-TTS checkpoint",
        exists=True,
    ),
):
    """
    Display checkpoint information.

    Shows checkpoint size, keys, and metadata.
    """
    import torch

    try:
        console.print(f"[cyan]📦 Loading checkpoint: {checkpoint}[/cyan]")

        # Load checkpoint
        if str(checkpoint).endswith(".safetensors"):
            from safetensors import safe_open

            with safe_open(str(checkpoint), framework="pt") as f:
                keys = list(f.keys())
                metadata = f.metadata()
        else:
            ckpt = torch.load(str(checkpoint), map_location="cpu")
            keys = list(ckpt.keys())
            metadata = ckpt.get("metadata", {})

        # Display info
        info_table = Table(title="📦 Checkpoint Information", show_header=False)
        info_table.add_column("Field", style="cyan")
        info_table.add_column("Value", style="green")

        file_size = checkpoint.stat().st_size / (1024**3)  # GB
        info_table.add_row("File", str(checkpoint.name))
        info_table.add_row("Size", f"{file_size:.2f} GB")
        info_table.add_row(
            "Format", "SafeTensors" if str(checkpoint).endswith(".safetensors") else "PyTorch"
        )
        info_table.add_row("Keys", str(len(keys)))

        if metadata:
            for key, value in metadata.items():
                info_table.add_row(f"  {key}", str(value))

        console.print(info_table)
        console.print()

        # Display top keys
        console.print("[cyan]🔑 Top 10 Keys:[/cyan]")
        for key in keys[:10]:
            console.print(f"  • {key}")
        if len(keys) > 10:
            console.print(f"  ... and {len(keys) - 10} more")

    except Exception as e:
        console.print(f"[red]❌ Error loading checkpoint: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
