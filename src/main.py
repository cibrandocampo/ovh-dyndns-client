import time
import schedule

from infrastructure.config import Config
from infrastructure.logger import Logger
from application.controller import UpdateDnsController

logger = Logger.get_logger()
config = Config()
controller = UpdateDnsController()

def execute_main_controller() -> None:
    """
    Executes the DNS update controller handler.
    
    Catches and logs runtime errors if the controller fails to execute.
    """
    
    try:
        logger.info("Executing DNS update controller")
        controller.handler()
        logger.info("DNS update completed successfully")
    except RuntimeError as e:
        logger.error(f"Controller execution failed: {e}")

if __name__ == "__main__":
    """
    Main entry point of the application. Schedules periodic execution of the controller
    and ensures that the scheduler runs continuously.
    """
    
    # Initialize logger and config
    logger.info("Starting OVH DynDNS client")
    
    execute_main_controller()
    
    logger.info(f"Scheduling updates every {config.update_ip_interval} seconds")
    schedule.every(config.update_ip_interval).seconds.do(execute_main_controller)
    logger.info("Scheduler configured")

    # Run the scheduler in an infinite loop
    while True:
        schedule.run_pending()
        time.sleep(10)
