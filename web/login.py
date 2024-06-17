import json
import sys
import tornado.web
from bson import ObjectId
from build_config import CONFIG
from util.conn_util import MongoMixin
from util.log_util import Log
from util.time_util import timeNow
from bson.json_util import dumps as bdumps
from helper.jwt_helper import JWT_DECODE_1, JWT_ENCODE_1
from lib.fernet_crypto import FN_DECRYPT, FN_ENCRYPT


class LoginHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('POST', 'OPTIONS')

    user = MongoMixin.userDb[
        CONFIG['database'][0]['table'][12]['name']
    ]

    company = MongoMixin.userDb[
        CONFIG['database'][0]['table'][13]['name']
    ]
    role = MongoMixin.userDb[
        CONFIG['database'][0]['table'][15]['name']
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
                # converts the body into json
                self.request.arguments = json.loads(self.request.body)

            except Exception as e:
                code = 4100
                status = False
                message = 'Expected Request Type JSON.'
                raise Exception

            email = self.request.arguments.get('email')
            if email is None or not email or len(email) >= 50 or not isinstance(email, str):
                message = 'Email is not valid.'
                code = 4512
                raise Exception

            password = self.request.arguments.get('password')
            if password is None or not password or not isinstance(password, str):
                message = 'Please enter valid password.'
                raise Exception

            password = FN_ENCRYPT(password)
            password = FN_DECRYPT(password)

            userQ = await self.user.find_one(
                {
                    'email': email
                },
                limit=1
            )

            if not userQ:
                message = 'This email not registered.'
                code = 4201
                status = False
                raise Exception

            DBpassword = userQ['password']
            DBpassword = FN_DECRYPT(DBpassword)
            userId = str(userQ['_id'])
            userRole = str(userQ['role'])
            companyId = str(userQ['companyId'])

            role = await self.role.find_one({'_id': ObjectId(userRole)})
            role = role.get('role')

            payload = {
                'userId': userId,
                'companyId': companyId,
                'userRole': role
            }

            if password != DBpassword:
                message = 'Invalid Password.'
                code = 4202
                status = False
                raise Exception

            if password == DBpassword:
                token = JWT_ENCODE_1(payload)
                status = True
                code = 200
                message = 'Login Successful.'
                result = {
                    'token': token
                }

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
