from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import configparser


app = FastAPI(
    ssl_keyfile="/root/private.key",
    ssl_certfile="/root/cert.crt"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(HTTPSRedirectMiddleware)

config = configparser.ConfigParser()
config.read('ConfigFile.ini')


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
def read_root():
    educations = run_query('SELECT * FROM education ORDER BY id DESC')
    return {'educations': educations}


@app.get('/experiences')
def read_root():
    experiences = run_query('SELECT * FROM experience ORDER BY id DESC')

    for experience in experiences:
        projects = run_query(f'SELECT * FROM experience_project WHERE '
                             f'experience_project.experience = {experience["id"]} ORDER BY id')
        experience['projects'] = projects

    return {'experiences': experiences}


@app.get('/volunteering')
def read_root():
    volunteering = run_query('SELECT * FROM volunteering ORDER BY id DESC')
    return {'volunteering': volunteering}


@app.get('/projects')
def read_root():
    projects = run_query('SELECT * FROM project ORDER BY id DESC')
    return {'projects': projects}


@app.get('/courses')
def read_root():
    courses = run_query('SELECT * FROM course ORDER BY title')
    return {'courses': courses}


@app.get('/licenses')
def read_root():
    licenses = run_query('SELECT * FROM license ORDER BY id DESC')
    return {'licenses': licenses}
