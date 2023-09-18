from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import configparser

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
    educations = run_query('SELECT * FROM education ORDER BY id DESC')
    return {'educations': educations}


@app.get('/experiences')
def get_experiences():
    experiences = run_query('SELECT * FROM experience ORDER BY id DESC')

    for experience in experiences:
        projects = run_query(f'SELECT * FROM experience_project WHERE '
                             f'experience_project.experience = {experience["id"]} ORDER BY id')
        experience['projects'] = projects

    return {'experiences': experiences}


@app.get('/volunteering')
def get_volunteering():
    volunteering = run_query('SELECT * FROM volunteering ORDER BY id DESC')
    return {'volunteering': volunteering}


@app.get('/projects')
def get_projects():
    projects = run_query('SELECT * FROM project ORDER BY id DESC')
    return {'projects': projects}


@app.get('/courses')
def get_courses():
    courses = run_query('SELECT * FROM course ORDER BY title')
    return {'courses': courses}


@app.get('/licenses')
def get_licenses():
    licenses = run_query('SELECT * FROM license ORDER BY id DESC')
    return {'licenses': licenses}


@app.get('/cv')
def get_cv():
    return FileResponse(path="Amir Mohammad's CV.pdf", filename="Amir Mohammad's CV.pdf", media_type='text/pdf')


@app.get('/resume')
def get_resume():
    return FileResponse(path="Amir Mohammad's Resume.pdf", filename="Amir Mohammad's Resume.pdf", media_type='text/pdf')
