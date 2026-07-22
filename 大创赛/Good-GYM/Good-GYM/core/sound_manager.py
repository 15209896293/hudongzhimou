import os
import threading
from PyQt5.QtCore import QUrl, QObject, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class SoundManager(QObject):
    """Sound effect management class for playing various notification sounds"""
    
    voice_alert = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tts_engine = None
        self.voice_enabled = True
        self.tts_lock = threading.Lock()  # 防止并发调用 pyttsx3 导致语音被吞
        self.init_sounds()
        self.init_tts()
    
    def init_sounds(self):
        """Initialize all sound effects"""
        # Set paths for various sound effects
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.count_sound_path = os.path.join(base_dir, "assets", "count.mp3")
        self.succeed_sound_path = os.path.join(base_dir, "assets", "succeed.mp3")
        self.milestone_sound_path = os.path.join(base_dir, "assets", "milestone.mp3")
        
        # Verify files exist
        self.count_file_exists = os.path.exists(self.count_sound_path)
        self.succeed_file_exists = os.path.exists(self.succeed_sound_path)
        self.milestone_file_exists = os.path.exists(self.milestone_sound_path)
        
        # Initialize players
        self.init_sound_players()
    
    def init_sound_players(self):
        """Initialize players"""
        # Initialize count player
        self.count_sound = QMediaPlayer(self)
        if self.count_file_exists:
            self.count_sound.setMedia(QMediaContent(QUrl.fromLocalFile(self.count_sound_path)))
            self.count_sound.setVolume(80)  
        
        # Initialize success player
        self.succeed_player = QMediaPlayer(self)
        if self.succeed_file_exists:
            self.succeed_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.succeed_sound_path)))
            self.succeed_player.setVolume(80)  # Set volume (0-100)
            
        # Initialize milestone player
        self.milestone_player = QMediaPlayer(self)
        if self.milestone_file_exists:
            self.milestone_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.milestone_sound_path)))
            self.milestone_player.setVolume(85)  # Set volume (0-100)
    
    def init_tts(self):
        """初始化文本转语音引擎"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'zh' in voice.id.lower() or 'chinese' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            print("TTS engine initialized successfully")
        except ImportError:
            print("pyttsx3 not found, voice features disabled")
        except Exception as e:
            print(f"Failed to initialize TTS engine: {e}")
    
    def set_voice_enabled(self, enabled):
        self.voice_enabled = enabled
    
    def speak(self, text):
        """播放语音提示"""
        if not self.voice_enabled or not text:
            return

        if self.tts_engine:
            thread = threading.Thread(target=self._speak_thread, args=(text,))
            thread.daemon = True
            thread.start()
        else:
            self.voice_alert.emit(text)
    
    def _speak_thread(self, text):
        """在后台线程中播放语音（加锁防止并发播报被吞）"""
        try:
            with self.tts_lock:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Failed to speak: {e}")
    
    def play_count_sound(self):
        """Play count sound effect"""
        if self.count_file_exists:
            # Use count sound file
            self.count_sound.play()
    
    def play_milestone_sound(self, count):
        """Play milestone notification sound (e.g., special sound every 10 counts)"""
        if count > 0 and count % 10 == 0:
            if self.milestone_file_exists:
                # Use milestone sound file
                self.milestone_player.setPosition(0)  # Reset playback position
                self.milestone_player.play()
    
    def play_completion_sound(self):
        """Play completion notification sound (can be used after achieving specific goals)"""
        if self.succeed_file_exists:
            # Use success notification sound
            self.succeed_player.setPosition(0)  # Reset playback position
            self.succeed_player.play()
    
    def play_safety_alert(self, messages):
        """播放安全警报语音"""
        if messages:
            for msg in messages:
                self.speak(msg)
