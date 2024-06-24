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


class CompanyCreateHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('OPTIONS', 'POST')

    user = MongoMixin.userDb[
        CONFIG['database'][0]['table'][12]['name']
    ]

    company = MongoMixin.userDb[
        CONFIG['database'][0]['table'][13]['name']
    ]

    def options(self):
        code = 4100
        message = ''
        status = False
        result = []

    async def post(self):
        code = 4000
        message = ''
        status = False
        result = []

        try:

            try:
                # converts the bosy into json
                self.request.arguments = json.loads(self.request.body)

            except Exception as e:
                code = 4100
                status = False
                message = 'Expected Request Type JSON.'
                raise Exception

            firstName = self.request.arguments.get('firstName')
            if firstName is None or not firstName or isinstance(firstName, str):
                code = 4100
                message = 'Invalid First Name.'
                status = False
                raise Exception
            firstName = firstName.title().strip()

            lastName = self.request.arguments.get('lastName')
            if lastName is None or not lastName or isinstance(lastName, str):
                code = 4100
                message = 'Invalid Last Name.'
                status = False
                raise Exception
            lastName = lastName.title().strip()

            email = self.request.arguments.get('email')
            if email is None or not email or len(email) >= 50 or not isinstance(email, str):
                code = 4100
                message = 'Invalid Email.'
                status = False
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
            if password is None or not password or 8 >= len(password) <= 50 or not isinstance(password, str):
                code = 4100
                message = 'Invalid Password.'
                status = False
                raise Exception

            password = FN_ENCRYPT(password)

            phone = self.request.arguments.get('phone')
            if phone is None or not phone or len(phone) != 10 or isinstance(phone, str):
                code = 4100
                message = 'Invalid Phone Number.'
                status = False
                raise Exception
            phone = phone.strip()

            companyName = self.request.arguments.get('companyName')
            if companyName is None or not companyName or isinstance(companyName, str):
                code = 4100
                message = 'Invalid Company Name.'
                status = False
                raise Exception

            companyName = companyName.title().strip()

            companyAddress = self.request.arguments.get('companyAddress')
            if companyAddress is None or not companyAddress or isinstance(companyAddress, str):
                code = 4100
                message = 'Invalid Company Address.'
                status = False
                raise Exception

            companyAddress = companyAddress.strip()

            companyPhone = self.request.arguments.get('companyPhone')
            if companyPhone is None or not companyPhone or len(companyPhone)!=10 or isinstance(companyPhone, str):
                code = 4100
                message = 'Invalid Company Phone Number.'
                status = False
                raise Exception

            companyData = {
                'companyName': companyName,
                'companyAddress': companyAddress,
                'companyPhone': companyPhone,
                'status': 'active',
                'createdOn': timeNow(),
                'updatedOn': None
            }

            try:
                companyId = await self.company.insert_one(companyData)
                companyId = companyId.inserted_id

            except Exception as e:
                code = 4100
                status = False
                message = 'Internal Error. Please Contact the Support Team.'
                raise Exception

            perosnalInfo = {
                'firstName': firstName,
                'lastName': lastName,
                'phone': phone
            }

            userData = {
                'companyId': companyId,
                'email': email,
                'password': password,
                'role': ObjectId('6668274e46b7840924b39246'),
                'personalInfo': perosnalInfo,
                'active': True,
                'createdAt': timeNow(),
                'updatedAt': None
            }

            try:
                registerUser = await self.user.insert_one(userData)
                registerUser = registerUser.inserted_id
                code = 200
                status = True
                message = 'Account created successfully.'
            except Exception as e:
                code = 4100
                status = False
                message = 'Internal Error. Please Contact the Support Team.'
                raise Exception
        except Exception as e:
            status = False
            self.set_status(503)
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
            'message': message
        }
        Log.d('RSP', response)

        response = {
            'code': code,
            'status': status,
            'message': message
        }
        Log.d('RSP', response)
        try:
            response['result'] = result
            Log.i(response)
            self.write(response)
            await self.finish()
            return
        except Exception as e:
            status = False
            template = 'Exception: {0}. Argument: {1!r}'
            code = 5011
            iMessage = template.format(type(e).__name__, e.args)
            message = 'Internal Error Please Contact the Support Team.'
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = exc_tb.tb_frame.f_code.co_filename
            Log.w('EXC', iMessage)
            Log.d('EX2', 'FILE: ' + str(fname) + ' LINE: ' + str(exc_tb.tb_lineno) + ' TYPE: ' + str(exc_type))
            response = {
                'code': code,
                'status': status,
                'message': message
            }
            self.write(response)
            await self.finish()
