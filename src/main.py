import time
import schedule

from infrastructure.config import Config
from infrastructure.logger import Logger
from application.controller import UpdateDnsController

logger = Logger.get_logger()
config = Config()

def execute_main_controller():
    """
    Executes the main controller logic by invoking the handler method of UpdateDnsController.

    Catches and logs runtime errors if the controller fails to execute.
    """
    
    try:
        logger.info("Executing UpdateDnsController handler")
        UpdateDnsController().handler()
        logger.info("UpdateDnsController executed successfully")
    except RuntimeError as e:
        logger.error(f"Failed to execute controller: {e}")

if __name__ == "__main__":
    """
    Main entry point of the application. Schedules periodic execution of the controller
    and ensures that the scheduler runs continuously.
    """
    
    # Initialize logger and config
    logger.info("Starting ovh-dyndns application")
    
    execute_main_controller()
    
    execution_interval = config.get('system_settings', 'check_interval')
    logger.info(f"Configuring Scheduler to execute controller every {execution_interval} minutes")
    schedule.every(execution_interval).minutes.do(execute_main_controller)
    logger.info("Scheduler service configured.")

    # Run the scheduler in an infinite loop
    while True:
        schedule.run_pending()
        time.sleep(1)
