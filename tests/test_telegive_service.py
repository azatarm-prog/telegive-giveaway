"""
Unit tests for the Giveaway Management Service
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import json
from datetime import datetime, timezone

from app import app, db
from models import Giveaway, GiveawayStats, GiveawayPublishingLog
from config import TestingConfig

class TestGiveawayService:
    """Test class for Giveaway Service functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client with testing configuration"""
        app.config.from_object(TestingConfig)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def sample_giveaway_data(self):
        """Sample giveaway data for testing"""
        return {
            'account_id': 1,
            'title': 'Test Giveaway',
            'main_body': 'Win amazing prizes! Join now for a chance to win incredible rewards.',
            'winner_count': 3,
            'participation_button_text': 'Join Now'
        }
    
    @pytest.fixture
    def sample_finish_messages(self):
        """Sample finish messages for testing"""
        return {
            'public_conclusion_message': 'Giveaway finished! Check results below.',
            'winner_message': 'Congratulations! You won!',
            'loser_message': 'Better luck next time!'
        }
    
    def test_create_giveaway_success(self, client, sample_giveaway_data):
        """Test successful giveaway creation"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            response = client.post('/api/giveaways/create', 
                                 json=sample_giveaway_data,
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['giveaway']['title'] == 'Test Giveaway'
            assert data['giveaway']['status'] == 'active'
            assert 'result_token' in data['giveaway']
    
    def test_create_giveaway_validation_error(self, client):
        """Test giveaway creation with validation errors"""
        invalid_data = {
            'account_id': 1,
            'title': 'AB',  # Too short
            'main_body': 'Short',  # Too short
            'winner_count': 0  # Invalid
        }
        
        response = client.post('/api/giveaways/create',
                             json=invalid_data,
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'validation_errors' in data
    
    def test_create_giveaway_single_active_limit(self, client, sample_giveaway_data):
        """Test single active giveaway enforcement"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create first giveaway
            response1 = client.post('/api/giveaways/create',
                                  json=sample_giveaway_data,
                                  content_type='application/json')
            assert response1.status_code == 201
            
            # Try to create second giveaway
            response2 = client.post('/api/giveaways/create',
                                  json=sample_giveaway_data,
                                  content_type='application/json')
            
            assert response2.status_code == 409
            data = json.loads(response2.data)
            assert data['success'] == False
            assert 'already has an active giveaway' in data['error']
    
    def test_get_active_giveaway_success(self, client, sample_giveaway_data):
        """Test getting active giveaway for account"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create giveaway first
            create_response = client.post('/api/giveaways/create',
                                        json=sample_giveaway_data,
                                        content_type='application/json')
            assert create_response.status_code == 201
            
            # Get active giveaway
            response = client.get('/api/giveaways/active/1')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['giveaway']['title'] == 'Test Giveaway'
    
    def test_get_active_giveaway_not_found(self, client):
        """Test getting active giveaway when none exists"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            response = client.get('/api/giveaways/active/1')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data['success'] == False
            assert 'No active giveaway found' in data['error']
    
    @patch('services.ChannelService.validate_channel_setup')
    @patch('services.BotService.post_giveaway_message')
    @patch('services.MediaService.schedule_cleanup')
    def test_publish_giveaway_success(self, mock_cleanup, mock_post, mock_channel, client, sample_giveaway_data):
        """Test successful giveaway publishing"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create giveaway first
            create_response = client.post('/api/giveaways/create',
                                        json=sample_giveaway_data,
                                        content_type='application/json')
            giveaway_id = json.loads(create_response.data)['giveaway']['id']
            
            # Mock services
            mock_channel.return_value = {'success': True, 'permissions': {'can_post_messages': True}}
            mock_post.return_value = {'success': True, 'message_id': 123456}
            mock_cleanup.return_value = {'success': True}
            
            response = client.post(f'/api/giveaways/{giveaway_id}/publish')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['message_id'] == 123456
    
    def test_publish_giveaway_not_found(self, client):
        """Test publishing non-existent giveaway"""
        response = client.post('/api/giveaways/999/publish')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Giveaway not found' in data['error']
    
    def test_update_finish_messages_success(self, client, sample_giveaway_data, sample_finish_messages):
        """Test updating finish messages"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create giveaway first
            create_response = client.post('/api/giveaways/create',
                                        json=sample_giveaway_data,
                                        content_type='application/json')
            giveaway_id = json.loads(create_response.data)['giveaway']['id']
            
            response = client.put(f'/api/giveaways/{giveaway_id}/finish-messages',
                                json=sample_finish_messages,
                                content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['messages_ready'] == True
    
    def test_update_finish_messages_validation_error(self, client, sample_giveaway_data):
        """Test updating finish messages with validation errors"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create giveaway first
            create_response = client.post('/api/giveaways/create',
                                        json=sample_giveaway_data,
                                        content_type='application/json')
            giveaway_id = json.loads(create_response.data)['giveaway']['id']
            
            invalid_messages = {
                'public_conclusion_message': 'OK',  # Too short
                'winner_message': '',  # Empty
                'loser_message': 'A' * 5000  # Too long
            }
            
            response = client.put(f'/api/giveaways/{giveaway_id}/finish-messages',
                                json=invalid_messages,
                                content_type='application/json')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] == False
            assert 'validation_errors' in data
    
    @patch('services.ParticipantService.select_winners')
    @patch('services.ParticipantService.get_participants')
    @patch('services.BotService.send_bulk_messages')
    @patch('services.BotService.post_conclusion_message')
    def test_finish_giveaway_success(self, mock_conclusion, mock_bulk, mock_participants, mock_winners, client, sample_giveaway_data, sample_finish_messages):
        """Test successful giveaway finishing"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create giveaway
            create_response = client.post('/api/giveaways/create',
                                        json=sample_giveaway_data,
                                        content_type='application/json')
            giveaway_id = json.loads(create_response.data)['giveaway']['id']
            
            # Set finish messages
            client.put(f'/api/giveaways/{giveaway_id}/finish-messages',
                      json=sample_finish_messages,
                      content_type='application/json')
            
            # Manually set message_id to simulate published giveaway
            with app.app_context():
                giveaway = Giveaway.query.get(giveaway_id)
                giveaway.message_id = 123456
                db.session.commit()
            
            # Mock services
            mock_winners.return_value = {
                'success': True,
                'winners': [{'user_id': 111}, {'user_id': 222}],
                'total_participants': 100
            }
            mock_participants.return_value = {
                'success': True,
                'participants': [{'user_id': i} for i in range(1, 101)]
            }
            mock_bulk.return_value = {'success': True, 'delivered': 100}
            mock_conclusion.return_value = {'success': True, 'message_id': 789}
            
            response = client.post(f'/api/giveaways/{giveaway_id}/finish')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['status'] == 'finished'
            assert data['winners_selected'] == 2
    
    def test_finish_giveaway_not_ready(self, client, sample_giveaway_data):
        """Test finishing giveaway that's not ready"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create giveaway but don't set finish messages
            create_response = client.post('/api/giveaways/create',
                                        json=sample_giveaway_data,
                                        content_type='application/json')
            giveaway_id = json.loads(create_response.data)['giveaway']['id']
            
            response = client.post(f'/api/giveaways/{giveaway_id}/finish')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] == False
            assert 'CANNOT_FINISH' in data['error_code']
    
    def test_get_giveaway_history(self, client, sample_giveaway_data):
        """Test getting giveaway history"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create a giveaway
            client.post('/api/giveaways/create',
                       json=sample_giveaway_data,
                       content_type='application/json')
            
            response = client.get('/api/giveaways/history/1')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert len(data['giveaways']) == 1
            assert 'pagination' in data
    
    def test_get_giveaway_stats(self, client, sample_giveaway_data):
        """Test getting giveaway statistics"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create giveaway
            create_response = client.post('/api/giveaways/create',
                                        json=sample_giveaway_data,
                                        content_type='application/json')
            giveaway_id = json.loads(create_response.data)['giveaway']['id']
            
            response = client.get(f'/api/giveaways/{giveaway_id}/stats')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert 'stats' in data
    
    def test_get_giveaway_by_token(self, client, sample_giveaway_data):
        """Test getting giveaway by result token"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create giveaway
            create_response = client.post('/api/giveaways/create',
                                        json=sample_giveaway_data,
                                        content_type='application/json')
            result_token = json.loads(create_response.data)['giveaway']['result_token']
            
            response = client.get(f'/api/giveaways/by-token/{result_token}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['giveaway']['title'] == 'Test Giveaway'
    
    def test_get_giveaway_by_invalid_token(self, client):
        """Test getting giveaway with invalid token"""
        response = client.get('/api/giveaways/by-token/invalid-token')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'Invalid result token format' in data['error']
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        with patch('services.AuthService.is_service_healthy') as mock_auth, \
             patch('services.ChannelService.is_service_healthy') as mock_channel, \
             patch('services.ParticipantService.is_service_healthy') as mock_participant, \
             patch('services.BotService.is_service_healthy') as mock_bot, \
             patch('services.MediaService.is_service_healthy') as mock_media:
            
            # Mock all services as healthy
            mock_auth.return_value = True
            mock_channel.return_value = True
            mock_participant.return_value = True
            mock_bot.return_value = True
            mock_media.return_value = True
            
            response = client.get('/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'healthy'
            assert data['service'] == 'telegive-giveaway'
    
    def test_rate_limiting(self, client, sample_giveaway_data):
        """Test rate limiting functionality"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # This test would need to be configured based on actual rate limits
            # For now, just test that the endpoint responds normally
            response = client.post('/api/giveaways/create',
                                 json=sample_giveaway_data,
                                 content_type='application/json')
            
            assert response.status_code in [201, 429]  # Either success or rate limited

class TestGiveawayModels:
    """Test class for Giveaway models"""
    
    @pytest.fixture
    def app_context(self):
        """Create application context for testing"""
        app.config.from_object(TestingConfig)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    def test_giveaway_creation(self, app_context):
        """Test Giveaway model creation"""
        giveaway = Giveaway(
            account_id=1,
            title='Test Giveaway',
            main_body='Test content',
            winner_count=2
        )
        
        db.session.add(giveaway)
        db.session.commit()
        
        assert giveaway.id is not None
        assert giveaway.result_token is not None
        assert giveaway.status == 'active'
        assert giveaway.created_at is not None
    
    def test_giveaway_to_dict(self, app_context):
        """Test Giveaway to_dict method"""
        giveaway = Giveaway(
            account_id=1,
            title='Test Giveaway',
            main_body='Test content',
            winner_count=2
        )
        
        db.session.add(giveaway)
        db.session.commit()
        
        giveaway_dict = giveaway.to_dict()
        
        assert 'id' in giveaway_dict
        assert 'title' in giveaway_dict
        assert 'status' in giveaway_dict
        assert 'result_token' not in giveaway_dict  # Not included by default
        
        # Test with sensitive data
        giveaway_dict_sensitive = giveaway.to_dict(include_sensitive=True)
        assert 'result_token' in giveaway_dict_sensitive
    
    def test_giveaway_status_methods(self, app_context):
        """Test Giveaway status checking methods"""
        giveaway = Giveaway(
            account_id=1,
            title='Test Giveaway',
            main_body='Test content'
        )
        
        assert giveaway.is_active() == True
        assert giveaway.is_finished() == False
        assert giveaway.can_publish() == True
        assert giveaway.can_finish() == False  # No message_id yet
        
        # Mark as published
        giveaway.mark_published(123456)
        assert giveaway.can_publish() == False
        
        # Set finish messages
        giveaway.set_finish_messages('conclusion', 'winner', 'loser')
        assert giveaway.can_finish() == True
        
        # Mark as finished
        giveaway.mark_finished(789012)
        assert giveaway.is_finished() == True
        assert giveaway.is_active() == False
    
    def test_giveaway_stats_creation(self, app_context):
        """Test GiveawayStats model"""
        giveaway = Giveaway(
            account_id=1,
            title='Test Giveaway',
            main_body='Test content'
        )
        db.session.add(giveaway)
        db.session.flush()
        
        stats = GiveawayStats(giveaway_id=giveaway.id)
        db.session.add(stats)
        db.session.commit()
        
        assert stats.id is not None
        assert stats.total_participants == 0
        assert stats.last_updated is not None
    
    def test_publishing_log_creation(self, app_context):
        """Test GiveawayPublishingLog model"""
        giveaway = Giveaway(
            account_id=1,
            title='Test Giveaway',
            main_body='Test content'
        )
        db.session.add(giveaway)
        db.session.flush()
        
        log_entry = GiveawayPublishingLog.log_publish_attempt(
            giveaway_id=giveaway.id,
            success=True,
            telegram_message_id=123456
        )
        db.session.add(log_entry)
        db.session.commit()
        
        assert log_entry.id is not None
        assert log_entry.action == 'publish'
        assert log_entry.success == True
        assert log_entry.telegram_message_id == 123456

class TestUtilities:
    """Test class for utility functions"""
    
    def test_giveaway_validator(self):
        """Test GiveawayValidator utility"""
        from utils import GiveawayValidator
        
        # Test valid data
        valid_data = {
            'account_id': 1,
            'title': 'Valid Title',
            'main_body': 'This is a valid main body with enough content.',
            'winner_count': 3
        }
        
        result = GiveawayValidator.validate_giveaway_creation(valid_data)
        assert result['valid'] == True
        
        # Test invalid data
        invalid_data = {
            'account_id': 'invalid',
            'title': 'AB',  # Too short
            'main_body': 'Short',  # Too short
            'winner_count': 0  # Invalid
        }
        
        result = GiveawayValidator.validate_giveaway_creation(invalid_data)
        assert result['valid'] == False
        assert len(result['errors']) > 0
    
    def test_token_generator(self):
        """Test TokenGenerator utility"""
        from utils import TokenGenerator
        
        # Test result token generation
        token = TokenGenerator.generate_result_token(32)
        assert len(token) == 32
        assert TokenGenerator.validate_token_format(token, 32) == True
        
        # Test unique token generation
        def mock_check_function(token):
            return token == 'existing_token'
        
        unique_token = TokenGenerator.generate_unique_result_token(mock_check_function)
        assert unique_token != 'existing_token'
    
    def test_status_manager(self):
        """Test StatusManager utility"""
        from utils import StatusManager
        
        # Test valid status
        assert StatusManager.is_valid_status('active') == True
        assert StatusManager.is_valid_status('finished') == True
        assert StatusManager.is_valid_status('invalid') == False
        
        # Test transitions
        assert StatusManager.can_transition('active', 'finished') == True
        assert StatusManager.can_transition('finished', 'active') == False
        
        # Test validation
        result = StatusManager.validate_status_transition('active', 'finished')
        assert result['valid'] == True

