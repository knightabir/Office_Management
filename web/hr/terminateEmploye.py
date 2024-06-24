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


class TerminateEmployeHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('POST', 'OPTIONS')

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
            user_id = payload.get('id')
            company_id = payload.get('companyId')
            role = payload.get('userRole')

            if role != 'HR-1' and role != 'branchManager':
                code = 4001
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            # Convert body into json
            try:
                self.request.arguments = json.loads(self.request.body)

            except Exception as e:
                Log.i(e)
                code = 4100
                status = False
                message = 'Expected Request Type JSON.'
                raise Exception

            employeeId = self.request.arguments.get('employeeId')

            if employeeId is None or not employeeId:
                code = 4001
                message = 'Invalid - [ employeeId ]'
                status = False
                raise Exception

            try:
                employeeId = ObjectId(employeeId)
            except Exception as e:
                Log.i(e)
                code = 4001
                message = 'Invalid - [ employeeId ]'
                status = False
                raise Exception

            if not employeeId:
                code = 4001
                message = 'Invalid - [ employeeId ]'
                status = False
                raise Exception

            try:

                employee = await self.user.find_one({'_id': employeeId})

            except Exception as e:
                Log.i(e)
                code = 4001
                message = 'Invalid - [ employeeId ]'
                status = False
                raise Exception

            if employee is None:
                code = 4001
                message = 'Employee Not Found'
                status = False
                raise Exception

            try:
                output = await self.user.update_one(
                    {
                        '_id': employeeId
                    },
                    {
                        '$set':
                        {
                            'active': False, 'deleted': True, 'deletedAt': timeNow()
                        }
                    }
                )

                if output.modified_count < 1:
                    code = 4001
                    message = 'Employee Not Found'
                    status = False
                    raise Exception
                

                code = 2000
                status = True
                message = 'Employee Terminated'

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
