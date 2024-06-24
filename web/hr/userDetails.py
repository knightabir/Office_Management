import json
import sys
from datetime import datetime, timedelta

import pytz
from lib.fernet_crypto import FN_ENCRYPT, FN_DECRYPT
import tornado.web
from bson import ObjectId
from build_config import CONFIG
from util.conn_util import MongoMixin
from util.log_util import Log
from util.time_util import offset, tStampToLocalTStamp, timeNow, TimeUtil
from bson.json_util import dumps as bdumps
from helper.jwt_helper import JWT_DECODE_1, JWT_ENCODE_1
from helper.decorators import all_origin

class ResignationUserHandler(tornado.web.RequestHandler, MongoMixin):

    SUPPORTED_METHODS = ('OPTIONS', 'PUT', 'POST','GET', 'DELETE')

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

    resignation = MongoMixin.userDb[
        CONFIG['database'][0]['table'][23]['name']
    ]

    def options(self):
        self.set_status(204)
        self.finish()

    async def get(self):
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
            compName = 'attendance'

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

            userQ = await self.user.find_one({'_id': ObjectId(userId)})
            companyId = userQ.get('companyId')

            detailsQ = self.user.aggregate(
                [
                    {
                        '$match': {
                            '_id': ObjectId(userId),
                            'companyId': ObjectId(companyId),
                            'branchId': ObjectId(userQ.get('branchId'))
                        }
                    }, {
                        '$lookup': {
                            'from': 'role',
                            'localField': 'role',
                            'foreignField': '_id',
                            'as': 'roleInfo'
                        }
                    }, {
                        '$lookup': {
                            'from': 'resignation',
                            'localField': '_id',
                            'foreignField': 'userId',
                            'as': 'resignationInfo'
                        }
                    }, {
                        '$lookup': {
                            'from': 'user_role_map',
                            'localField': '_id',
                            'foreignField': 'userId',
                            'as': 'role_id'
                        }
                    }, {
                        '$unwind': {
                            'path': '$roleInfo',
                            'preserveNullAndEmptyArrays': True
                        }
                    }, {
                        '$unwind': {
                            'path': '$resignationInfo',
                            'preserveNullAndEmptyArrays': True
                        }
                    }, {
                        '$unwind': {
                            'path': '$role_id',
                            'preserveNullAndEmptyArrays': True
                        }
                    }, {
                        '$unwind': {
                            'path': '$role_id.ruleId',
                            'preserveNullAndEmptyArrays': True
                        }
                    }, {
                        '$lookup': {
                            'from': 'rule',
                            'localField': 'role_id.ruleId.ruleId',
                            'foreignField': '_id',
                            'as': 'ruleDetails'
                        }
                    }, {
                        '$project': {
                            '_id': {
                                '$toString': '$_id'
                            },
                            'firstName': '$personalInfo.firstName',
                            'lastName': '$personalInfo.lastName',
                            'role': '$roleInfo.role',
                            'lastWorkingDate': '$resignationInfo.lastWorkingDate',
                            'Reason': '$resignationInfo.reason',
                            'ruleDetails': '$ruleDetails.name'
                        }
                    }
                ]
            )

            details = []
            async for i in detailsQ:
                details.append(i)

            # payment details
            paygradeQ = self.payGrade.aggregate(
                [
                    {
                        '$match': {
                            'user_Id': ObjectId(userId), 
                            'companyId': ObjectId(companyId), 
                            'branchId': ObjectId(userQ.get('branchId'))
                        }
                    }, {
                        '$unwind': '$payScale'
                    }, {
                        '$lookup': {
                            'from': 'payScale', 
                            'localField': 'payScale.payScaleId', 
                            'foreignField': '_id', 
                            'as': 'paySclaeDetails'
                        }
                    }, {
                        '$unwind': '$paySclaeDetails'
                    }, {
                        '$project': {
                            '_id': 0, 
                            'payScaleGrade': '$paySclaeDetails.payGrade', 
                            'baseSalary': '$paySclaeDetails.baseSalary', 
                            'performanceBonus': '$paySclaeDetails.performanceBonus', 
                            'annualBonus': '$paySclaeDetails.annualBonus', 
                            'isActive': '$payScale.isActive', 
                            'time': '$payScale.createdAt'
                        }
                    }
                ]
            )

            payment = []
            async for i in paygradeQ:
                i['time'] = datetime.fromtimestamp(i['time'] / 1e6).astimezone(pytz.utc)
                i['time'] = str(i['time'].date())
                payment.append(i)

            firstElement = payment[0]
            lastElement = payment[-1]

            paymentDetails = [
                {'initialSalary': firstElement},
                {'lastSalary': lastElement}
            ]

            result = {
                'details': details,
                'paymentDetails': paymentDetails,
                'totalSalary': payment
            }
            status = True
            code = 2000
            message = 'Success'

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
        # Log.d('RSP', response)
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
