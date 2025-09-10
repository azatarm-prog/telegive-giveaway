"""
Performance tests for the Giveaway Management Service
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from app import app, db
from models import Giveaway, GiveawayStats
from config import TestingConfig

class TestPerformance:
    """Performance test class"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app.config.from_object(TestingConfig)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    def test_database_query_performance(self, client):
        """Test database query performance"""
        with app.app_context():
            # Create multiple giveaways
            giveaways = []
            for i in range(100):
                giveaway = Giveaway(
                    account_id=i % 10,  # 10 different accounts
                    title=f'Test Giveaway {i}',
                    main_body=f'Content for giveaway {i}',
                    winner_count=1
                )
                giveaways.append(giveaway)
            
            db.session.add_all(giveaways)
            db.session.commit()
            
            # Test query performance
            start_time = time.time()
            
            # Query active giveaways for each account
            for account_id in range(10):
                active_giveaway = Giveaway.query.filter_by(
                    account_id=account_id,
                    status='active'
                ).first()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should complete within reasonable time
            assert query_time < 1.0, f"Query took too long: {query_time}s"
    
    def test_concurrent_giveaway_creation(self, client):
        """Test concurrent giveaway creation"""
        def create_giveaway(account_id):
            with patch('services.AuthService.validate_account') as mock_auth:
                mock_auth.return_value = {'success': True, 'account': {'id': account_id}}
                
                giveaway_data = {
                    'account_id': account_id,
                    'title': f'Test Giveaway {account_id}',
                    'main_body': 'Test content for concurrent creation',
                    'winner_count': 1
                }
                
                response = client.post('/api/giveaways/create',
                                     json=giveaway_data,
                                     content_type='application/json')
                return response.status_code
        
        # Test concurrent creation with different accounts
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(create_giveaway, i)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All should succeed
        assert all(status == 201 for status in results)
        # Should complete within reasonable time
        assert total_time < 5.0, f"Concurrent creation took too long: {total_time}s"
    
    def test_api_response_time(self, client):
        """Test API response times"""
        with patch('services.AuthService.validate_account') as mock_auth:
            mock_auth.return_value = {'success': True, 'account': {'id': 1}}
            
            # Create a giveaway first
            giveaway_data = {
                'account_id': 1,
                'title': 'Performance Test Giveaway',
                'main_body': 'Testing API response times',
                'winner_count': 1
            }
            
            # Test creation time
            start_time = time.time()
            response = client.post('/api/giveaways/create',
                                 json=giveaway_data,
                                 content_type='application/json')
            creation_time = time.time() - start_time
            
            assert response.status_code == 201
            assert creation_time < 2.0, f"Creation took too long: {creation_time}s"
            
            # Test retrieval time
            start_time = time.time()
            response = client.get('/api/giveaways/active/1')
            retrieval_time = time.time() - start_time
            
            assert response.status_code == 200
            assert retrieval_time < 1.0, f"Retrieval took too long: {retrieval_time}s"
    
    def test_health_check_performance(self, client):
        """Test health check response time"""
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
            
            start_time = time.time()
            response = client.get('/health')
            health_check_time = time.time() - start_time
            
            assert response.status_code == 200
            assert health_check_time < 0.5, f"Health check took too long: {health_check_time}s"
    
    def test_bulk_data_handling(self, client):
        """Test handling of bulk data operations"""
        with app.app_context():
            # Create many giveaways
            giveaways = []
            for i in range(1000):
                giveaway = Giveaway(
                    account_id=i % 100,  # 100 different accounts
                    title=f'Bulk Test Giveaway {i}',
                    main_body=f'Bulk test content {i}',
                    winner_count=1
                )
                giveaways.append(giveaway)
            
            start_time = time.time()
            db.session.add_all(giveaways)
            db.session.commit()
            bulk_insert_time = time.time() - start_time
            
            assert bulk_insert_time < 5.0, f"Bulk insert took too long: {bulk_insert_time}s"
            
            # Test bulk query
            start_time = time.time()
            all_giveaways = Giveaway.query.all()
            bulk_query_time = time.time() - start_time
            
            assert len(all_giveaways) == 1000
            assert bulk_query_time < 2.0, f"Bulk query took too long: {bulk_query_time}s"
    
    def test_memory_usage(self, client):
        """Test memory usage during operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        with app.app_context():
            # Perform memory-intensive operations
            giveaways = []
            for i in range(500):
                giveaway = Giveaway(
                    account_id=i % 50,
                    title=f'Memory Test Giveaway {i}',
                    main_body=f'Memory test content {i}' * 10,  # Larger content
                    winner_count=1
                )
                giveaways.append(giveaway)
            
            db.session.add_all(giveaways)
            db.session.commit()
            
            # Query all giveaways
            all_giveaways = Giveaway.query.all()
            giveaway_dicts = [g.to_dict() for g in all_giveaways]
            
            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100 * 1024 * 1024, f"Memory usage too high: {memory_increase} bytes"
    
    def test_concurrent_api_requests(self, client):
        """Test concurrent API requests"""
        def make_health_request():
            with patch('services.AuthService.is_service_healthy') as mock_auth:
                mock_auth.return_value = True
                response = client.get('/health')
                return response.status_code
        
        start_time = time.time()
        
        # Make 20 concurrent health check requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(20):
                future = executor.submit(make_health_request)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All should succeed
        assert all(status == 200 for status in results)
        # Should handle concurrent requests efficiently
        assert total_time < 3.0, f"Concurrent requests took too long: {total_time}s"
    
    def test_database_connection_pool(self, client):
        """Test database connection pool performance"""
        def make_database_query():
            with app.app_context():
                # Simple query to test connection pool
                count = Giveaway.query.count()
                return count
        
        # Create some test data first
        with app.app_context():
            for i in range(10):
                giveaway = Giveaway(
                    account_id=i,
                    title=f'Pool Test Giveaway {i}',
                    main_body='Pool test content',
                    winner_count=1
                )
                db.session.add(giveaway)
            db.session.commit()
        
        start_time = time.time()
        
        # Make concurrent database queries
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for _ in range(15):
                future = executor.submit(make_database_query)
                futures.append(future)
            
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All should return the same count
        assert all(count == 10 for count in results)
        # Should handle concurrent DB access efficiently
        assert total_time < 2.0, f"Concurrent DB access took too long: {total_time}s"
    
    def test_token_generation_performance(self):
        """Test token generation performance"""
        from utils import TokenGenerator
        
        start_time = time.time()
        
        # Generate many tokens
        tokens = []
        for _ in range(1000):
            token = TokenGenerator.generate_result_token(32)
            tokens.append(token)
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # All tokens should be unique
        assert len(set(tokens)) == 1000
        # Should generate tokens quickly
        assert generation_time < 1.0, f"Token generation took too long: {generation_time}s"
    
    def test_validation_performance(self):
        """Test validation performance"""
        from utils import GiveawayValidator
        
        test_data = {
            'account_id': 1,
            'title': 'Performance Test Giveaway',
            'main_body': 'This is a test giveaway for performance testing',
            'winner_count': 5
        }
        
        start_time = time.time()
        
        # Perform many validations
        for _ in range(1000):
            result = GiveawayValidator.validate_giveaway_creation(test_data)
            assert result['valid'] == True
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # Should validate quickly
        assert validation_time < 1.0, f"Validation took too long: {validation_time}s"

