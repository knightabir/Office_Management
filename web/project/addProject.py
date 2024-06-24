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


class AddProjectHandler(tornado.web.RequestHandler, MongoMixin):
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

    project = MongoMixin.userDb[
        CONFIG['database'][0]['table'][19]['name']
    ]
    user_role_map = MongoMixin.userDb[
        CONFIG['database'][0]['table'][22]['name']
    ]

    def options(self):
        status = False
        code = 4100
        message = ''
        result = []

    async def post(self):
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
                    code = 4211
                    message = 'Invalid - [ Authorization ]'
                    status = False
                    raise Exception

                # Decode the token
                payload = JWT_DECODE_1(token)
                if payload is None:
                    code = 4212
                    message = 'Invalid - [ Authorization ]'
                    status = False
                    raise Exception
            except Exception as e:
                Log.i(e)
                code = 4334
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            user_id = payload.get('userId')
            company_id = payload.get('companyId')
            role = payload.get('userRole')
            compName = 'project'
            ruleQ = self.user_role_map.aggregate(
                [
                    {
                        '$match': {
                            'user_Id': ObjectId(user_id)
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

            # Giving access which user
            if role != 'branchManager':
                code = 4563
                message = 'You are not authorized to access this resource.'
                status = False
                raise Exception
            else:
                try:
                    self.request.arguments = json.loads(self.request.body)
                except Exception as e:
                    code = 4743
                    message = 'Excepted Request Type JSON'
                    raise Exception

                # extract branch id from user_id
                userQ = self.user.find(
                    {
                        '_id': ObjectId(user_id)
                    },
                    limit=1
                )

                user = []
                async for i in userQ:
                    user.append(i)

                if not user:
                    message = 'User not found in database.'
                    code = 6587
                    status = False
                    raise Exception

                branch_id = user[0]['branchId']
                if not branch_id:
                    message = 'Branch not found.'
                    code = 6588
                    status = False
                    raise Exception

                projectName = self.request.arguments.get('projectName')
                if projectName is None or not projectName or isinstance(projectName, str):
                    code = 4136
                    message = 'Please give proper project Name'
                    raise Exception
                projectName = projectName.strip().title()

                description = self.request.arguments.get('description')
                if description is None or not description or not isinstance(description, str):
                    code = 4135
                    message = 'please give proper description.'
                description = description.strip()

                projectCode = self.request.arguments.get('projectCode')
                if projectCode is None or not projectCode or not isinstance(projectCode, str):
                    code = 4134
                    message = 'please give proper project code'


                projectType = self.request.arguments.get('projectType')
                if projectType is None or not projectType or not isinstance(projectType, str):
                    code = 4133
                    message = 'please give proper Project Type'
                    raise Exception

                projectCategory = self.request.arguments.get('projectCategory')
                if projectCategory is None or not projectCategory or not isinstance(projectCategory, str):
                    message = 'Please give proper Project Category'
                    code = 4132
                    raise Exception

                projectCategory = projectCategory.strip()

                endDate = self.request.arguments.get('endDate')
                if endDate is None or not endDate or not isinstance(endDate, str):
                    code = 4124
                    message = 'Please give proper end date'
                    raise Exception

                endDate = endDate.strip()

                assignee = []

                projectInfo = {
                    'projectName': projectName,
                    'description': description,
                    'projectCode': projectCode,
                    'isActive': True,
                    'createdBy': ObjectId(user_id),
                    'companyId': ObjectId(company_id),
                    'branchId': ObjectId(branch_id),
                    'createdOn': timeNow(),
                    'endDate': endDate,
                    'isDelivered': False,
                    'deleveredOn': None,
                    'deleted': False,
                    'projectType': projectType,
                    'projectCategory': projectCategory,
                    'assignee': assignee
                }

                try:
                    await self.project.insert_one(projectInfo)
                    code = 2000
                    status = True
                    message = 'Project created successfully.'

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
