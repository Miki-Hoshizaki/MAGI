from .base import *

import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# import development or production settings based on the env
if os.getenv("MAGI_DEPLOYMENT") == "production":
    from .production import *
else:
    from .development import *