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


class GetAnyUserHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('OPTIONS', 'POST', 'PUT', 'GET')

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
        CONFIG['database'][0]['table'][15]['name']
    ]

    def options(self):
        code = 4100
        status = False
        message = ''
        result = []

    async def get(self):
        code = 4100
        status = False
        message = ''
        result = []

        try:

            try:
                # get the authorizon token
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

            # get the id and role from the token

            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            role = payload.get('userRole')

            if role != 'branchManager':
                code = 4001
                message = 'you are not authorized to to access this resource'
                status = False
                raise Exception
            
            else:
                try:
                    # Converts the body into json
                    self.request.arguments = json.loads(self.request.body)

                except Exception as e:
                    code = 4100
                    status = False
                    message = 'Expected Request Type JSON.'
                    raise Exception
                
                userId = self.request.arguments.get('userId')

                if userId is None or not userId or not isinstance(userId, str):
                    code = 4512
                    status = False
                    message = 'user id is not valid.'
                    raise Exception
                try:
                    user = await self.user.find_one({'_id':ObjectId(userId)})
                except Exception as e:
                    Log.i(e)
                    code = 4512
                    status = False
                    message = 'Internal Server Error. Please Contact the Support Team.'
                    raise Exception
                
                try:
                    userQ = self.user.aggregate(
                        [{
                            '$match': {
                                '_id': ObjectId(userId)
                            }
                        }, {
                            '$lookup': {
                                'from': 'company', 
                                'localField': 'companyId', 
                                'foreignField': '_id', 
                                'as': 'companyData'
                            }
                        }, {
                            '$unwind': '$companyData'
                        }, {
                            '$lookup': {
                                'from': 'branch', 
                                'localField': 'branchId', 
                                'foreignField': '_id', 
                                'as': 'branchData'
                            }
                        }, {
                            '$unwind': '$branchData'
                        }, {
                            '$lookup': {
                                'from': 'role', 
                                'localField': 'role', 
                                'foreignField': '_id', 
                                'as': 'role'
                            }
                        }, {
                            '$unwind': '$role'
                        }, {
                            '$project': {
                                '_id': {
                                    '$toString': '$_id'
                                }, 
                                'companyName': '$companyData.companyName', 
                                'branchName': '$branchData.branchName', 
                                'firstName': '$personalInfo.firstName', 
                                'lastname': '$personalInfo.lastName', 
                                'email': '$email', 
                                'phoone': '$personalInfo.phone', 
                                'Designation': '$role.role'
                            }
                        }])
                    
                    user = []
                    async for i in userQ:
                        user.append(i)

                    if user is None:
                        code = 4512
                        status = False
                        message = 'user not found.'
                        raise Exception
                    
                    code = 2000
                    message = 'User Found.'
                    result = user
                    status = True
                except Exception as e:
                    Log.i(e)
                    code = 4512
                    status = False
                    message = 'Internal Server Error. Please Contact the Support Team.'
                    raise Exception
                    
                if user is None:
                    code = 4512
                    status = False
                    message = 'user not found.'
                    raise Exception
                else:
                    code = 2000
                    message = 'user found.'
                    result = user
                    status = True

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