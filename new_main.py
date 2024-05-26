from loguru import logger
from libs.rover import Rover

logger.info("Starting Autonomous...")
remi = Rover()

# this generally shouldn't happen unless the Rover first specifies
logger.warning("Autonomous code ended. Main thread exiting...")
logger.warning("Make sure to use Ctrl^C if other threads continue to run.")
exit(0)