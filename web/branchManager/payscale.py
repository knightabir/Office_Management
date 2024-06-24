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


class PayScaleHandler(tornado.web.RequestHandler, MongoMixin):
    SUPPORTED_METHODS = ('OPTIONS', 'GET', 'POST')

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
    payScale = MongoMixin.userDb[
        CONFIG['database'][0]['table'][17]['name']
    ]

    def options(self):
        status = False
        code = 4100
        message = ''
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
                #  only role with company and Branch Manager can add role
            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            roleQ = payload.get('userRole')
            Log.i('ROLE :', roleQ)

            if roleQ != 'company' and roleQ != 'branchManager':
                code = 4001
                message = 'you are not authorized to to access this resource'
                status = False
                raise Exception

            try:

                self.request.arguments = json.loads(self.request.body)

            except Exception as e:
                code = 4100
                status = False
                message = 'Expected Request Type JSON.'
                raise Exception

            payGrade = self.request.arguments.get('payGrade')
            if payGrade is None or not payGrade or isinstance(payGrade, str):
                code = 4875
                message = 'Please Enter valid pay grade.'
                raise Exception
            payGrade = payGrade.strip()

            baseSalary = self.request.arguments.get('baseSalary')
            if baseSalary is None or not baseSalary or isinstance(baseSalary, str):
                code = 4876
                message = 'Please Enter valid Base Salary'
                raise Exception

            annualBonus = self.request.arguments.get('annualBonus')
            if annualBonus is None or not annualBonus or isinstance(annualBonus, str):
                code = 4877
                message = 'Please Enter valid Annual Bonus.'
                raise Exception

            performanceBonus = self.request.arguments.get('performanceBonus')
            if performanceBonus is None or not performanceBonus or isinstance(performanceBonus, str):
                code = 4878
                message = 'Please enter valid Performance Bonus.'
                raise Exception

            signingBonus = self.request.arguments.get('signingBonus')
            if signingBonus is None or not signingBonus or isinstance(signingBonus, str):
                code = 4879
                message = 'Please Enter valid SingIn Bonus.'
                raise Exception

            pay = {
                'payGrade': payGrade,
                'baseSalary': baseSalary,
                'annualBonus': annualBonus,
                'performanceBonus': performanceBonus,
                'signingBonus': signingBonus,
                'createdAt': timeNow(),
                'createdBy': ObjectId(user_id),
                'companyId': ObjectId(company_id),
                'updatedAt': None,
                'updatedBy': None,
                'isActive': True,
                'isDeleted': False,

            }
            try:
                # print(pay)
                self.payScale.insert_one(pay)
                code = 2000
                status = True
                message = 'Role created successfully'

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

    async def get(self):
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
                #  only role with company and Branch Manager can add role
            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            roleQ = payload.get('userRole')
            Log.i('ROLE :', roleQ)

            if roleQ != 'company' and roleQ != 'branchManager':
                code = 4001
                message = 'you are not authorized to to access this resource'
                status = False
                raise Exception

            payScaleQ = self.payScale.aggregate(
                [
                    {
                        '$match': {
                            'companyId': ObjectId('66681a63ed55f1052413d85c')
                        }
                    }, {
                    '$group': {
                        '_id': '$_id',
                        'payGrade': {
                            '$first': '$payGrade'
                        }
                    }
                }, {
                    '$project': {
                        '_id': {
                            '$toString': '$_id'
                        },
                        'payGrade': 1
                    }
                }
                ]
            )

            payScale = []
            async for i in payScaleQ:
                payScale.append(i)

            if not payScale:
                code = 4100
                status = False
                message = 'Payscale not found'
            else:
                code = 2000
                status = True
                message = 'Payscale fetched successfully'
                result = payScale

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