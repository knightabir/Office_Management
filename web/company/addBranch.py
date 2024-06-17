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


class AddBranchHandler(tornado.web.RequestHandler, MongoMixin):
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

                branchName = self.request.arguments.get('branchName')
                if branchName is None or not branchName or isinstance(branchName, str):
                    code = 4704
                    message = 'Please Enter valid Branch name.'
                branchName = branchName.strip()

                branchLocation = self.request.arguments.get('branchLocation')
                if branchLocation is None or not branchLocation or isinstance(branchLocation, str):
                    code = 4703
                    message = 'Please Enter valid Branch Location.'
                branchLocation = branchLocation.strip()

                branchAddress = self.request.arguments.get('branchAddress')
                if branchAddress is None or not branchAddress or isinstance(branchAddress, str):
                    code = 4702
                    message = 'Please enter valid Branch address'
                    raise Exception
                branchAddress = branchAddress.strip()

                branchContact = self.request.arguments.get('branchContact')
                if branchContact is None or not branchContact or isinstance(branchContact, str):
                    code = 4701
                    message = 'Please enter valid branch Contact.'
                    raise Exception
                branchContact = branchContact.strip()

                branchEmail = self.request.arguments.get('branchEmail')
                if branchEmail is None or not branchEmail or isinstance(branchEmail, str):
                    code = 4700
                    message = 'Please Enter valid branch Email.'
                    raise Exception
                branchEmail = branchEmail.strip()

                branchInfo = {
                    'companyId': ObjectId(company_id),
                    'branchName': branchName,
                    'branchLocation': branchLocation,
                    'branchAddress': branchAddress,
                    'branchContact': branchContact,
                    'branchEmail': branchEmail,
                    'createdAt': timeNow(),
                    'createdBy': ObjectId(user_id),
                    'updatedAt': None,
                    'active': True,
                    'deleted': False,
                }

                try:
                    self.branch.insert_one(branchInfo)
                    code = 2000
                    status = True
                    message = 'Branch created successfully'

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

