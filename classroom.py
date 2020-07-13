#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from auth import auth
import os
import logging
from logging import handlers
from datetime import datetime, timedelta, date
from googleapiclient.errors import HttpError

#аутентификация
service = auth.get_service()

def logs_dir():
    """
    Создание директории с логами.
    """
    path = os.getcwd()
    n_dir = "/logs"
    try:
        os.mkdir(path+n_dir)
    except OSError:
        pass


def logger_init():
    """
    Инициализация логгинга.
    """
    logs_dir()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s:%(message)s')
    file_handler = logging.handlers.RotatingFileHandler('logs/log.log', mode='a', maxBytes=1*1024*1024, 
                                 backupCount=50, encoding=None, delay=0)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

#инициализация логгинга
logger = logger_init()

def get_course(courseId):
    """
    Принимает: id курса
    Возвращает: объект курса с заданным id
    """
    return service.courses().get(id=courseId).execute()

def get_courses(studentId = None):
    """
    Принимает: -
    Вовзращает: список курсов, к которым есть доступ с используемым токеном
                пользователя
    """
    if studentId==None:
        courses = service.courses().list().execute().get('courses', [])
        if courses == []:
            logger.log(logging.INFO, 'нет курсов')
        else:
            logger.log(logging.INFO, 'загружено {} курсов'.format(len(courses)))
    else:
        courses = service.courses().list(studentId=studentId).execute().get('courses', [])


    return courses

def find_course(courseId, courses):
    """
    Принимает: id курса, список курсов
    Возвращает: объект искомого курса
    """
    for course in courses:
        if course['id'] == courseId:
            return course.copy()

def get_announcements(course):
    """
    Принимает: объект курса
    Возвращает: список объявлений курса
    """
    announcements = []
    flag = False
    token = ''
    while not flag:
        result = service.courses().announcements().list(courseId=course['id'], pageToken=token).execute()
        announcement = result.get('announcements', [])
        [announcements.append(i) for i in announcement]
        token = result.get('nextPageToken', [])
        if not token:
            flag = True
    logger.info('загружено {} объявлений с курса {} ({})'.format(len(announcements), course['name'], course['id']))
    return announcements

def get_topics(course):
    """
    Принимает: объект курса
    Возвращает: список тем курса
    """
    topics = []
    flag = False
    token = ''
    while not flag:
        result = service.courses().topics().list(courseId=course['id'], pageToken=token).execute()
        topic = result.get('topic', [])
        [topics.append(i) for i in topic]
        token = result.get('nextPageToken', [])
        if not token:
            flag = True
    logger.info('загружено {} тем с курса {} ({})'.format(len(topics), course['name'], course['id']))
    return topics


def get_teachers(course):
    """
    Принимает: объект курса
    Вовзращает: список преподавателей курса
    """
    teachers = []
    flag = False
    token = ''
    while not flag:
        result = service.courses().teachers().list(courseId=course['id'], pageToken=token).execute()
        teacher = result.get('teachers', [])
        [teachers.append(i['profile']) for i in teacher]
        token = result.get('nextPageToken', [])
        if not token:
            flag = True
    for teacher in teachers:
        for i in ['permissions', 'verifiedTeacher']:
            if i in teacher.keys():
                teacher.pop(i)
    return teachers



def get_students(course, count = 0):
    """
    Принимает: один курс
    Вовзращает: список студентов курса.
    """
    students = []
    flag = False
    token = ''
    while not flag:
        result = service.courses().students().list(courseId=course['id'], pageToken=token).execute()
        student = result.get('students', [])
        [students.append(i['profile']) for i in student]
        token = result.get('nextPageToken', [])
        if not token:
            flag = True

    #удаляем ненужные ключи, добавляем требуемые
    for student in students:
        if 'givenName' in student['name'].keys():
                student['firstName'] = student['name']['givenName']
        else:
                student['firstName'] = '-'

        if 'familyName' in student['name'].keys():
                student['lastName'] = student['name']['familyName']
        else:
                student['lastName'] = '-'
        for i in ['permissions', 'verifiedTeacher', 'photoUrl', 'name']:
            if i in student.keys():
                    student.pop(i)

    return students


def find_student(userId, students):
    """
    Принимает: id студента, список студентов
    Возвращает: объект искомого студента
    """
    for i in students:
        if i['id']==userId:
            return i.copy()
    return None


def get_courseWork(course, count = 0):
    """
    Принимает: объект курса, опционно - счетчик курсов для логгинга
    Вовзращает: список заданий курса
    """
    courseWork = []
    flag = False
    token = ''
    while not flag:
        result = service.courses().courseWork().list(courseId=course['id'], pageToken=token).execute()
        work = result.get('courseWork', [])
        [courseWork.append(i) for i in work]
        token = result.get('nextPageToken', [])
        if not token:
            flag = True

#    for work in courseWork:
#        work['creationTime'] = to_timestamp(work['creationTime'])
#        work['updateTime'] = to_timestamp(work['updateTime'])

    return courseWork


def find_Submission(userId, courseWork):
    """
    Принимает: id студента, объект задания
    Возвращает: объект работы студента
    """
    for i in courseWork['studentSubmissions']:
        if i['userId'] == userId:
            return i.copy()
    return None



def get_submissions(course, courseWork):
    """
    Принимает: объект курса и объект задания
    Вовзращает: список работ студентов (studentSubmissions) по этому заданию.
    """
    studentSubmissions = []
    flag = False
    token = ''
    while not flag:
        result = service.courses().courseWork().studentSubmissions().list(
                courseId=course['id'],
                courseWorkId=courseWork['id'],
                pageToken=token).execute()
        subm = result.get('studentSubmissions', [])
        [studentSubmissions.append(i) for i in subm]
        token = result.get('nextPageToken', [])
        if not token:
            flag = True

    if studentSubmissions == []:
        logger.log(logging.WARNING, 'на курсе {} нет студентов'.format(course['id']))

    change_submsissions_date_format(studentSubmissions)

    #for item in studentSubmissions:
    #    if 'updateTime' in item.keys():
    #        item['updateTime'] = to_timestamp(item['updateTime'])

    return studentSubmissions

def checkKeys(data, keys):
    """
    Принимает: исходную информацию (list of dict); список полей, которые
               должны присутствоовать в структуре, и их значений по умолчанию (dict).
    Возвращает: исходные данные, но только с требуемыми полями.

    *Добавляет недостающие и удаляет лишние поля
    """
    data = checkMissingKeys(data, keys)

    for item in data:
        for key in item.keys():
            if key not in keys.keys():
                item.pop(key)

    return data


def checkMissingKeys(data, missingValues):
    """
    Принимает: исходную информацию (list of dict или dict); список полей, которые
               должны присутствоовать в структуре, и их значений по умолчанию (dict).
    Возвращает: исходные данные, но с новыми полями.

    *Добавляет недостающие поля
    """
    if type(data) == list:
        for key in missingValues.keys():
            for item in data:
                if key not in item.keys():
                    item[key] = missingValues[key]
    else:
        for key in missingValues.keys():
            if key not in data.keys():
                data[key] = missingValues[key]
    return data


def state_or_grade(element):
    """
    Принимает: один элемент из истории изменений работы (submissionHistory).
    Возвращает: строку state или grade, в зависимости от того, к какому типу
                относится элемент.
    """
    if 'stateHistory' in element.keys():
        return 'state'
    else:
        return 'grade'



def select_data_by_date(studentSubmissions, d_from=-1, d_to=1):
    """
    Принимает: список работ и временной период
               (даты в формате datetime.date).
    Возвращает: список работ, который были изменены в этот период.

    1) Можно задать не обе даты, а только одну или ни одной.
    2) В возвращаемом списке работ, в графах submissionHistory содержится не
       вся история изменений, а лишь те события, которые произошли в указанный
       период.
    """

    if d_from==-1 and d_to==1:
        logger.log(logging.INFO, 'вся история')
        return studentSubmissions

    if type(d_from)!=date and d_from not in [-1,1]:
        logger.log(logging.WARNING, 'дата "от" должна быть в формате datetime.date или "-1" или "1"')
        return []

    if type(d_to)!=date and d_to!=1:
        logger.log(logging.WARNING, 'дата "до" должна быть в формате datetime.date или "1"')
        return []

    if d_from!=-1 and d_to!=1 and d_from > d_to:
        logger.log(logging.WARNING, 'дата "от" должна быть меньше даты "до"')
        return []

    #проверка на вхождения работ в заданный диапазон дат
    new_data = []
    for work in studentSubmissions:
        buf = []
        if work['state']!='NEW':
            for item in work['submissionHistory']:
                el_type = state_or_grade(item)
                curr = item[el_type+'History']
                flag = False
                if d_from != -1:
                    if (curr['timestamp'].date() - d_from).days > -1:
                        buf.append({state_or_grade(item)+'History': curr})
                        flag = True

                if d_to != 1:
                    if (d_to - curr['timestamp'].date()).days > -1:
                        if not flag:
                            buf.append({state_or_grade(item)+'History': curr})
                            flag = True
                    else:
                        if flag:
#                            logger.log(logging.INFO, 'удалили {} тк {} > ({})'.format(work['id'], curr['timestamp'], d_to))
                            buf.pop(-1)

                if d_from != -1:
                    if flag == True:
                        if (curr['timestamp'].date() - d_from).days <= -1:
                            buf.pop(-1)

            if buf != []:
                new_data.append(work.copy())
                new_data[-1]['submissionHistory'] = buf

    return new_data

def to_timestamp(timestamp):
    """
    Принимает: timestamp в формате 2014-10-02T15:01:23.045123456Z
    Возвращает: отметку времени в формате datetime.
    """

    #избавляется от лишней части отметки времени
    def helper(time):
        new_time = time
        if ('.') in time:
            new_time = time.split('.', 1)[0]
        else:
            new_time = time.split('Z', 1)[0]
        if new_time == time:
            logger.log(logging.ERROR, 'что-то пошло не так при парсинге отметки времени')
        return new_time

    timestamp = helper(timestamp)
    timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
    return timestamp


def change_submsissions_date_format(studentsSubmissions):
    """
    Принимает: список работ студента (studentsSubmissions).
    Возвращает: -

    *Парсит в каждой работе формат отметки времени в словарь.
    """
    for item in studentsSubmissions:
        if 'submissionHistory' in item.keys():
            for element in item['submissionHistory']:
                el_type = state_or_grade(element)
                element[el_type+'History']['timestamp'] = to_timestamp(element[el_type+'History'].pop(el_type+'Timestamp'))
