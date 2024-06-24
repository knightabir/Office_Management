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

class RuleHandler(tornado.web.RequestHandler, MongoMixin):

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
            
            userId = payload.get('userId')
            companyId = payload.get('companyId')
            role = payload.get('userRole')

            # Check if role is either "company" or "branchManager"
            if role not in ['company', 'branchManager']:
                code = 4003
                message = 'Unauthorized - Invalid Role'
                status = False
                raise Exception('Expectation Error: Unauthorized Role')

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
            
            name = self.request.arguments.get('name')
            if name is None or not len(name) or not isinstance(name, str):
                message = 'module name is not valid.'
                code = 4512
                raise Exception

            data = {
                'name': name,
                'companyId': ObjectId(companyId),
                'createdBy': ObjectId(userId),
                'updatedBy': None,
                'createdAt': timeNow(),
                'updatedAt': None
            }

            try:
                insert_result = await self.rule.insert_one(data)
                status = True
                code = 2000
                message = 'Rule created successfully.'
            except Exception as e:
                Log.i(e)
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

    async def get(self):
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
            
            userId = payload.get('userId')
            companyId = payload.get('companyId')
            role = payload.get('userRole')

            # Check if role is either "company" or "branchManager"
            if role not in ['company', 'branchManager']:
                code = 4003
                message = 'You are not authorized to perform this action.'
                status = False
                raise Exception('Expectation Error: Unauthorized Role')

            userQ = await self.user.find_one({'_id': ObjectId(userId)})

            try:
                #  match the companyId then return the rules id and name 
                ruleQ = self.rule.aggregate(
                    [
                        {
                            '$match': {
                                'companyId': ObjectId('66681a63ed55f1052413d85c')
                            }
                        }, {
                            '$project': {
                                '_id': {
                                    '$toString': '$_id'
                                }, 
                                'name': 1
                            }
                        }
                    ]
                )
                role = []
                async for i in ruleQ:
                    role.append(i)
                if not len(role):
                    code = 4005
                    message = 'No Rule found.'
                    status = False
                    raise Exception
                
                status = True
                code = 2000
                message = 'Rule fetched successfully.'
                result = role
            except Exception as e:
                Log.i(e)
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