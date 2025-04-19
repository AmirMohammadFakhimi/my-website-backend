import configparser

import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import FileResponse
from psycopg2.extras import RealDictCursor

config = configparser.ConfigParser()
config.read('ConfigFile.ini')

app = FastAPI(
    ssl_certfile=config.get('CertificateSection', 'certificate_path'),
    ssl_keyfile=config.get('CertificateSection', 'private_key_path')
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(HTTPSRedirectMiddleware)


def get_database_config(option):
    global config
    return config.get('DatabaseSection', option)


connection = psycopg2.connect(database=get_database_config('database'),
                              user=get_database_config('user'),
                              password=get_database_config('password'),
                              host=get_database_config('host'),
                              port=get_database_config('port'))


def run_query(query):
    global connection

    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()

    return result


@app.get('/educations')
def get_educations():
    educations = run_query('SELECT * FROM education ORDER BY id DESC;')
    return {'educations': educations}


@app.get('/work-experiences')
def get_experiences():
    work_experiences = run_query('SELECT * FROM work_experience ORDER BY id DESC;')

    for work_experience in work_experiences:
        medias = run_query(f'SELECT * FROM work_experience_media WHERE '
                           f'work_experience_media.experience = {work_experience["id"]} ORDER BY id;')
        work_experience['medias'] = medias

    return {'experiences': work_experiences}


@app.get('/research-experiences')
def get_educations():
    research_experiences = run_query('SELECT * FROM research_experience ORDER BY id DESC;')
    return {'laboratories': research_experiences}


@app.get('/volunteering')
def get_volunteering():
    volunteering = run_query('SELECT * FROM volunteering ORDER BY id DESC;')

    for volunteer in volunteering:
        volunteer['labels'] = volunteer['labels'].strip('{}').replace('"', '').split(',')

    for volunteer in volunteering:
        medias = run_query(f'SELECT * FROM volunteering_media WHERE '
                           f'volunteering_media.volunteering = {volunteer["id"]} ORDER BY id;')
        volunteer['medias'] = medias

    return {'volunteering': volunteering}


@app.get('/projects')
def get_projects():
    projects = run_query('SELECT * FROM project ORDER BY id DESC;')
    for project in projects:
        project['labels'] = project['labels'].strip('{}').replace('"', '').split(',')

    return {'projects': projects}


@app.get('/courses')
def get_courses():
    courses = run_query('SELECT * FROM course ORDER BY id DESC;')
    return {'courses': courses}


@app.get('/honors-and-certificates')
def get_honors_and_certificates():
    honors_and_certificates = run_query('SELECT * FROM honor_and_certificate ORDER BY id DESC;')
    return {'honors_and_certificates': honors_and_certificates}


@app.get('/resume')
def get_resume():
    return FileResponse(path="Amir Mohammad Fakhimi's Resume.pdf", filename="Amir Mohammad Fakhimi's Resume.pdf",
                        media_type='text/pdf')


@app.get('/photos/{photo_name}')
def get_photo(photo_name: str):
    return FileResponse(path=f'photos/{photo_name}', filename=f'photos/{photo_name}', media_type='image/jpeg')
