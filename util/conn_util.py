# Mongo Database Connection Class
import motor.motor_asyncio

from build_config import *


class MongoMixin(object):

    # def initUserDb():
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            CONFIG['database'][0]['host'],
            CONFIG['database'][0]['port'],
        )

        userDb = client[CONFIG['database'][0]['key']]
        client = None

        print('MONGO', '{} has been Initialized!'.format(CONFIG['database'][0]['key']))
    except:
        userDb = None
        print('MONGO', 'Ether Database has been Initialization Failed!')