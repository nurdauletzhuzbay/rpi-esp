import logging
from urllib.parse import quote_plus

import pymongo as pm

MONGO_HOST = "192.168.8.95:27017/?directConnection=true"
MONGO_PASS = "chlen"
MONGO_USER = "mnogo"

class DbController:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DbController, cls).__new__(cls)
            cls._instance.__initialize_client()
        return cls._instance

    def __initialize_client(self):
        try:
            uri = "mongodb://%s:%s@%s" % (quote_plus(MONGO_USER), quote_plus(MONGO_PASS), MONGO_HOST)
            _mongo_client = pm.MongoClient(uri)
            # _mongo_client = pm.MongoClient(MONGO_HOST, MONGO_PORT)
        except:
            logging.error('Mongo DB connection failed: %s', MONGO_HOST)
            raise Exception('Mongo DB connection failed')

        self.__ecom = _mongo_client.ecom


    def update_order_status_by_id(self, order_id, status):
        the_order = {'state': status}
        self.__ecom.orders.update_one({'_id': order_id}, {"$set": the_order})

    def set_sku_in_order_status_by_id(self, order_id, status):
        order = self.__ecom.orders.find_one({'_id': order_id})
        for item in order['item_list']:
            item['status'] = status
        self.__ecom.orders.update_one({'_id': order_id}, {"$set": order})

    def update_robot_status(self, status):
        the_robot = {'status': status}
        self.__ecom.robots.update_one({'robot_id': "1"}, {"$set": the_robot})
