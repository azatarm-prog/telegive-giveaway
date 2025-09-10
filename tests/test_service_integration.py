"""
Integration tests for service communication
"""

import pytest
from unittest.mock import patch, Mock
import requests
import json

class TestServiceIntegration:
    """Test class for inter-service communication"""
    
    @patch('requests.post')
    def test_telegive_bot_integration(self, mock_post):
        """Test integration with Bot Service"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'message_id': 123456
        }
        mock_post.return_value = mock_response
        
        from services.bot_service import BotService
        
        giveaway_data = {
            'id': 1,
            'main_body': 'Test giveaway content',
            'winner_count': 1,
            'participation_button_text': 'Participate',
            'result_token': 'test_token_123'
        }
        
        result = BotService.post_giveaway_message(
            account_id=1,
            giveaway_data=giveaway_data
        )
        
        assert result['success'] == True
        assert result['message_id'] == 123456
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_telegive_channel_integration(self, mock_get):
        """Test integration with Channel Service"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'permissions': {
                'can_post_messages': True,
                'can_edit_messages': True
            }
        }
        mock_get.return_value = mock_response
        
        from services.channel_service import ChannelService
        
        result = ChannelService.get_permissions(account_id=1)
        
        assert result['success'] == True
        assert result['permissions']['can_post_messages'] == True
        mock_get.assert_called_once()
    
    @patch('requests.post')
    def test_telegive_participant_integration(self, mock_post):
        """Test integration with Participant Service"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'winners': [{'user_id': 111}, {'user_id': 222}],
            'total_participants': 50
        }
        mock_post.return_value = mock_response
        
        from services.participant_service import ParticipantService
        
        result = ParticipantService.select_winners(giveaway_id=1, winner_count=2)
        
        assert result['success'] == True
        assert len(result['winners']) == 2
        assert result['total_participants'] == 50
        mock_post.assert_called_once()
    
    @patch('requests.get')
    def test_telegive_auth_integration(self, mock_get):
        """Test integration with Auth Service"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'account': {
                'id': 1,
                'bot_username': 'test_bot',
                'channel_verified': True
            }
        }
        mock_get.return_value = mock_response
        
        from services.auth_service import AuthService
        
        result = AuthService.validate_account(account_id=1)
        
        assert result['success'] == True
        assert result['account']['id'] == 1
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_telegive_media_integration(self, mock_get):
        """Test integration with Media Service"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'file': {
                'id': 1,
                'filename': 'test_image.jpg',
                'accessible': True
            }
        }
        mock_get.return_value = mock_response
        
        from services.media_service import MediaService
        
        result = MediaService.get_media_file(file_id=1)
        
        assert result['success'] == True
        assert result['file']['id'] == 1
        mock_get.assert_called_once()
    
    @patch('requests.post')
    def test_media_cleanup_scheduling(self, mock_post):
        """Test media cleanup scheduling"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'cleanup_scheduled': True,
            'cleanup_time': '2024-01-15T10:35:00Z'
        }
        mock_post.return_value = mock_response
        
        from services.media_service import MediaService
        
        result = MediaService.schedule_cleanup(file_id=1, delay_minutes=5)
        
        assert result['success'] == True
        assert result['cleanup_scheduled'] == True
        mock_post.assert_called_once()
    
    def test_service_error_handling(self):
        """Test service error handling"""
        from services.auth_service import AuthService
        
        with patch('requests.get') as mock_get:
            # Simulate connection error
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
            
            result = AuthService.validate_account(account_id=1)
            
            assert result['success'] == False
            assert 'AUTH_SERVICE_UNAVAILABLE' in result['error_code']
    
    def test_service_timeout_handling(self):
        """Test service timeout handling"""
        from services.bot_service import BotService
        
        with patch('requests.post') as mock_post:
            # Simulate timeout
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
            
            result = BotService.post_giveaway_message(
                account_id=1,
                giveaway_data={'id': 1, 'main_body': 'test'}
            )
            
            assert result['success'] == False
            assert 'BOT_SERVICE_UNAVAILABLE' in result['error_code']
    
    def test_service_http_error_handling(self):
        """Test HTTP error handling"""
        from services.channel_service import ChannelService
        
        with patch('requests.get') as mock_get:
            # Simulate HTTP 500 error
            mock_response = Mock()
            mock_response.ok = False
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            result = ChannelService.get_permissions(account_id=1)
            
            assert result['success'] == False
            assert 'CHANNEL_PERMISSIONS_FAILED' in result['error_code']
    
    @patch('requests.get')
    def test_health_check_integration(self, mock_get):
        """Test health check integration"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'status': 'healthy',
            'service': 'telegive-auth'
        }
        mock_get.return_value = mock_response
        
        from services.auth_service import AuthService
        
        is_healthy = AuthService.is_service_healthy()
        
        assert is_healthy == True
        mock_get.assert_called_once()
    
    def test_bulk_messaging_integration(self):
        """Test bulk messaging integration"""
        from services.bot_service import BotService
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {
                'success': True,
                'delivered': 45,
                'failed': 5
            }
            mock_post.return_value = mock_response
            
            winners = [{'user_id': 111}, {'user_id': 222}]
            participants = [{'user_id': i} for i in range(1, 51)]
            
            result = BotService.send_bulk_messages(
                account_id=1,
                giveaway_id=1,
                winner_message='You won!',
                loser_message='Better luck next time!',
                winners=winners,
                participants=participants
            )
            
            assert result['success'] == True
            assert result['delivered'] == 45
    
    def test_participant_stats_integration(self):
        """Test participant statistics integration"""
        from services.participant_service import ParticipantService
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.ok = True
            mock_response.json.return_value = {
                'success': True,
                'stats': {
                    'total_participants': 150,
                    'captcha_completed_participants': 142,
                    'active_participants': 140
                }
            }
            mock_get.return_value = mock_response
            
            result = ParticipantService.get_participation_stats(giveaway_id=1)
            
            assert result['success'] == True
            assert result['stats']['total_participants'] == 150
            assert result['stats']['captcha_completed_participants'] == 142

class TestEndToEndFlows:
    """Test end-to-end workflows"""
    
    def test_complete_giveaway_flow(self):
        """Test complete giveaway lifecycle"""
        # This would test the full flow from creation to completion
        # but requires more complex mocking setup
        pass
    
    def test_error_recovery_flow(self):
        """Test error recovery scenarios"""
        # Test how the system handles partial failures
        pass

