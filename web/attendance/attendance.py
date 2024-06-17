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


class AttendanceHandler(tornado.web.RequestHandler, MongoMixin):
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

    attendance = MongoMixin.userDb[
        CONFIG['database'][0]['table'][18]['name']
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

            user_id = payload.get('userId')
            # find branch_id using user_id

            userQ = self.user.find({'_id': ObjectId(user_id)})

            user = []
            async for i in userQ:
                user.append(i)
            if user is None:
                code = 4001
                message = 'Invalid - [ Authorization ]'
                status = False
                raise Exception

            try:
                # decode json
                self.request.arguments = json.loads(self.request.body)

            except Exception as e:
                code = 4100
                status = False
                message = 'Expected Request Type JSON.'
                raise Exception

            input = self.request.arguments.get('input')
            if input is None or not input or not isinstance(input, int):
                code = 4512
                message = 'Please Enter valid Input'
                status = False
                raise Exception

            if input == 0:
                branch_id = user[0].get('branchId')
                company_id = payload.get('companyId')
                roleQ = payload.get('userRole')
                Log.i('ROLE :', roleQ)

                if roleQ == 'company':
                    code = 4001
                    message = 'you are not authorized to to access this resource'
                    status = False
                    raise Exception
                # CUrrent date
                date = datetime.now().date()
                date_str = str(date)
                time_now = datetime.now().time()

                # Define the check-in and check-out times
                check_in_time = datetime.strptime("10:00AM", "%I:%M%p").time()
                check_out_time = datetime.strptime("07:00PM", "%I:%M%p").time()

                # Determine if the user is late
                is_late = time_now > check_in_time

                attendance = {
                    'user_id': ObjectId(user_id),
                    'company_id': ObjectId(company_id),
                    'branch_id': ObjectId(branch_id),
                    'date': date_str,
                    'in_time': time_now.strftime("%I:%M %p"),
                    'out_time': None,
                    'is_late': is_late,
                    'is_absent': False,
                    'is_half_day': False,
                    'leave': False,
                    'working_hours': None
                }

                try:
                    self.attendance.insert_one(attendance)
                    code = 2000
                    status = True
                    message = 'Checked in successfully'

                except Exception as e:
                    code = 4100
                    status = False
                    message = 'Internal Server Error'

            elif input == 1:
                branch_id = user[0].get('branchId')
                company_id = payload.get('companyId')
                roleQ = payload.get('userRole')
                Log.i('ROLE :', roleQ)

                if roleQ == 'company':
                    code = 4001
                    message = 'you are not authorized to to access this resource'
                    status = False
                    raise Exception

                # CUrrent date
                date = datetime.now().date()
                date_str = str(date)
                time_now = datetime.now().time()

                # Define the check-in and check-out times
                check_in_time = datetime.strptime("10:00AM", "%I:%M%p").time()
                check_out_time = datetime.strptime("07:00PM", "%I:%M%p").time()

                print(user_id)
                print(date_str)

                # Fetch the attendance record for the day
                attendanceQ = self.attendance.find({'user_id': ObjectId(user_id), 'date': date_str})

                attendanceD = []
                async for i in attendanceQ:
                    attendanceD.append(i)

                if not attendanceD:
                    code = 4100
                    status = False
                    message = 'You are not checked in'
                    raise Exception

                attendance_record = attendanceD[0]  # Since we're only fetching one record

                if attendance_record.get('out_time'):
                    code = 4100
                    status = False
                    message = 'You are already checked out'
                    raise Exception

                working_hours = datetime.combine(date, time_now) - datetime.combine(date, datetime.strptime(
                    attendance_record['in_time'], "%I:%M %p").time())

                result = await self.attendance.update_many(
                    {'user_id': ObjectId(user_id), 'date': date_str},
                    {'$set': {'out_time': time_now.strftime("%I:%M %p"), 'working_hours': str(working_hours)}}
                )

                if result.modified_count == 0:
                    code = 4250
                    status = False
                    message = 'Internal Server Error'
                    raise Exception

                code = 2000
                status = True
                message = 'Checked out successfully'
                result = []  # Ensure result is an empty list to avoid serialization issues

                # Check for any missing attendance and mark as absent if necessary
                yesterday = datetime.now() - timedelta(days=1)
                yesterday_str = str(yesterday.date())

                missed_attendance = await self.attendance.find(
                    {'user_id': ObjectId(user_id), 'date': yesterday_str}).to_list(length=1)
                if not missed_attendance:
                    self.attendance.insert_one({
                        'user_id': ObjectId(user_id),
                        'company_id': ObjectId(company_id),
                        'branch_id': ObjectId(branch_id),
                        'date': yesterday_str,
                        'in_time': None,
                        'out_time': None,
                        'is_late': None,
                        'is_absent': True,
                        'is_half_day': False,
                        'leave': False,
                        'working_hours': None
                    })

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
