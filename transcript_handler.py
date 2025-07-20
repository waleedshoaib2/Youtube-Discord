from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled
import logging

logger = logging.getLogger(__name__)

class TranscriptHandler:
    def __init__(self):
        self.supported_languages = ['en', 'es', 'fr', 'de', 'ja', 'ko', 'pt', 'ru']
        
    def get_transcript(self, video_id, preferred_language='en'):
        """Fetch transcript for a video"""
        try:
            # Try to get manual transcript first
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Check for manual transcripts
            try:
                transcript = transcript_list.find_manually_created_transcript([preferred_language])
                return self._format_transcript(transcript.fetch())
            except:
                pass
                
            # Fall back to auto-generated
            try:
                transcript = transcript_list.find_generated_transcript([preferred_language])
                return self._format_transcript(transcript.fetch())
            except:
                # Try any available language
                for transcript in transcript_list:
                    if transcript.language_code in self.supported_languages:
                        return self._format_transcript(transcript.fetch())
                        
        except (NoTranscriptFound, TranscriptsDisabled) as e:
            logger.warning(f"No transcript available for video {video_id}: {e}")
        except Exception as e:
            logger.error(f"Error fetching transcript for {video_id}: {e}")
            
        return None
        
    def _format_transcript(self, transcript_data):
        """Format transcript data into readable text"""
        if not transcript_data:
            return None
            
        # Combine all text segments
        full_text = ' '.join([segment['text'] for segment in transcript_data])
        
        # Create time-stamped version
        timestamped = []
        for segment in transcript_data:
            time = self._seconds_to_time(segment['start'])
            timestamped.append(f"[{time}] {segment['text']}")
            
        return {
            'full_text': full_text,
            'timestamped': '\n'.join(timestamped),
            'segments': transcript_data,
            'duration': transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0
        }
        
    def _seconds_to_time(self, seconds):
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
        
    def extract_key_segments(self, transcript_data, max_segments=5):
        """Extract most important segments based on length and position"""
        if not transcript_data or not transcript_data.get('segments'):
            return []
            
        segments = transcript_data['segments']
        
        # Score segments based on length and position
        scored_segments = []
        total_duration = transcript_data['duration']
        
        for i, segment in enumerate(segments):
            # Favor longer segments
            length_score = len(segment['text'].split())
            
            # Favor segments from important parts (beginning, middle, end)
            position = segment['start'] / total_duration if total_duration > 0 else 0
            if position < 0.1:  # Beginning
                position_score = 1.5
            elif 0.4 < position < 0.6:  # Middle
                position_score = 1.2
            elif position > 0.9:  # End
                position_score = 1.3
            else:
                position_score = 1.0
                
            total_score = length_score * position_score
            scored_segments.append((segment, total_score))
            
        # Sort by score and return top segments
        scored_segments.sort(key=lambda x: x[1], reverse=True)
        return [seg[0] for seg in scored_segments[:max_segments]]
        
    def create_summary_preview(self, transcript_data, max_length=500):
        """Create a preview summary from transcript"""
        if not transcript_data:
            return "No transcript available"
            
        # Use key segments for summary
        key_segments = self.extract_key_segments(transcript_data, max_segments=3)
        
        if key_segments:
            summary = ' '.join([seg['text'] for seg in key_segments])
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            return summary
        else:
            # Fallback to beginning of transcript
            full_text = transcript_data.get('full_text', '')
            if len(full_text) > max_length:
                return full_text[:max_length-3] + "..."
            return full_text 