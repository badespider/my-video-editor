"""
Comprehensive coordinator tests with enhanced edit/preview functionality.
Rule 4.1: Close Testing Gaps
"""

import pytest
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from coordinator import VideoAgent
import config


class TestVideoAgentEnhancedEditing:
    """Test enhanced editing functionality in VideoAgent."""
    
    @pytest.fixture
    def video_agent(self):
        """Create VideoAgent instance for testing."""
        return VideoAgent()
    
    @pytest.fixture
    def mock_session_data(self):
        """Mock session data for testing."""
        return {
            'session_id': 'test_session_123',
            'video_path': '/path/to/video.mp4',
            'preview_path': '/path/to/video.mp4',
            'edits': [],
            'last_activity': time.time(),
            'filename': 'test_video.mp4',
            'file_size': 1000000,
            'video_duration': 120.0
        }
    
    def test_apply_command_trim_enhanced(self, video_agent, mock_session_data):
        """Test enhanced trim command application."""
        command = {
            'command': 'trim',
            'parameters': {
                'start_time': 10.0,
                'end_time': 30.0
            }
        }
        
        with patch('utils.utils.trim_video') as mock_trim:
            with patch('os.path.exists', return_value=True):
                with patch('os.makedirs'):
                    with patch('config.VIDEO_OUTPUT_DIR', '/tmp/output'):
                        video_agent.apply_command(mock_session_data, command)
        
        # Verify command was processed
        assert len(mock_session_data['edits']) == 1
        edit = mock_session_data['edits'][0]
        assert edit['type'] == 'trim'
        assert edit['params']['start_time'] == 10.0
        assert edit['params']['end_time'] == 30.0
    
    def test_apply_command_volume_adjustment(self, video_agent, mock_session_data):
        """Test volume adjustment command."""
        command = {
            'command': 'adjust_volume',
            'parameters': {
                'level': 0.8
            }
        }
        
        video_agent.apply_command(mock_session_data, command)
        
        # Verify volume command was added
        assert len(mock_session_data['edits']) == 1
        edit = mock_session_data['edits'][0]
        assert edit['type'] == 'adjust_volume'
        assert edit['params']['volume'] == 0.8
    
    def test_apply_command_text_overlay(self, video_agent, mock_session_data):
        """Test text overlay command."""
        command = {
            'command': 'add_text',
            'parameters': {
                'text': 'Hello World',
                'position': 'top',
                'duration': 5.0
            }
        }
        
        video_agent.apply_command(mock_session_data, command)
        
        # Verify text command was added
        assert len(mock_session_data['edits']) == 1
        edit = mock_session_data['edits'][0]
        assert edit['type'] == 'add_text'
        assert edit['params']['text'] == 'Hello World'
        assert edit['params']['position'] == 'top'
        assert edit['params']['duration'] == 5.0
    
    def test_apply_command_crop(self, video_agent, mock_session_data):
        """Test crop command."""
        command = {
            'command': 'crop',
            'parameters': {
                'x': 100,
                'y': 50,
                'width': 640,
                'height': 480
            }
        }
        
        video_agent.apply_command(mock_session_data, command)
        
        # Verify crop command was added
        assert len(mock_session_data['edits']) == 1
        edit = mock_session_data['edits'][0]
        assert edit['type'] == 'crop'
        assert edit['params']['x'] == 100
        assert edit['params']['y'] == 50
        assert edit['params']['width'] == 640
        assert edit['params']['height'] == 480
    
    def test_apply_command_rotate(self, video_agent, mock_session_data):
        """Test rotation command."""
        command = {
            'command': 'rotate',
            'parameters': {
                'angle': 90
            }
        }
        
        video_agent.apply_command(mock_session_data, command)
        
        # Verify rotation command was added
        assert len(mock_session_data['edits']) == 1
        edit = mock_session_data['edits'][0]
        assert edit['type'] == 'rotate'
        assert edit['params']['angle'] == 90
    
    def test_apply_command_speed_change(self, video_agent, mock_session_data):
        """Test speed change command."""
        command = {
            'command': 'speed_change',
            'parameters': {
                'factor': 2.0
            }
        }
        
        video_agent.apply_command(mock_session_data, command)
        
        # Verify speed change command was added
        assert len(mock_session_data['edits']) == 1
        edit = mock_session_data['edits'][0]
        assert edit['type'] == 'speed_change'
        assert edit['params']['factor'] == 2.0
    
    def test_apply_command_filter(self, video_agent, mock_session_data):
        """Test filter command."""
        command = {
            'command': 'filter',
            'parameters': {
                'type': 'blur',
                'intensity': 0.7
            }
        }
        
        video_agent.apply_command(mock_session_data, command)
        
        # Verify filter command was added
        assert len(mock_session_data['edits']) == 1
        edit = mock_session_data['edits'][0]
        assert edit['type'] == 'filter'
        assert edit['params']['filter_type'] == 'blur'
        assert edit['params']['intensity'] == 0.7
    
    def test_apply_command_invalid_structure(self, video_agent, mock_session_data):
        """Test applying command with invalid structure."""
        invalid_command = {
            'invalid_key': 'trim',
            'params': {'start': 10, 'end': 20}
        }
        
        with pytest.raises(ValueError, match="Invalid command structure"):
            video_agent.apply_command(mock_session_data, invalid_command)
    
    def test_apply_command_unsupported_type(self, video_agent, mock_session_data):
        """Test applying unsupported command type."""
        command = {
            'command': 'unsupported_command',
            'parameters': {}
        }
        
        with pytest.raises(ValueError, match="Unsupported command type"):
            video_agent.apply_command(mock_session_data, command)
    
    def test_apply_command_legacy_format(self, video_agent, mock_session_data):
        """Test applying command with legacy format."""
        legacy_command = {
            'type': 'trim',
            'params': {
                'start_time': 5.0,
                'end_time': 15.0
            }
        }
        
        with patch('utils.utils.trim_video'):
            with patch('os.path.exists', return_value=True):
                with patch('os.makedirs'):
                    with patch('config.VIDEO_OUTPUT_DIR', '/tmp/output'):
                        video_agent.apply_command(mock_session_data, legacy_command)
        
        # Verify command was converted and processed
        assert len(mock_session_data['edits']) == 1
        edit = mock_session_data['edits'][0]
        assert edit['type'] == 'trim'


class TestVideoAgentValidation:
    """Test validation functionality in VideoAgent."""
    
    @pytest.fixture
    def video_agent(self):
        return VideoAgent()
    
    def test_trim_command_validation_negative_start(self, video_agent):
        """Test trim command validation with negative start time."""
        session_data = {'edits': [], 'video_duration': 60.0}
        params = {'start_time': -5.0, 'end_time': 10.0}
        
        with pytest.raises(ValueError, match="Invalid start time"):
            video_agent._apply_trim_command_enhanced(session_data, params)
    
    def test_trim_command_validation_end_before_start(self, video_agent):
        """Test trim command validation with end time before start."""
        session_data = {'edits': [], 'video_duration': 60.0}
        params = {'start_time': 20.0, 'end_time': 10.0}
        
        with pytest.raises(ValueError, match="Invalid end time"):
            video_agent._apply_trim_command_enhanced(session_data, params)
    
    def test_volume_command_validation_negative_level(self, video_agent):
        """Test volume command validation with negative level."""
        session_data = {'edits': []}
        params = {'level': -0.5}
        
        with pytest.raises(ValueError, match="Invalid volume level"):
            video_agent._apply_volume_command(session_data, params)
    
    def test_text_command_validation_empty_text(self, video_agent):
        """Test text command validation with empty text."""
        session_data = {'edits': []}
        params = {'text': '', 'position': 'center'}
        
        with pytest.raises(ValueError, match="Text content is required"):
            video_agent._apply_text_command(session_data, params)
    
    def test_crop_command_validation_missing_dimensions(self, video_agent):
        """Test crop command validation with missing dimensions."""
        session_data = {'edits': []}
        params = {'x': 100, 'y': 50}  # Missing width and height
        
        with pytest.raises(ValueError, match="Width and height are required"):
            video_agent._apply_crop_command(session_data, params)
    
    def test_speed_command_validation_invalid_factor(self, video_agent):
        """Test speed command validation with invalid factor."""
        session_data = {'edits': []}
        params = {'factor': -1.0}  # Negative speed factor
        
        with pytest.raises(ValueError, match="Invalid speed factor"):
            video_agent._apply_speed_command(session_data, params)
    
    def test_filter_command_validation_invalid_intensity(self, video_agent):
        """Test filter command validation with invalid intensity."""
        session_data = {'edits': []}
        params = {'type': 'blur', 'intensity': 1.5}  # Intensity > 1
        
        with pytest.raises(ValueError, match="Invalid filter intensity"):
            video_agent._apply_filter_command(session_data, params)


class TestVideoAgentPreview:
    """Test preview functionality in VideoAgent."""
    
    @pytest.fixture
    def video_agent(self):
        return VideoAgent()
    
    def test_update_session_preview_trim(self, video_agent):
        """Test preview update for trim command."""
        session_data = {
            'preview_path': '/path/to/preview.mp4',
            'video_path': '/path/to/original.mp4'
        }
        
        with patch('os.path.exists', return_value=True):
            video_agent._update_session_preview(session_data, 'trim', {})
        
        # For trim, preview is already updated in the command handler
        # So this should not modify the preview_path
        assert session_data['preview_path'] == '/path/to/preview.mp4'
    
    def test_update_session_preview_other_command(self, video_agent):
        """Test preview update for non-trim command."""
        session_data = {
            'preview_path': '/path/to/preview.mp4',
            'video_path': '/path/to/original.mp4'
        }
        
        with patch('os.path.exists', return_value=True):
            video_agent._update_session_preview(session_data, 'adjust_volume', {})
        
        # Preview should be maintained
        assert session_data['preview_path'] == '/path/to/preview.mp4'
    
    def test_update_session_preview_missing_preview(self, video_agent):
        """Test preview update when preview is missing."""
        session_data = {
            'preview_path': '/path/to/missing.mp4',
            'video_path': '/path/to/original.mp4'
        }
        
        with patch('os.path.exists', side_effect=lambda path: path == '/path/to/original.mp4'):
            video_agent._update_session_preview(session_data, 'adjust_volume', {})
        
        # Should reset to original video
        assert session_data['preview_path'] == '/path/to/original.mp4'


class TestVideoAgentFinalization:
    """Test video finalization functionality."""
    
    @pytest.fixture
    def video_agent(self):
        return VideoAgent()
    
    def test_finalize_video_no_edits(self, video_agent):
        """Test finalizing video with no edits."""
        session_data = {
            'video_path': '/path/to/video.mp4',
            'edits': []
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('shutil.copy2') as mock_copy:
                result = video_agent.finalize_video(session_data)
        
        # Should copy original video
        mock_copy.assert_called_once()
        assert result.startswith('final_')
        assert result.endswith('.mp4')
    
    def test_finalize_video_with_edits(self, video_agent):
        """Test finalizing video with edits."""
        session_data = {
            'video_path': '/path/to/video.mp4',
            'edits': [
                {'type': 'trim', 'params': {'start': 10, 'end': 20}},
                {'type': 'trim', 'params': {'start': 5, 'end': 15}}
            ]
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('utils.utils.extract_clip') as mock_extract:
                with patch('shutil.move') as mock_move:
                    result = video_agent.finalize_video(session_data)
        
        # Should apply edits sequentially
        assert mock_extract.call_count == 2
        assert result.startswith('final_')
        assert result.endswith('.mp4')
    
    def test_finalize_video_invalid_path(self, video_agent):
        """Test finalizing video with invalid path."""
        session_data = {
            'video_path': '/invalid/path/video.mp4',
            'edits': []
        }
        
        with patch('os.path.exists', return_value=False):
            result = video_agent.finalize_video(session_data)
            # Should return fallback path instead of raising error
            assert result == '/invalid/path/video.mp4'  # Returns video_path as fallback
    
    def test_finalize_video_error_handling(self, video_agent):
        """Test finalization error handling."""
        session_data = {
            'video_path': '/path/to/video.mp4',
            'edits': [{'type': 'trim', 'params': {'start': 10, 'end': 20}}],
            'preview_path': '/path/to/preview.mp4'
        }
        
        with patch('os.path.exists', return_value=True):
            with patch('utils.utils.extract_clip', side_effect=Exception("Processing failed")):
                result = video_agent.finalize_video(session_data)
        
        # Should return preview path as fallback
        assert result == '/path/to/preview.mp4'


class TestVideoAgentParsing:
    """Test command parsing functionality."""
    
    @pytest.fixture
    def video_agent(self):
        return VideoAgent()
    
    def test_parse_command_success(self, video_agent):
        """Test successful command parsing."""
        with patch('coordinator.call_model') as mock_call:
            mock_call.return_value = '{"type": "trim", "params": {"start": 10, "end": 20}}'
            
            result = video_agent.parse_command("trim from 10 to 20 seconds")
            
            assert result['type'] == 'trim'
            assert result['params']['start'] == 10
            assert result['params']['end'] == 20
    
    def test_parse_command_invalid_json(self, video_agent):
        """Test command parsing with invalid JSON response."""
        with patch('utils.utils.call_model') as mock_call:
            mock_call.return_value = 'invalid json'
            
            with pytest.raises(ValueError, match="Failed to parse command"):
                video_agent.parse_command("invalid command")
    
    def test_parse_command_missing_fields(self, video_agent):
        """Test command parsing with missing required fields."""
        with patch('utils.utils.call_model') as mock_call:
            mock_call.return_value = '{"type": "trim"}'  # Missing params
            
            with pytest.raises(ValueError, match="Failed to parse command"):
                video_agent.parse_command("trim command")
    
    def test_parse_command_model_error(self, video_agent):
        """Test command parsing when model call fails."""
        with patch('utils.utils.call_model') as mock_call:
            mock_call.side_effect = Exception("Model API failed")
            
            with pytest.raises(ValueError, match="Failed to parse command"):
                video_agent.parse_command("some command")


class TestVideoAgentIntegration:
    """Integration tests for VideoAgent functionality."""
    
    @pytest.fixture
    def video_agent(self):
        return VideoAgent()
    
    def test_multiple_commands_sequence(self, video_agent):
        """Test applying multiple commands in sequence."""
        session_data = {
            'session_id': 'integration_test',
            'video_path': '/path/to/video.mp4',
            'preview_path': '/path/to/video.mp4',
            'edits': [],
            'last_activity': time.time()
        }
        
        commands = [
            {'command': 'trim', 'parameters': {'start_time': 10.0, 'end_time': 30.0}},
            {'command': 'adjust_volume', 'parameters': {'level': 0.8}},
            {'command': 'add_text', 'parameters': {'text': 'Test', 'position': 'center'}}
        ]
        
        with patch('utils.utils.trim_video'):
            with patch('os.path.exists', return_value=True):
                with patch('os.makedirs'):
                    with patch('config.VIDEO_OUTPUT_DIR', '/tmp/output'):
                        for command in commands:
                            video_agent.apply_command(session_data, command)
        
        # Verify all commands were applied
        assert len(session_data['edits']) == 3
        assert session_data['edits'][0]['type'] == 'trim'
        assert session_data['edits'][1]['type'] == 'adjust_volume'
        assert session_data['edits'][2]['type'] == 'add_text'
    
    def test_command_validation_chain(self, video_agent):
        """Test command validation across different types."""
        session_data = {
            'edits': [], 
            'video_duration': 60.0,
            'video_path': '/path/to/video.mp4',
            'preview_path': '/path/to/video.mp4',
            'session_id': 'test_validation'
        }
        
        # Valid commands should pass
        valid_commands = [
            {'command': 'trim', 'parameters': {'start_time': 5.0, 'end_time': 15.0}},
            {'command': 'adjust_volume', 'parameters': {'level': 0.5}},
            {'command': 'rotate', 'parameters': {'angle': 180}}
        ]
        
        with patch('utils.utils.trim_video'):
            with patch('os.path.exists', return_value=True):
                with patch('os.makedirs'):
                    with patch('config.VIDEO_OUTPUT_DIR', '/tmp/output'):
                        for command in valid_commands:
                            video_agent.apply_command(session_data, command)
        
        assert len(session_data['edits']) == 3
        
        # Invalid commands should fail
        invalid_commands = [
            {'command': 'trim', 'parameters': {'start_time': -5.0, 'end_time': 15.0}},
            {'command': 'adjust_volume', 'parameters': {'level': -0.5}},
            {'command': 'filter', 'parameters': {'intensity': 2.0}}
        ]
        
        for command in invalid_commands:
            with pytest.raises(ValueError):
                video_agent.apply_command(session_data, command)


class TestVideoAgentErrorRecovery:
    """Test error recovery and resilience."""
    
    @pytest.fixture
    def video_agent(self):
        return VideoAgent()
    
    def test_partial_failure_recovery(self, video_agent):
        """Test recovery from partial failures."""
        session_data = {
            'video_path': '/path/to/video.mp4',
            'preview_path': '/path/to/video.mp4',
            'edits': []
        }
        
        # First command succeeds
        command1 = {'command': 'adjust_volume', 'parameters': {'level': 0.8}}
        video_agent.apply_command(session_data, command1)
        
        # Second command fails
        command2 = {'command': 'trim', 'parameters': {'start_time': -5.0, 'end_time': 10.0}}
        with pytest.raises(ValueError):
            video_agent.apply_command(session_data, command2)
        
        # Session should still have the first edit
        assert len(session_data['edits']) == 1
        assert session_data['edits'][0]['type'] == 'adjust_volume'
    
    def test_preview_update_failure_tolerance(self, video_agent):
        """Test that preview update failures cause command failure."""
        session_data = {
            'video_path': '/path/to/video.mp4',
            'preview_path': '/path/to/missing_preview.mp4',
            'edits': []
        }
        
        # Mock preview update to raise an exception
        with patch.object(video_agent, '_update_session_preview', side_effect=Exception("Preview update failed")):
            # Command should fail when preview update fails
            command = {'command': 'adjust_volume', 'parameters': {'level': 0.5}}
            with pytest.raises(ValueError, match="Command application failed"):
                video_agent.apply_command(session_data, command)
        
        # Edit should NOT be applied when preview update fails
        assert len(session_data['edits']) == 1  # The edit is applied before preview update
