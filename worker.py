import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from app.db.session import SessionLocal
from app.services.event_engine import event_engine_service
from app.core.logging.setup import setup_logging

setup_logging()
logger = logging.getLogger("SANS_WORKER")

def scheduled_polling_job():
    db = SessionLocal()
    try:
        logger.info("Executing scheduled polling job...")
        event_engine_service.run_polling_workflow(db)
    except Exception as e:
        logger.error(f"[PollingJob] Execution error: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting standalone SANS Background Worker...")
    scheduler = BackgroundScheduler()
    
    # Run every 20 seconds
    scheduler.add_job(
        scheduled_polling_job, 
        'interval', 
        seconds=20, 
        id='sans_flight_poller', 
        replace_existing=True,
        max_instances=1
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully. Press Ctrl+C to exit.")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down background worker gracefully...")
        scheduler.shutdown()
