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


class OnBoardingHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('OPTIONS', 'POST', 'PUT')

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

    def options(self):
        self.set_status(204)
        self.finish()

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

            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            role = payload.get('userRole')

            # Hr and Manager can onboard
            if role not in ['HR-1', 'HR-2', 'HR-3', 'branchManager']:
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

                firstName = self.request.arguments.get('firstName')
                if not firstName or not isinstance(firstName, str):
                    code = 4856
                    message = 'Please Enter Valid First Name'
                    raise Exception
                firstName = firstName.title().strip()

                lastName = self.request.arguments.get('lastName')
                if not lastName or not isinstance(lastName, str):
                    code = 4857
                    message = 'Please Enter valid Last Name'
                    raise Exception
                lastName = lastName.title().strip()

                email = self.request.arguments.get('email')
                if not email or not isinstance(email, str):
                    code = 4855
                    message = 'Please enter valid email'
                    raise Exception
                email = email.lower().strip()

                # Find if the email already exists
                try:
                    userQ = self.obBoard.find(
                        {
                            'email': email
                        },
                        limit=1
                    )
                    user = []
                    async for i in userQ:
                        user.append(i)
                except Exception as e:
                    Log.i(e)
                    code = 4854
                    status = False
                    message = 'Internal Server Error'
                    raise Exception

                if user:
                    code = 4001
                    status = False
                    message = 'Email Already Exists'
                    raise Exception

                phone = self.request.arguments.get('phone')
                if not phone or not isinstance(phone, str) or len(phone) != 10:
                    code = 4138
                    message = 'Please enter valid phone'
                    raise Exception
                phone = phone.strip()

                address = self.request.arguments.get('address')
                if not address or not isinstance(address, str):
                    code = 4138
                    message = 'Please give proper address'
                    raise Exception
                address = address.strip().title()

                message = self.request.arguments.get('message')
                if not message or not isinstance(message, str):
                    code = 4137
                    message = 'Please give proper message.'
                    raise Exception
                message = message.strip()

                # Find branchId using userId
                try:
                    userQ = await self.user.find_one(
                        {
                            '_id': ObjectId(user_id)
                        }
                    )

                    branchId = userQ.get('branchId')
                    branchId = str(branchId)

                    if branchId:
                        pass
                    else:
                        code = 404
                        status = False
                        message = 'User not found'
                        raise Exception(message)

                except Exception as e:
                    Log.i(e)
                    code = 4584
                    status = False
                    message = 'Internal Server Error'
                    raise Exception(message)

                userInfo = {
                    'firstName': firstName,
                    'lastName': lastName,
                    'email': email,
                    'phone': phone,
                    'address': address,
                    'message': message,
                    'offerAccepted': False,
                    'companyId': ObjectId(company_id),
                    'branchId': ObjectId(branchId),
                    'createdAt': timeNow(),
                    'createdBy': ObjectId(user_id),
                    'updatedAt': None,
                    'active': True,
                    'deleted': False,
                }

                try:
                    self.obBoard.insert_one(userInfo)
                    code = 2000
                    status = True
                    message = 'OnBoarding Successful'

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

    async def put(self):
        status = False
        code = 4100
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
            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            role = payload.get('userRole')

            userQ = self.user.find(
                {
                    '_id': ObjectId(user_id)
                }
            )

            user = []
            async for i in userQ:
                user.append(i)

            if not user:
                code = 4001
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception
            branchId = user[0]['branchId']

            # Find and update offerAccepted false to true in onBoarding collection
            try:
                obBoard = await self.obBoard.update_one(
                    {   'companyId': ObjectId(company_id),
                        'branchId': ObjectId(branchId),
                        'offerAccepted': False
                    },
                    {
                        '$set': {
                            'offerAccepted': True
                        }
                    }
                )
                code = 2000
                status = True
                message = 'OnBoarding Successful'

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
