import json
import sys
from datetime import datetime, timedelta

import tornado.web
from bson import ObjectId
from build_config import CONFIG
from lib.fernet_crypto import FN_DECRYPT
from util.conn_util import MongoMixin
from util.log_util import Log
from util.time_util import timeNow
from bson.json_util import dumps as bdumps
from helper.jwt_helper import JWT_DECODE_1, JWT_ENCODE_1
from helper.decorators import all_origin


class AddEmployeeHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('POST', 'OPTIONS')

    user = MongoMixin.userDb[
        CONFIG['database'][0]['table'][12]['name']
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

            # get the id and role from the token

            userId = payload.get('userId')
            company = payload.get('userRole')

            if company != 'branchManager':
                code = 4001
                message = 'you are not authorized to to access this resource'
                status = False
                raise Exception
            else:
                try:
                    # converts the body into json
                    self.request.arguments = json.loads(self.request.body)

                except Exception as e:
                    code = 4100
                    status = False
                    message = 'Expected Request Type JSON.'
                    raise Exception

                # I have user id from the database i need to find the company and branch id

                companyIdQ = await self.user.find_one(
                    {'_id': ObjectId(userId)},
                    limit=1
                )

                if not companyIdQ:
                    code = 4201
                    status = False
                    message = 'User not found.'
                    raise Exception
                companyId = companyIdQ.get('companyId')
                branchId = companyIdQ.get('branchId')

                firstName = self.request.arguments.get('firstName')
                if firstName is None or not firstName or not isinstance(firstName, str):
                    code = 4323
                    message = 'Please Enter valid First Name.'
                    raise Exception
                firstName = firstName.strip().title()

                lastName = self.request.arguments.get('lastName')
                if lastName is None or not lastName or not isinstance(lastName, str):
                    code = 6587
                    message = 'Please Enter valid last Name.'
                    raise Exception
                lastName = lastName.strip().title()

                phone = self.request.arguments.get('phone')
                if phone is None or not phone or len(phone) != 10 or not isinstance(phone, str):
                    code = 6548
                    message = 'Please Enter valid Phone.'
                    raise Exception
                phone = phone.strip()

                email = self.request.arguments.get('email')
                if email is None or not email or not isinstance(email, str):
                    code = 4587
                    message = 'Please Enter valid Email.'
                    raise Exception
                email = email.strip().lower()

                emailDB = await self.user.find_one(
                    {
                        "email": email
                    },
                    limit=1
                )
                if emailDB:
                    code = 4587
                    message = 'email already registered.'
                    status = False
                    raise Exception

                password = self.request.arguments.get('password')
                if password is None or not password:
                    code = 4585
                    message = 'Please enter valid Password'
                    raise Exception
                password = FN_DECRYPT(password)

                role = self.request.arguments.get('role')
                if role is None or not role or not isinstance(role, str):
                    code = 4545
                    message = 'Please select valid Role.'
                    raise Exception

                role = role.strip()

                companyQ = await self.branch.find_one(
                    {
                        'companyId': ObjectId(companyId)
                    },
                    limit=1
                )

                if not companyQ:
                    code = 4201
                    status = False
                    message = 'Company not found.'
                    raise Exception

                branchIdQ = await self.branch.find_one(
                    {
                        '_id': ObjectId(branchId)
                    },
                    limit=1
                )

                if not branchIdQ:
                    code = 4201
                    status = False
                    message = 'Branch not found.'
                    raise Exception

                personalInfo = {
                    'firstName': firstName,
                    'lastName': lastName,
                    'phone': phone,
                }

                userData = {
                    'companyId': companyId,
                    'branchId': branchId,
                    'email': email,
                    'password': password,
                    'role': ObjectId(role),
                    'personalInfo': personalInfo,
                    'active': True,
                    'createdAt': timeNow(),
                    'updatedAt': None,
                    'deletedAt': None,
                    'deleted': False
                }

            try:
                self.user.insert_one(userData)
                code = 2000
                status = True
                message = 'Employee created successfully'

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
