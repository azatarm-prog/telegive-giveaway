"""
ParticipantService - Integration with Participant Service
Handles participant management and winner selection
"""

import requests
import logging
from typing import Dict, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class ParticipantService:
    """Service for participant management and winner selection"""
    
    @staticmethod
    def get_service_headers() -> Dict[str, str]:
        """Get standard headers for inter-service communication"""
        return {
            'Content-Type': 'application/json',
            'X-Service-Name': 'telegive-giveaway'
        }
    
    @staticmethod
    def select_winners(giveaway_id: int, winner_count: int) -> Dict:
        """
        Select winners for a giveaway
        
        Args:
            giveaway_id: Giveaway ID
            winner_count: Number of winners to select
            
        Returns:
            Dict with winner selection results
        """
        try:
            participant_url = current_app.config['TELEGIVE_PARTICIPANT_URL']
            url = f"{participant_url}/api/participants/{giveaway_id}/select-winners"
            
            payload = {
                'winner_count': winner_count
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=ParticipantService.get_service_headers(),
                timeout=30  # Winner selection might take longer
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Winners selected for giveaway {giveaway_id}: {len(data.get('winners', []))} winners")
                return data
            else:
                logger.error(f"Winner selection failed for giveaway {giveaway_id}: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Winner selection failed: {response.status_code}',
                    'error_code': 'WINNER_SELECTION_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Participant service request failed: {e}")
            return {
                'success': False,
                'error': 'Participant service unavailable',
                'error_code': 'PARTICIPANT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in winner selection: {e}")
            return {
                'success': False,
                'error': 'Internal error during winner selection',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def get_participant_count(giveaway_id: int) -> Dict:
        """
        Get participant count for a giveaway
        
        Args:
            giveaway_id: Giveaway ID
            
        Returns:
            Dict with participant count info
        """
        try:
            participant_url = current_app.config['TELEGIVE_PARTICIPANT_URL']
            url = f"{participant_url}/api/participants/{giveaway_id}/count"
            
            response = requests.get(
                url,
                headers=ParticipantService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Participant count for giveaway {giveaway_id}: {data.get('total_participants', 0)}")
                return data
            else:
                logger.error(f"Participant count retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Participant count retrieval failed: {response.status_code}',
                    'error_code': 'PARTICIPANT_COUNT_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Participant service request failed: {e}")
            return {
                'success': False,
                'error': 'Participant service unavailable',
                'error_code': 'PARTICIPANT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in participant count: {e}")
            return {
                'success': False,
                'error': 'Internal error during participant count retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def get_participants(giveaway_id: int, page: int = 1, limit: int = 50) -> Dict:
        """
        Get participants for a giveaway
        
        Args:
            giveaway_id: Giveaway ID
            page: Page number
            limit: Results per page
            
        Returns:
            Dict with participants list
        """
        try:
            participant_url = current_app.config['TELEGIVE_PARTICIPANT_URL']
            url = f"{participant_url}/api/participants/{giveaway_id}"
            
            params = {
                'page': page,
                'limit': limit
            }
            
            response = requests.get(
                url,
                params=params,
                headers=ParticipantService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Participants for giveaway {giveaway_id} retrieved: page {page}")
                return data
            else:
                logger.error(f"Participants retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Participants retrieval failed: {response.status_code}',
                    'error_code': 'PARTICIPANTS_RETRIEVAL_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Participant service request failed: {e}")
            return {
                'success': False,
                'error': 'Participant service unavailable',
                'error_code': 'PARTICIPANT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in participants retrieval: {e}")
            return {
                'success': False,
                'error': 'Internal error during participants retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def get_winner_list(giveaway_id: int) -> Dict:
        """
        Get list of winners for a finished giveaway
        
        Args:
            giveaway_id: Giveaway ID
            
        Returns:
            Dict with winners list
        """
        try:
            participant_url = current_app.config['TELEGIVE_PARTICIPANT_URL']
            url = f"{participant_url}/api/participants/{giveaway_id}/winners"
            
            response = requests.get(
                url,
                headers=ParticipantService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Winners for giveaway {giveaway_id} retrieved: {len(data.get('winners', []))} winners")
                return data
            else:
                logger.error(f"Winners retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Winners retrieval failed: {response.status_code}',
                    'error_code': 'WINNERS_RETRIEVAL_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Participant service request failed: {e}")
            return {
                'success': False,
                'error': 'Participant service unavailable',
                'error_code': 'PARTICIPANT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in winners retrieval: {e}")
            return {
                'success': False,
                'error': 'Internal error during winners retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def get_participation_stats(giveaway_id: int) -> Dict:
        """
        Get detailed participation statistics
        
        Args:
            giveaway_id: Giveaway ID
            
        Returns:
            Dict with participation statistics
        """
        try:
            participant_url = current_app.config['TELEGIVE_PARTICIPANT_URL']
            url = f"{participant_url}/api/participants/{giveaway_id}/stats"
            
            response = requests.get(
                url,
                headers=ParticipantService.get_service_headers(),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                logger.info(f"Participation stats for giveaway {giveaway_id} retrieved")
                return data
            else:
                logger.error(f"Participation stats retrieval failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f'Participation stats retrieval failed: {response.status_code}',
                    'error_code': 'PARTICIPATION_STATS_FAILED'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Participant service request failed: {e}")
            return {
                'success': False,
                'error': 'Participant service unavailable',
                'error_code': 'PARTICIPANT_SERVICE_UNAVAILABLE'
            }
        except Exception as e:
            logger.error(f"Unexpected error in participation stats: {e}")
            return {
                'success': False,
                'error': 'Internal error during participation stats retrieval',
                'error_code': 'INTERNAL_ERROR'
            }
    
    @staticmethod
    def is_service_healthy() -> bool:
        """
        Check if participant service is healthy
        
        Returns:
            Boolean indicating service health
        """
        try:
            participant_url = current_app.config['TELEGIVE_PARTICIPANT_URL']
            url = f"{participant_url}/health"
            
            response = requests.get(url, timeout=5)
            return response.ok and response.json().get('status') == 'healthy'
            
        except Exception as e:
            logger.error(f"Participant service health check failed: {e}")
            return False

