import configparser
from contextlib import asynccontextmanager

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import FileResponse

config = configparser.ConfigParser()
config.read('ConfigFile.ini')

pool = None


def db_kwargs():
    return {
        'database': config.get('DatabaseSection', 'database'),
        'user': config.get('DatabaseSection', 'user'),
        'password': config.get('DatabaseSection', 'password'),
        'host': config.get('DatabaseSection', 'host'),
        'port': config.get('DatabaseSection', 'port'),
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = ThreadedConnectionPool(1, 10, **db_kwargs())
    try:
        yield
    finally:
        pool.closeall()


app = FastAPI(
    lifespan=lifespan,
    ssl_certfile=config.get('CertificateSection', 'certificate_path'),
    ssl_keyfile=config.get('CertificateSection', 'private_key_path'),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.add_middleware(HTTPSRedirectMiddleware)


def run_query(query, params=None):
    conn = pool.getconn()
    try:
        conn.autocommit = True
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn, close=bool(conn.closed))


@app.get('/educations')
def get_educations():
    educations = run_query('SELECT * FROM education ORDER BY id DESC;')
    return {'educations': educations}


@app.get('/industry-experience')
def get_industry_experience():
    industry_experience = run_query('SELECT * FROM industry_experience ORDER BY id DESC;')

    for current_industry_experience in industry_experience:
        medias = run_query(f'SELECT * FROM industry_experience_media WHERE '
                           f'industry_experience_media.experience = {current_industry_experience["id"]} ORDER BY id;')
        current_industry_experience['medias'] = medias

    return {'industry_experience': industry_experience}


@app.get('/research-experience')
def get_research_experience():
    research_experience = run_query('SELECT * FROM research_experience ORDER BY id DESC;')
    return {'research_experience': research_experience}


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
    return FileResponse(path="Resume.pdf", filename="Resume.pdf", media_type='text/pdf')


@app.get('/cv')
def get_cv():
    return FileResponse(path="CV.pdf", filename="CV.pdf", media_type='text/pdf')


@app.get('/photos/{photo_name}')
def get_photo(photo_name: str):
    return FileResponse(path=f'photos/{photo_name}', filename=f'photos/{photo_name}', media_type='image/jpeg')
