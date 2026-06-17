"""
Media preview: images, video and audio.

Images are shown directly; video/audio use QtMultimedia when available, with a
graceful fallback (open with the system default app) if the multimedia
backend is missing.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from . import theme

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".heic", ".gif", ".bmp", ".tiff", ".webp")
VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".3gp", ".avi", ".mkv", ".webm")
AUDIO_EXTS = (".mp3", ".m4a", ".aac", ".wav", ".ogg", ".opus", ".amr", ".caf")


def media_kind(path: str) -> str:
    p = path.lower()
    if p.endswith(VIDEO_EXTS):
        return "video"
    if p.endswith(AUDIO_EXTS):
        return "audio"
    if p.endswith(IMAGE_EXTS):
        return "image"
    return "image"  # default: try as image


def _open_external(path: str) -> None:
    import os
    import subprocess
    import sys
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def _image_dialog(parent, path: str) -> QDialog:
    pix = QPixmap(path)
    dlg = QDialog(parent)
    dlg.setWindowTitle(Path(path).name)
    lay = QVBoxLayout(dlg)
    lbl = QLabel()
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if pix.isNull():
        lbl.setText("⚠ يتعذّر عرض الصورة")
    else:
        dlg.resize(min(900, pix.width() + 40), min(720, pix.height() + 60))
        lbl.setPixmap(pix.scaled(
            860, 680, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
    lay.addWidget(lbl)
    cap = QLabel(path)
    cap.setObjectName("noteLabel")
    cap.setWordWrap(True)
    lay.addWidget(cap)
    return dlg


def _player_dialog(parent, path: str, kind: str) -> QDialog | None:
    try:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
        from PyQt6.QtMultimediaWidgets import QVideoWidget
    except Exception:
        return None

    dlg = QDialog(parent)
    dlg.setWindowTitle(Path(path).name)
    dlg.resize(720, 520 if kind == "video" else 160)
    lay = QVBoxLayout(dlg)

    player = QMediaPlayer(dlg)
    audio = QAudioOutput(dlg)
    player.setAudioOutput(audio)
    dlg._player = player  # keep refs alive
    dlg._audio = audio

    if kind == "video":
        video = QVideoWidget()
        video.setStyleSheet("background:#000;")
        lay.addWidget(video, 1)
        player.setVideoOutput(video)
    else:
        icon = QLabel("🎵  " + Path(path).name)
        icon.setStyleSheet(f"color:{theme.TEXT};font-size:14px;padding:10px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon)

    player.setSource(QUrl.fromLocalFile(str(Path(path).resolve())))

    controls = QHBoxLayout()
    play_btn = QPushButton("▶  تشغيل")
    play_btn.setObjectName("primary")
    pause_btn = QPushButton("⏸  إيقاف")
    pause_btn.setObjectName("ghost")
    play_btn.clicked.connect(player.play)
    pause_btn.clicked.connect(player.pause)
    controls.addWidget(play_btn)
    controls.addWidget(pause_btn)
    controls.addStretch(1)
    lay.addLayout(controls)
    return dlg


def open_media(parent, path: str) -> None:
    """Preview a media file (image/video/audio) for the examiner."""
    if not path or not Path(path).exists():
        return
    kind = media_kind(path)
    if kind == "image":
        _image_dialog(parent, path).exec()
        return
    dlg = _player_dialog(parent, path, kind)
    if dlg is None:
        _open_external(path)   # no multimedia backend: hand off to the OS
        return
    dlg.exec()
