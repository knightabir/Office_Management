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


class GetUserByRoleHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('OPTIONS', 'GET')

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
    obBoard = MongoMixin.userDb[
        CONFIG['database'][0]['table'][16]['name']
    ]

    def options(self):
        self.set_status(204)
        self.finish()

    async def get(self):
        code = 4100
        status = False
        message = ''
        result = []

        try:
            # get the token from header
            token = self.request.headers.get('Authorization')
            if token:
                token = token.replace('Bearer ', '')
            else:
                code = 4001
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception('Invalid Authorization')

            # decode the token
            payload = JWT_DECODE_1(token)
            if payload is None:
                code = 4001
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception('Invalid Authorization')

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

            # Only role with company and Branch Manager can add role
            if roleQ != 'company' and roleQ != 'branchManager':
                code = 4001
                message = 'You are not authorized to access this resource'
                status = False
                raise Exception('Unauthorized Access')

            userQ = self.user.find(
                {
                    '_id': ObjectId(user_id)
                }
            )

            user = []
            async for i in userQ:
                user.append(i)

            if not user:
                code = 404
                message = 'User not found'
                status = False
                raise Exception('User not found')

            branchId = user[0]['branchId']

            roleId = self.request.arguments.get('roleId')
            if roleId is None or not roleId:
                code = 4015
                message = 'Please Enter valid Role Id'
                raise Exception('Invalid Role Id')

            totalEmployeesQ = self.user.aggregate(
                [
                    {
                        '$match': {
                            'companyId': ObjectId(company_id),
                            'branchId': ObjectId(branchId),
                            'role': ObjectId(roleId)
                        }
                    },
                    {
                        '$project': {
                            '_id': {
                                '$toString': '$_id'
                            },
                            'firstname': '$personalInfo.firstName',
                            'lastName': '$personalInfo.lastName',
                            'email': '$email',
                            'phone': '$personalInfo.phone'
                        }
                    }
                ]
            )
            totalEmployees = []
            async for i in totalEmployeesQ:
                totalEmployees.append(i)

            if not totalEmployees:
                status = False
                code = 4032
                message = 'User List Is Empty'
            else:
                status = True
                code = 200
                message = 'Users Found.'
                result = totalEmployees

        except Exception as e:
            status = False
            if not message:
                template = 'Exception: {0}. Argument: {1!r}'
                code = 5010
                message = template.format(type(e).__name__, e.args)
                message = 'Internal Error, Please Contact the Support Team.'
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = exc_tb.tb_frame.f_code.co_filename
                Log.w('EXC', message)
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
            message = template.format(type(e).__name__, e.args)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = exc_tb.tb_frame.f_code.co_filename
            Log.w('EXC', message)
            Log.d('EX2', 'FILE: ' + str(fname) + ' LINE: ' + str(exc_tb.tb_lineno) + ' TYPE: ' + str(exc_type))
            response = {
                'code': code,
                'status': status,
                'message': message
            }
            self.write(json.loads(bdumps(response)))
            await self.finish()
