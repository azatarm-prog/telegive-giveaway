"""
Cleanup tasks for the Giveaway Management Service
Handles scheduled cleanup operations and maintenance tasks
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
import logging
import atexit

from app import app, db
from models import Giveaway, GiveawayStats, GiveawayPublishingLog
from services import MediaService

logger = logging.getLogger(__name__)

class CleanupTasks:
    """Scheduled cleanup and maintenance tasks"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        atexit.register(lambda: self.scheduler.shutdown())
        
        # Schedule tasks
        self._schedule_tasks()
    
    def _schedule_tasks(self):
        """Schedule all cleanup tasks"""
        
        # Update giveaway statistics every 5 minutes
        self.scheduler.add_job(
            func=self.update_giveaway_statistics,
            trigger="interval",
            minutes=5,
            id='update_stats',
            name='Update Giveaway Statistics'
        )
        
        # Clean up old publishing logs every hour
        self.scheduler.add_job(
            func=self.cleanup_old_logs,
            trigger="interval",
            hours=1,
            id='cleanup_logs',
            name='Cleanup Old Publishing Logs'
        )
        
        # Check media cleanup status every 10 minutes
        self.scheduler.add_job(
            func=self.check_media_cleanup_status,
            trigger="interval",
            minutes=10,
            id='check_media_cleanup',
            name='Check Media Cleanup Status'
        )
        
        # Health check for external services every 30 minutes
        self.scheduler.add_job(
            func=self.health_check_services,
            trigger="interval",
            minutes=30,
            id='health_check',
            name='Health Check External Services'
        )
        
        logger.info("Cleanup tasks scheduled successfully")
    
    def update_giveaway_statistics(self):
        """Update statistics for active giveaways"""
        try:
            with app.app_context():
                # Get all active published giveaways
                active_giveaways = Giveaway.query.filter(
                    Giveaway.status == 'active',
                    Giveaway.message_id.isnot(None)
                ).all()
                
                updated_count = 0
                
                for giveaway in active_giveaways:
                    try:
                        # Get current participant stats from Participant Service
                        from services import ParticipantService
                        
                        participant_stats = ParticipantService.get_participation_stats(giveaway.id)
                        
                        if participant_stats.get('success', False):
                            stats_data = participant_stats.get('stats', {})
                            
                            # Update or create stats record
                            stats = GiveawayStats.get_or_create(giveaway.id)
                            stats.update_participants(
                                total_participants=stats_data.get('total_participants', 0),
                                captcha_completed=stats_data.get('captcha_completed_participants', 0)
                            )
                            
                            updated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to update stats for giveaway {giveaway.id}: {e}")
                        continue
                
                if updated_count > 0:
                    db.session.commit()
                    logger.info(f"Updated statistics for {updated_count} active giveaways")
                
        except Exception as e:
            logger.error(f"Error in update_giveaway_statistics task: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def cleanup_old_logs(self):
        """Clean up old publishing logs (keep last 30 days)"""
        try:
            with app.app_context():
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
                
                # Delete old logs
                deleted_count = GiveawayPublishingLog.query.filter(
                    GiveawayPublishingLog.created_at < cutoff_date
                ).delete()
                
                if deleted_count > 0:
                    db.session.commit()
                    logger.info(f"Cleaned up {deleted_count} old publishing logs")
                
        except Exception as e:
            logger.error(f"Error in cleanup_old_logs task: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def check_media_cleanup_status(self):
        """Check and update media cleanup status"""
        try:
            with app.app_context():
                # Get giveaways with scheduled media cleanup
                giveaways_with_media = Giveaway.query.filter(
                    Giveaway.media_file_id.isnot(None),
                    Giveaway.media_cleanup_status == 'scheduled'
                ).all()
                
                updated_count = 0
                
                for giveaway in giveaways_with_media:
                    try:
                        # Check cleanup status with Media Service
                        cleanup_status = MediaService.get_cleanup_status(giveaway.media_file_id)
                        
                        if cleanup_status.get('success', False):
                            status_data = cleanup_status.get('status', {})
                            new_status = status_data.get('cleanup_status', 'scheduled')
                            
                            if new_status != giveaway.media_cleanup_status:
                                giveaway.media_cleanup_status = new_status
                                if new_status in ['completed', 'failed']:
                                    giveaway.media_cleanup_timestamp = datetime.now(timezone.utc)
                                updated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to check media cleanup for giveaway {giveaway.id}: {e}")
                        continue
                
                if updated_count > 0:
                    db.session.commit()
                    logger.info(f"Updated media cleanup status for {updated_count} giveaways")
                
        except Exception as e:
            logger.error(f"Error in check_media_cleanup_status task: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def health_check_services(self):
        """Perform health check on external services"""
        try:
            from services import AuthService, ChannelService, ParticipantService, BotService, MediaService
            
            services = {
                'auth_service': AuthService,
                'channel_service': ChannelService,
                'participant_service': ParticipantService,
                'bot_service': BotService,
                'media_service': MediaService
            }
            
            healthy_services = []
            unhealthy_services = []
            
            for service_name, service_class in services.items():
                try:
                    is_healthy = service_class.is_service_healthy()
                    if is_healthy:
                        healthy_services.append(service_name)
                    else:
                        unhealthy_services.append(service_name)
                except Exception as e:
                    logger.error(f"Health check failed for {service_name}: {e}")
                    unhealthy_services.append(service_name)
            
            if unhealthy_services:
                logger.warning(f"Unhealthy services detected: {', '.join(unhealthy_services)}")
            else:
                logger.info(f"All services healthy: {', '.join(healthy_services)}")
                
        except Exception as e:
            logger.error(f"Error in health_check_services task: {e}")
    
    def cleanup_finished_giveaways(self):
        """Clean up data for very old finished giveaways (optional maintenance)"""
        try:
            with app.app_context():
                # Clean up giveaways finished more than 1 year ago
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=365)
                
                old_giveaways = Giveaway.query.filter(
                    Giveaway.status == 'finished',
                    Giveaway.finished_at < cutoff_date
                ).all()
                
                cleaned_count = 0
                
                for giveaway in old_giveaways:
                    try:
                        # Clean up associated data but keep the giveaway record
                        # Delete old stats (keep the record but reset counters)
                        stats = GiveawayStats.query.filter_by(giveaway_id=giveaway.id).first()
                        if stats:
                            # Archive stats or reset to minimal data
                            stats.total_participants = 0
                            stats.captcha_completed_participants = 0
                            stats.messages_delivered = 0
                        
                        cleaned_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to clean up giveaway {giveaway.id}: {e}")
                        continue
                
                if cleaned_count > 0:
                    db.session.commit()
                    logger.info(f"Cleaned up data for {cleaned_count} old finished giveaways")
                
        except Exception as e:
            logger.error(f"Error in cleanup_finished_giveaways task: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def get_task_status(self):
        """Get status of all scheduled tasks"""
        jobs = self.scheduler.get_jobs()
        
        task_status = []
        for job in jobs:
            task_status.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return task_status
    
    def run_task_manually(self, task_id):
        """Manually run a specific task"""
        try:
            job = self.scheduler.get_job(task_id)
            if job:
                job.func()
                return True
            else:
                logger.error(f"Task {task_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error running task {task_id} manually: {e}")
            return False
    
    def stop_scheduler(self):
        """Stop the task scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Task scheduler stopped")

# Global instance
cleanup_tasks = None

def initialize_cleanup_tasks():
    """Initialize the cleanup tasks scheduler"""
    global cleanup_tasks
    
    if cleanup_tasks is None:
        try:
            cleanup_tasks = CleanupTasks()
            logger.info("Cleanup tasks initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cleanup tasks: {e}")
    
    return cleanup_tasks

def get_cleanup_tasks():
    """Get the cleanup tasks instance"""
    global cleanup_tasks
    return cleanup_tasks

