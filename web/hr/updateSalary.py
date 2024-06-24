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

class UpdateSalaryHandler(tornado.web.RequestHandler, MongoMixin):
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


    async def put(self):
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
            compName = 'salary'


# Commented because we dont have enough data to test this function but it will work in the production time.
            # if role != 'HR':
            #     code = 4003
            #     message = 'Invalid - [ Authorization ]'
            #     status = False
            #     raise Exception

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

            if rule is None:
                code = 4003
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception
            
            elif compName not in rule:
                code = 4003
                message = 'You are not authorized to perform this action.'
                status = False
                raise Exception


            userQ = await self.user.find_one({'_id': ObjectId(userId)})
            branchId = userQ.get('branchId')


            #  Converts the body into json
            try:
                self.request.arguments = json.loads(self.request.body)

            except Exception as e:
                Log.i(e)
                code = 4002
                message = 'Expected Request Type JSON.'
                status = False
                raise Exception

            user_Id = self.request.arguments.get('user_Id')
            if not user_Id or not ObjectId.is_valid(user_Id):
                code = 4004
                message = 'Invalid - [ user_Id ]'
                status = False
                raise Exception
            
            payrollId = self.request.arguments.get('payrollId')
            if not payrollId or not ObjectId.is_valid(payrollId):
                code = 4005
                message = 'Invalid - [ payrollId ]'
                status = False
                raise Exception
            
            userQ = await self.user.find_one({'_id': ObjectId(user_Id)})
            if not userQ:
                code = 4007
                message = 'Invalid - [ user_id ]'
                status = False
                raise Exception
            
            if not userQ:
                code = 4007
                message = 'user not found in the system'
                status = False
                raise Exception
            

            try:
                # Deactivate the last active payScale element
                outcome = await self.payGrade.update_one(
                    {'user_Id': ObjectId(user_Id), 'payScale.isActive': True},
                    {'$set': {'payScale.$.isActive': False}}
                )

                if outcome.modified_count == 0:
                    code = 4008
                    message = 'payScale not found in the system'
                    status = False
                    raise Exception

                # Add the new payScale object
                data = {
                    'payScaleId': ObjectId(payrollId),
                    'isActive': True,
                    'createdAt': timeNow(),
                    'createdBy': ObjectId(userId),
                }

                outcode = await self.payGrade.update_one(
                    {'user_Id': ObjectId(user_Id)},
                    {'$push': {'payScale': data}}
                )

                if outcode.modified_count == 0:
                    code = 4008
                    message = 'payScale not found in the system'
                    status = False
                    raise Exception

                code = 200
                status = True
                message = 'PayScale Updated Successfully.'

            except Exception as e:
                status = False
                code = 4006
                message = 'Internal Error, Please Contact the Support Team.'
                Log.i(e)

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
