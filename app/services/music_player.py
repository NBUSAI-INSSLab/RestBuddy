"""休息音乐播放：封装 QtMultimedia 的 QMediaPlayer。

支持播放列表、循环、随机、音量控制；若 QtMultimedia 不可用则优雅降级。
"""
from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal

AUDIO_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"}

try:
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

    _MULTIMEDIA_OK = True
except Exception:  # pragma: no cover - 环境缺依赖时降级
    _MULTIMEDIA_OK = False


class MusicPlayer(QObject):
    """休息音乐播放器。"""

    state_changed = Signal(bool)          # True=正在播放
    track_changed = Signal(str)           # 当前曲目名

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.playlist: list[str] = []
        self._index = -1
        self._loop = True
        self._shuffle = False
        self._available = _MULTIMEDIA_OK

        if self._available:
            self._player = QMediaPlayer(self)
            self._audio = QAudioOutput(self)
            self._player.setAudioOutput(self._audio)
            self._player.mediaStatusChanged.connect(self._on_status)
            self._player.errorOccurred.connect(self._on_error)
        else:
            self._player = None
            self._audio = None

    # ------------------------------------------------------------------
    @property
    def available(self) -> bool:
        return self._available

    def set_playlist(self, files: list[str]) -> None:
        self.playlist = [f for f in files if Path(f).suffix.lower() in AUDIO_EXTS]

    def set_volume(self, value: int) -> None:
        if self._audio is not None:
            self._audio.setVolume(max(0.0, min(1.0, value / 100.0)))

    def set_loop(self, loop: bool) -> None:
        self._loop = loop

    def set_shuffle(self, shuffle: bool) -> None:
        self._shuffle = shuffle

    # ------------------------------------------------------------------
    def play(self) -> None:
        if not self._available:
            return
        if not self.playlist:
            return
        self._index = self._next_index(first=True)
        self._load_and_play(self._index)

    def play_file(self, path: str) -> None:
        if not self._available:
            return
        self.playlist = [path]
        self._index = 0
        self._load_and_play(0)

    def _load_and_play(self, idx: int) -> None:
        if self._player is None or not (0 <= idx < len(self.playlist)):
            return
        url = QUrl.fromLocalFile(self.playlist[idx])
        self._player.setSource(url)
        self._player.play()
        self.track_changed.emit(Path(self.playlist[idx]).stem)

    def _next_index(self, first: bool = False) -> int:
        if not self.playlist:
            return -1
        if self._shuffle and len(self.playlist) > 1:
            choices = [i for i in range(len(self.playlist)) if i != self._index]
            return random.choice(choices)
        if first or self._index < 0:
            return 0
        return (self._index + 1) % len(self.playlist)

    def _on_status(self, status) -> None:
        if self._player is None:
            return
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self._loop:
                self._index = self._next_index()
                self._load_and_play(self._index)
            else:
                self.state_changed.emit(False)

    def _on_error(self, *_args) -> None:
        # 播放失败时尝试下一首，避免卡死
        if self.playlist and self._loop:
            self._index = self._next_index()
            self._load_and_play(self._index)

    # ------------------------------------------------------------------
    def pause(self) -> None:
        if self._player is not None:
            self._player.pause()
            self.state_changed.emit(False)

    def resume(self) -> None:
        if self._player is not None:
            self._player.play()
            self.state_changed.emit(True)

    def stop(self) -> None:
        if self._player is not None:
            self._player.stop()
            self.state_changed.emit(False)

    def is_playing(self) -> bool:
        if self._player is None:
            return False
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
