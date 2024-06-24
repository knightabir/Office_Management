import json
import sys
from datetime import datetime, timedelta

import tornado.web
from bson import ObjectId
from build_config import CONFIG
from lib.fernet_crypto import FN_ENCRYPT
from util.conn_util import MongoMixin
from util.log_util import Log
from util.time_util import timeNow
from bson.json_util import dumps as bdumps
from helper.jwt_helper import JWT_DECODE_1, JWT_ENCODE_1
from helper.decorators import all_origin


class AddBranchManagerHandler(tornado.web.RequestHandler, MongoMixin):
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

            user_id = payload.get('_id')
            company_id = payload.get('companyId')
            role = payload.get('userRole')

            if role != 'company':
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

                companyQ = await self.branch.find_one(
                    {
                        'companyId': ObjectId(company_id)
                    },
                    limit=1
                )

                if not companyQ:
                    code = 4201
                    status = False
                    message = 'Company not found.'
                    raise Exception

                firstname = self.request.arguments.get('firstName')
                if firstname is None or not firstname or isinstance(firstname, str):
                    code = 4863
                    message = 'please Enter valid First Name.'
                    raise Exception
                firstname = firstname.strip().title()

                lastName = self.request.arguments.get('lastName')
                if lastName is None or not lastName or isinstance(lastName, str):
                    code = 4862
                    message = 'Please Enter valid Last Name'
                lastName = lastName.strip().title()

                phone = self.request.arguments.get('phone')
                if phone is None or not phone or 10>len(phone)<10 or isinstance(phone, str):
                    code = 4862
                    message = 'Please Enter proper Phone Number.'
                    raise Exception

                address = self.request.arguments.get('address')
                if address is None or not address or isinstance(address , str):
                    code = 4861
                    message = 'Please Enter valid address.'
                    raise Exception

                address = address.strip()

                email = self.request.arguments.get('email')
                if email is None or not email or isinstance(email, str):
                    code = 4861
                    message = 'Please Enter Valid Email.'
                    raise Exception
                email = email.strip()

                emailQ = self.user.find(
                    {
                        "email": email
                    },
                    limit=1
                )

            emailD = []
            async for i in emailQ:
                emailD.append(i)

            if emailD:
                message = 'Email Already Exists.'
                status = False
                code = 4100
                raise Exception

            password = self.request.arguments.get('password')
            if password is None or not password or len(password) < 8 or isinstance(password,str):
                code = 4860
                message = 'Please Enter proper password.'
                raise Exception
            password = FN_ENCRYPT(password)

            branchId = self.request.arguments.get('branchId')
            if branchId is None or not branchId or isinstance(branchId, str):
                code = 4859
                message = 'Please select Proper Branch.'
                raise Exception

            role = self.request.arguments.get('role')
            if role is None or not role or isinstance(role, str):
                code = 4858
                message = 'Please Select proper Role.'
                raise Exception

            personalInfo = {
                'firstName': firstname,
                'lastName': lastName,
                'phone': phone,
                'address':address
            }

            branchManager = {
                'companyId': ObjectId(company_id),
                'branchId': ObjectId(branchId),
                'email': email,
                'password': password,
                'role': ObjectId(role),
                'PersonalInfo': personalInfo,
                'active': True,
                'createdAt': timeNow(),
                'createdBy': ObjectId(user_id),
                'updatedAt': None,
                'deletedAt': None,
                'deleted': False
            }

            try:
                self.user.insert_one(branchManager)
                code = 2000
                status = True
                message = 'Branch Manager created successfully'

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

