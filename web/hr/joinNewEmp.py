import json
import sys
from datetime import datetime, timedelta
from lib.fernet_crypto import FN_ENCRYPT, FN_DECRYPT
import tornado.web
from bson import ObjectId
from build_config import CONFIG
from util.conn_util import MongoMixin
from util.log_util import Log
from util.time_util import timeNow
from bson.json_util import dumps as bdumps
from helper.jwt_helper import JWT_DECODE_1, JWT_ENCODE_1
from helper.decorators import all_origin


class JoinNewEmpHandler(tornado.web.RequestHandler, MongoMixin):

    SUPPORTED_METHODS = ('OPTIONS', 'PUT', 'POST')


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

    user_role_map = MongoMixin.userDb[
        CONFIG['database'][0]['table'][22]['name']
    ]

    payGrade = MongoMixin.userDb[
        CONFIG['database'][0]['table'][20]['name']
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
            except:
                code = 4001
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            payload = JWT_DECODE_1(token)

            if payload is None:
                code = 4002
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            # get the user_id company_id and role from the token
            userId = payload.get('userId')
            companyId = payload.get('companyId')
            role = payload.get('userRole')
            compName = 'joiningModule'

            
            if role not in ['HR', 'branchManager']:
                code = 4003
                message = 'You are not authorized to perform this action.'
                status = False
                raise Exception('Expectation Error: Unauthorized Role') 
            
            ruleQ = self.user_role_map.aggregate(
                [
                    {
                        '$match': {
                            'user_Id': ObjectId(userId)
                        }
                    }, {
                        '$lookup': {
                            'from': 'rule', 
                            'localField': 'ruleId.ruleId', 
                            'foreignField': '_id', 
                            'as': 'result'
                        }
                    }, {
                        '$unwind': {
                            'path': '$result', 
                            'preserveNullAndEmptyArrays': True
                        }
                    }, {
                        '$project': {
                            '_id': 0, 
                            'result.name': 1
                        }
                    }
                ]
            )

            if ruleQ is None:
                code = 4003
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            rule = []
            async for i in ruleQ:
                rule.append(i['result']['name'])

            if role is None:
                code = 4005
                message = 'you are not authorized user'
                status = False
                raise Exception
            elif compName not in rule:
                code = 4004
                message = 'you are not authorized user'
                status = False
                raise Exception            
            
            try: 
                # Converts the body into json
                self.request.arguments = json.loads(self.request.body)
            except Exception as e:
                code = 4004
                message = 'exprected request type JSON.'
                status = False
                raise Exception

            userQ = await self.user.find_one({'_id': ObjectId(userId)})
            branchId = userQ.get('branchId')


            if not branchId:
                code = 4004
                message = 'You are not authorized to perform this action.'
                status = False
                raise Exception
            
            firstName = self.request.arguments.get('firstName')
            if firstName is None or not firstName or not isinstance(firstName, int):
                code = 4005
                message = 'Invalid - [ firstName ]'
                status = False
                raise Exception
            lastName = self.request.arguments.get('lastName')
            if lastName is None or not lastName or not isinstance(lastName, int):
                code = 4006
                message = 'Invalid - [ lastName ]'
                status = False
                raise Exception
            email = self.request.arguments.get('email')
            if email is None or not email or not isinstance(email, int):
                code = 4007
                message = 'Invalid - [ email ]'
                status = False
                raise Exception
            phoneNumber = self.request.arguments.get('phoneNumber')
            if phoneNumber is None or not phoneNumber or not isinstance(phoneNumber, int) or len(phoneNumber) != 10:
                code = 4008
                message = 'Invalid - [ phoneNumber ]'
                status = False
                raise Exception
            password = self.request.arguments.get('password')
            if password is None or not password or not isinstance(password, int):
                code = 4009
                message = 'Invalid - [ password ]'
                status = False
                raise Exception
            
            password = FN_ENCRYPT(password)

            role = self.request.arguments.get('role')
            if role is None or not role or not isinstance(role, str):
                code = 4010
                message = 'Invalid - [ role ]'
                status = False
                raise Exception
            address = self.request.arguments.get('address')
            if address is None or not address or not isinstance(address, str):
                code = 4011
                message = 'Invalid - [ address ]'
                status = False
                raise Exception
            

            perosnalInfo = {
                'firstName': firstName,
                'lastName': lastName,
                'phoneNumber': phoneNumber,
                'address': address
            }


            data = {
                'companyId': companyId,
                'branchId': branchId,
                'email': email,
                'password': password,
                'role': ObjectId(role),
                'perosnalInfo': perosnalInfo,
                'active': True,
                'createdBy': ObjectId(userId),
                'createdOn': timeNow(),
                'updatedOn': None,
                'updatedBy': None,
                'deleted': False,
                'deletedOn': None,
            }

            try:
                await self.user.insert_one(data)
                status = True
                code = 2000
                message = 'User Created Successfully.'

            except Exception as e:
                Log.i(e)
                status = False
                code = 5000
                message = 'Internal Error, Please Contact the Support Team.'


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