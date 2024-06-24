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


class ProjectAssignHandler(tornado.web.RequestHandler, MongoMixin):
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

            # Giving access which user
            if role != 'branchManager':
                code = 4563
                message = 'You are not authorized to access this resource.'
                status = False
                raise Exception

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

            #  assign a project to a project manager
            projectManagerId = self.request.arguments.get('pmId')
            if projectManagerId is None or not projectManagerId  or not isinstance(projectManagerId, str):
                code = 4512
                message = 'Invalid - [ Project Manager ID ]'
                status = False
                raise Exception
            # code, message = Validate.i(
            #     projectManagerId,
            #     'projectManagerId',
            #     notEmpty=True,
            #     notNull=True,
            #     dataType=str
            # )
            #
            # if code != 4100:
            #     raise Exception

            projectId = self.request.arguments.get('projectId')
            if projectId is None or not projectId or not isinstance(projectId, str):
                code = 4513
                status = False
                raise Exception

            # code, message = Validate.i(
            #     projectId,
            #     'projectId',
            #     notEmpty=True,
            #     notNull=True,
            #     dataType=str
            # )
            #
            # if code != 4100:
            #     raise Exception

            # find the project from the database
            projectQ = self.project.find(
                {
                    '_id': ObjectId(projectId)
                },
                limit=1
            )

            project = []
            async for i in projectQ:
                project.append(i)

            if not project:
                message = 'Project not found in database.'
                code = 6589
                status = False
                raise Exception

            try:
                output = await self.project.update_one(
                    {
                        '_id': ObjectId(projectId)
                    },
                    {
                        '$set': {
                            'assignee': ObjectId(projectManagerId)
                        }
                    }
                )

                if output.modified_count == 0:
                    code = 4250
                    status = False
                    message = 'Internal server error. Please contact the support team.'
                    raise Exception

                code = 2000
                status = True
                message = 'Project assigned successfully.'

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

            print(role)

            if role != 'branchManager':
                message = 'You are not authorizes to use this resource'
                code = 4400
                status = False
                raise Exception

            # extract the branch id from the user_id

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

            # fetch all the project manager from the database for a particular branch
            try:
                print('***********************')
                print('Company Id : ', company_id)
                print('Branch Id : ', branch_id)

                projectManagerQ = self.user.aggregate(
                    [
                        {
                            '$match': {
                                'companyId': ObjectId(company_id),
                                'branchId': ObjectId(branch_id),
                                'role': ObjectId('66693920b44eb2133282d589')
                            }
                        }, {
                        '$project': {
                            '_id': {
                                '$toString': '$_id'
                            },
                            'personalInfo.firstName': 1,
                            'personalInfo.lastName': 1
                        }
                    }
                    ])

                projectManager = []
                async for i in projectManagerQ:
                    projectManager.append(i)

                if not projectManager:
                    message = 'No Project Manager found.'
                    code = 6589
                    status = False
                    raise Exception

                result = projectManager
                code = 2000
                status = True
                message = 'Project Manager found.'


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