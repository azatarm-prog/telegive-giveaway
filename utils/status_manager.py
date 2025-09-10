"""
StatusManager - Utility for managing giveaway status transitions
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class StatusManager:
    """Utility class for managing giveaway status transitions and validation"""
    
    # Valid giveaway statuses
    VALID_STATUSES = ['active', 'finished']
    
    # Valid status transitions
    VALID_TRANSITIONS = {
        'active': ['finished'],
        'finished': []  # No transitions from finished state
    }
    
    # Status descriptions
    STATUS_DESCRIPTIONS = {
        'active': 'Giveaway is active and accepting participants',
        'finished': 'Giveaway has been completed and winners have been selected'
    }
    
    @staticmethod
    def is_valid_status(status: str) -> bool:
        """
        Check if a status is valid
        
        Args:
            status: Status to validate
            
        Returns:
            Boolean indicating if status is valid
        """
        return status in StatusManager.VALID_STATUSES
    
    @staticmethod
    def can_transition(current_status: str, new_status: str) -> bool:
        """
        Check if a status transition is allowed
        
        Args:
            current_status: Current giveaway status
            new_status: Desired new status
            
        Returns:
            Boolean indicating if transition is allowed
        """
        if not StatusManager.is_valid_status(current_status):
            return False
        
        if not StatusManager.is_valid_status(new_status):
            return False
        
        # Same status is always allowed
        if current_status == new_status:
            return True
        
        # Check valid transitions
        allowed_transitions = StatusManager.VALID_TRANSITIONS.get(current_status, [])
        return new_status in allowed_transitions
    
    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> Dict:
        """
        Validate a status transition and return detailed results
        
        Args:
            current_status: Current giveaway status
            new_status: Desired new status
            
        Returns:
            Dict with validation results
        """
        # Check if current status is valid
        if not StatusManager.is_valid_status(current_status):
            return {
                'valid': False,
                'error': f'Invalid current status: {current_status}',
                'error_code': 'INVALID_CURRENT_STATUS'
            }
        
        # Check if new status is valid
        if not StatusManager.is_valid_status(new_status):
            return {
                'valid': False,
                'error': f'Invalid new status: {new_status}',
                'error_code': 'INVALID_NEW_STATUS'
            }
        
        # Check if transition is allowed
        if not StatusManager.can_transition(current_status, new_status):
            return {
                'valid': False,
                'error': f'Invalid status transition from {current_status} to {new_status}',
                'error_code': 'INVALID_STATUS_TRANSITION',
                'allowed_transitions': StatusManager.VALID_TRANSITIONS.get(current_status, [])
            }
        
        return {
            'valid': True,
            'current_status': current_status,
            'new_status': new_status,
            'description': StatusManager.STATUS_DESCRIPTIONS.get(new_status, '')
        }
    
    @staticmethod
    def get_status_description(status: str) -> str:
        """
        Get description for a status
        
        Args:
            status: Status to describe
            
        Returns:
            Status description string
        """
        return StatusManager.STATUS_DESCRIPTIONS.get(status, f'Unknown status: {status}')
    
    @staticmethod
    def get_allowed_transitions(current_status: str) -> List[str]:
        """
        Get list of allowed transitions from current status
        
        Args:
            current_status: Current status
            
        Returns:
            List of allowed next statuses
        """
        if not StatusManager.is_valid_status(current_status):
            return []
        
        return StatusManager.VALID_TRANSITIONS.get(current_status, [])
    
    @staticmethod
    def can_publish(giveaway) -> Tuple[bool, Optional[str]]:
        """
        Check if giveaway can be published
        
        Args:
            giveaway: Giveaway object
            
        Returns:
            Tuple of (can_publish, error_message)
        """
        if not giveaway:
            return False, "Giveaway not found"
        
        if giveaway.status != 'active':
            return False, f"Cannot publish giveaway with status: {giveaway.status}"
        
        if giveaway.message_id is not None:
            return False, "Giveaway has already been published"
        
        return True, None
    
    @staticmethod
    def can_finish(giveaway) -> Tuple[bool, Optional[str]]:
        """
        Check if giveaway can be finished
        
        Args:
            giveaway: Giveaway object
            
        Returns:
            Tuple of (can_finish, error_message)
        """
        if not giveaway:
            return False, "Giveaway not found"
        
        if giveaway.status != 'active':
            return False, f"Cannot finish giveaway with status: {giveaway.status}"
        
        if giveaway.message_id is None:
            return False, "Giveaway must be published before it can be finished"
        
        if not giveaway.messages_ready_for_finish:
            return False, "Finish messages must be configured before finishing giveaway"
        
        return True, None
    
    @staticmethod
    def can_update_finish_messages(giveaway) -> Tuple[bool, Optional[str]]:
        """
        Check if giveaway finish messages can be updated
        
        Args:
            giveaway: Giveaway object
            
        Returns:
            Tuple of (can_update, error_message)
        """
        if not giveaway:
            return False, "Giveaway not found"
        
        if giveaway.status != 'active':
            return False, f"Cannot update finish messages for giveaway with status: {giveaway.status}"
        
        return True, None
    
    @staticmethod
    def get_giveaway_lifecycle_stage(giveaway) -> str:
        """
        Get the current lifecycle stage of a giveaway
        
        Args:
            giveaway: Giveaway object
            
        Returns:
            Lifecycle stage string
        """
        if not giveaway:
            return 'unknown'
        
        if giveaway.status == 'finished':
            return 'finished'
        
        if giveaway.status == 'active':
            if giveaway.message_id is None:
                return 'created'
            elif not giveaway.messages_ready_for_finish:
                return 'published'
            else:
                return 'ready_to_finish'
        
        return 'unknown'
    
    @staticmethod
    def get_next_actions(giveaway) -> List[str]:
        """
        Get list of possible next actions for a giveaway
        
        Args:
            giveaway: Giveaway object
            
        Returns:
            List of possible action strings
        """
        if not giveaway:
            return []
        
        actions = []
        stage = StatusManager.get_giveaway_lifecycle_stage(giveaway)
        
        if stage == 'created':
            actions.append('publish')
        elif stage == 'published':
            actions.append('configure_finish_messages')
        elif stage == 'ready_to_finish':
            actions.append('finish')
        
        # Always allow viewing stats and history
        if giveaway.status == 'active':
            actions.append('view_stats')
        elif giveaway.status == 'finished':
            actions.extend(['view_stats', 'view_results'])
        
        return actions
    
    @staticmethod
    def log_status_change(giveaway_id: int, old_status: str, new_status: str, 
                         changed_by: Optional[str] = None, reason: Optional[str] = None):
        """
        Log a status change for audit purposes
        
        Args:
            giveaway_id: Giveaway ID
            old_status: Previous status
            new_status: New status
            changed_by: Who made the change
            reason: Reason for the change
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        log_message = (
            f"Giveaway {giveaway_id} status changed from '{old_status}' to '{new_status}' "
            f"at {timestamp}"
        )
        
        if changed_by:
            log_message += f" by {changed_by}"
        
        if reason:
            log_message += f" (reason: {reason})"
        
        logger.info(log_message)
    
    @staticmethod
    def validate_giveaway_state(giveaway) -> Dict:
        """
        Validate the overall state of a giveaway
        
        Args:
            giveaway: Giveaway object
            
        Returns:
            Dict with validation results
        """
        if not giveaway:
            return {
                'valid': False,
                'error': 'Giveaway not found',
                'error_code': 'GIVEAWAY_NOT_FOUND'
            }
        
        issues = []
        warnings = []
        
        # Check status validity
        if not StatusManager.is_valid_status(giveaway.status):
            issues.append(f'Invalid status: {giveaway.status}')
        
        # Check consistency between status and other fields
        if giveaway.status == 'finished':
            if giveaway.finished_at is None:
                issues.append('Finished giveaway missing finished_at timestamp')
            
            if giveaway.conclusion_message_id is None:
                warnings.append('Finished giveaway missing conclusion message ID')
        
        if giveaway.status == 'active':
            if giveaway.finished_at is not None:
                issues.append('Active giveaway has finished_at timestamp')
            
            if giveaway.conclusion_message_id is not None:
                issues.append('Active giveaway has conclusion message ID')
        
        # Check message readiness
        if giveaway.messages_ready_for_finish:
            required_messages = ['public_conclusion_message', 'winner_message', 'loser_message']
            for msg_field in required_messages:
                if not getattr(giveaway, msg_field):
                    issues.append(f'Missing {msg_field} despite messages_ready_for_finish being True')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'lifecycle_stage': StatusManager.get_giveaway_lifecycle_stage(giveaway),
            'next_actions': StatusManager.get_next_actions(giveaway)
        }

