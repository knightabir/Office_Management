import json
import sys
from datetime import datetime, timedelta
from lib.fernet_crypto import FN_ENCRYPT, FN_DECRYPT
import tornado.web
from bson import ObjectId
from build_config import CONFIG
from util.conn_util import MongoMixin
from util.log_util import Log
from util.time_util import timeNow
from bson.json_util import dumps as bdumps
from helper.jwt_helper import JWT_DECODE_1, JWT_ENCODE_1
from helper.decorators import all_origin

class ResignationHandler(tornado.web.RequestHandler, MongoMixin):

    SUPPORTED_METHODS = ('OPTIONS', 'PUT', 'POST','GET', 'DELETE')

    user = MongoMixin.userDb[
        CONFIG['database'][0]['table'][12]['name']
    ]

    company = MongoMixin.userDb[
        CONFIG['database'][0]['table'][13]['name']
    ]

    branch = MongoMixin.userDb[
        CONFIG['database'][0]['table'][14]['name']
    ]

    obBoard = MongoMixin.userDb[
        CONFIG['database'][0]['table'][16]['name']
    ]

    project = MongoMixin.userDb[
        CONFIG['database'][0]['table'][19]['name']
    ]

    rule = MongoMixin.userDb[
        CONFIG['database'][0]['table'][21]['name']
    ]

    user_role_map = MongoMixin.userDb[
        CONFIG['database'][0]['table'][22]['name']
    ]

    payGrade = MongoMixin.userDb[
        CONFIG['database'][0]['table'][20]['name']
    ]

    resignation = MongoMixin.userDb[
        CONFIG['database'][0]['table'][23]['name']
    ]


    def options(self):
        code = 4100
        status = False
        message = ''
        result = []


    async def post(self):
        code = 4100
        status = False
        message = ''
        result = []

        try:
            try:
                token = self.request.headers.get('Authorization')
                if token:
                    token = token.replace('Bearer ', '')
                else:
                    code = 4001
                    message = 'Invalid - [ Authorization ]'
                    status = False
                    raise Exception
            except:
                code = 4001
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            payload = JWT_DECODE_1(token)

            if payload is None:
                code = 4002
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            # get the user_id company_id and role from the token
            userId = payload.get('userId')
            companyId = payload.get('companyId')
            role = payload.get('userRole')

            try:
                self.request.arguments = json.loads(self.request.body)
            except Exception as e:
                code = 4003
                message = 'Expected request Type [ JSON ]'
                status = False
                raise Exception

            userQ = await self.user.find_one({'_id': ObjectId(userId)})
            if userQ is None:
                code = 4003
                message = 'Invalid - [ userId ]'
                status = False
                raise Exception
            
            branchId = userQ.get('branchId')
            if companyId is None:
                code = 4003
                message = 'Invalid - [ companyId ]'
                status = False
                raise Exception
            

            message = self.request.arguments.get('message')
            if message is None or not message or not isinstance(message, str):
                code = 4003
                message = 'Invalid - [ message ]'
                status = False
                raise Exception
            
            message = message.strip().title()

            date = self.request.arguments.get('date')
            if date is None or not date or not isinstance(date, str):
                code = 4003
                message = 'Invalid - [ date ]'
                status = False
                raise Exception



            data = {
                'userId': ObjectId(userId),
                'companyId': ObjectId(companyId),
                'branchId': ObjectId(branchId),
                'reason': message,
                'lastWorkingDate': date,
                'createdBy': ObjectId(userId),
                'createdOn': timeNow()
            }
            
            try: 
                self.user.update_many({'_id': ObjectId(userId)}, {'$set': {'isResigned': True,'active': False}})
                await self.resignation.insert_one(data)
                status = True
                message = 'Resignation Request Submitted Successfully.'
                code = 2000
            except Exception as e:
                code = 4004
                message = 'Internal Error, Please Contact the Support Team.'
                status = False
                raise Exception

        except Exception as e:
            status = False
            if not len(message):
                template = 'Exception: {0}. Argument: {1!r}'
                code = 5010
                iMessage = template.format(type(e).__name__, e.args)
                message = 'Internal Error, Please Contact the Support Team.'
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = exc_tb.tb_frame.f_code.co_filename
                Log.w('EXC', iMessage)
                Log.d('EX2', 'FILE: ' + str(fname) + ' LINE: ' + str(exc_tb.tb_lineno) + ' TYPE: ' + str(exc_type))

        response = {
            'code': code,
            'status': status,
            'message': message,
            'result': result
        }
        Log.d('RSP', response)
        try:
            self.write(json.loads(bdumps(response)))
            await self.finish()
            return
        except Exception as e:
            status = False
            template = 'Exception: {0}. Argument: {1!r}'
            code = 5011
            iMessage = template.format(type(e).__name__, e.args)
            message = 'Internal Error, Please Contact the Support Team.'
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = exc_tb.tb_frame.f_code.co_filename
            Log.w('EXC', iMessage)
            Log.d('EX2', 'FILE: ' + str(fname) + ' LINE: ' + str(exc_tb.tb_lineno) + ' TYPE: ' + str(exc_type))
            response = {
                'code': code,
                'status': status,
                'message': message
            }
            self.write(json.loads(bdumps(response)))
            await self.finish()