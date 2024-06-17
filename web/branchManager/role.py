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


class RoleHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('POST', 'OPTIONS', 'GET')

    user = MongoMixin.userDb[
        CONFIG['database'][0]['table'][12]['name']
    ]
    role = MongoMixin.userDb[
        CONFIG['database'][0]['table'][15]['name']
    ]
    company = MongoMixin.userDb[
        CONFIG['database'][0]['table'][13]['name']
    ]

    branch = MongoMixin.userDb[
        CONFIG['database'][0]['table'][14]['name']
    ]

    def options(self):
        code = 4100
        message = ''
        status = False
        result = []

    async def post(self):
        code = 4100
        message = ''
        status = False
        result = []

        try:
            try:
                # get the token from header
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

            try:
                self.request.arguments = json.loads(self.request.body)

            except Exception as e:
                code = 4100
                status = False
                message = 'Expected Request Type JSON.'
                raise Exception

            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            roleQ = payload.get('userRole')

            #  only role with company and Branch Manager can add role

            if roleQ != 'company' and roleQ != 'branchManager':
                code = 4001
                message = 'you are not authorized to to access this resource'
                status = False
                raise Exception

            role = self.request.arguments.get('role')
            if role is None or not role or isinstance(role, str):
                code = 4787
                message = 'Please Enter valid role.'
                raise Exception

            data = {
                'companyId': ObjectId(company_id),
                'userId': ObjectId(user_id),
                'role': role
            }
            try:
                self.role.insert_one(data)
                code = 2000
                status = True
                message = 'Role created successfully'

            except Exception as e:
                code = 4100
                status = False
                message = 'Internal Server Error'

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
                # Get the token from header
                token = self.request.headers.get('Authorization')
                if token:
                    token = token.replace('Bearer ', '')
                else:
                    code = 4001
                    message = 'Invalid - [ Authorization ]'
                    status = False
                    raise Exception

                # Decode the token
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

            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            roleQ = payload.get('userRole')

            # Only role with company and Branch Manager can add role
            if roleQ != 'company' and roleQ != 'branchManager':
                code = 4001
                message = 'You are not authorized to access this resource'
                status = False
                raise Exception

            try:
                # Get all the roles where companyId = company_id
                roleQ = self.role.aggregate([
                    {
                        '$match': {
                            'companyId': ObjectId(company_id)
                        }
                    },
                    {
                        '$group': {
                            '_id': '$_id',
                            'role': {
                                '$first': '$role'
                            }
                        }
                    },
                    {
                        '$project': {
                            '_id': {
                                '$toString': '$_id'
                            },
                            'role': 1
                        }
                    }
                ])

                role = []
                async for document in roleQ:
                    if document['role'] == "company":
                        continue
                    role.append(document)

                if not role:
                    code = 4100
                    status = False
                    message = 'Role not found'
                    raise Exception
                else:
                    code = 200
                    status = True
                    message = 'Role found successfully'
                    result = role
            except Exception as e:
                Log.i(e)
                code = 4100
                status = False
                message = 'Internal Server Error'
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