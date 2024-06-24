import json
import sys
from datetime import datetime, timedelta

import tornado.web
from bson import ObjectId
from build_config import CONFIG
from util.conn_util import MongoMixin
from util.log_util import Log
from util.time_util import timeNow
from bson.json_util import dumps as bdumps
from helper.jwt_helper import JWT_DECODE_1, JWT_ENCODE_1
from helper.decorators import all_origin

class AssignPayScaleHandler(tornado.web.RequestHandler, MongoMixin):

    SUPPORTED_METHODS = ('OPTIONS', 'PUT', 'POST')

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
    payScale = MongoMixin.userDb[
        CONFIG['database'][0]['table'][17]['name']
    ]

    attendance = MongoMixin.userDb[
        CONFIG['database'][0]['table'][18]['name']
    ]

    PayGrade = MongoMixin.userDb[
        CONFIG['database'][0]['table'][20]['name']
    ]

    def options(self):
        status = False
        code = 4100
        message = ''
        result = []

    async def post(self):
        code = 4100
        message = ''
        status = False
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

                # decode the token
                payload = JWT_DECODE_1(token)
                if payload is None:
                    code = 4001
                    message = 'Invalid - [ Authorization ]'
                    status = False
                    raise Exception
            except Exception as e:
                Log.i(e)
                code = 4001
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            # get the user_id company_id and role from the token
            # 'userId': '6668259eb27f0e68666fa3ba', 'companyId': '66681a63ed55f1052413d85c', 'userRole': 'branchManager'}
            userId = payload.get('userId')
            companyId = payload.get('companyId')
            role = payload.get('userRole')

            userQ = await self.user.find_one({'_id': ObjectId(userId)})
            # Convert the body into json          
            try:
                self.request.arguments = json.loads(self.request.body)
            except Exception as e:
                Log.i(e)
                code = 4002
                message = 'Expected Request Type JSON.'
                status = False
                raise Exception
            
            payScaleId = self.request.arguments.get('payScaleId')
            branchId = userQ.get('branchId')
            user_Id = self.request.arguments.get('user_Id')

            data = {
                'companyId': ObjectId(companyId),
                'branchId':ObjectId(branchId),
                'user_Id': ObjectId(user_Id),
                'payScale':[{
                    'payScaleId': ObjectId(payScaleId),
                    'isActive': True,
                    'creaatedAt': timeNow(),
                    'createdBy': ObjectId(userId),
                }],
                'isActive': True
            }

            try: 
                # print(data)
                await self.PayGrade.insert_one(data)
                code = 200
                status = True
                message = 'PayScale Assigned Successfully.'

            except Exception as e:
                Log.i(e)
                code = 4004
                message = 'Internal Error, Please Contact the Support Team.'
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