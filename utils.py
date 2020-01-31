import requests, time, sqlite3, itertools
from statistics import mean
from math import floor, ceil

def get_vacancies(vacancy_name):
    params = {
        'text': f'NAME:({vacancy_name})',
        'per_page': 100,
        'page': 0
    }
    response_json = requests.get('https://api.hh.ru/vacancies', params=params).json()
    vacancies = response_json['items']
    if response_json['pages']>1:
        for page in range(1, response_json['pages']+1):
            params['page'] = page
            response_json = requests.get('https://api.hh.ru/vacancies', params=params).json()
            items = response_json.get('items')
            if items:
                vacancies.extend(items)
    
    return vacancies

def get_areas(vacancies):
    return [
        {
            'id': area_kv[0],
            'name': area_kv[1]
        }
        for area_kv
        in {
            vacancy['area']['id']: vacancy['area']['name'] for vacancy in vacancies
        }.items()
    ]

def get_vacancies_count_by_areas(vacancies):
    vacancies_count_by_areas = []
    areas_kv = {vacancy['area']['id']: vacancy['area']['name'] for vacancy in vacancies}
    for area_id, area_name in sorted(areas_kv.items(), key=lambda kv: kv[1]):
        vacancies_count = len([vacancy for vacancy in vacancies if vacancy["area"]["id"]==area_id])
        vacancies_count_by_areas.append({
            'id': area_id,
            'name': area_name,
            'count': vacancies_count
        })

    return vacancies_count_by_areas

def get_area_vacancies(vacancies, chosen_area):
    area_vacancies = []
    if chosen_area:
        area_vacancies = [vacancy for vacancy in vacancies if vacancy['area']['name'].capitalize().startswith(chosen_area)]
        chosen_area = chosen_area
    
    return area_vacancies

def print_avalable_areas(vacancies_count_by_areas):
    for vacancy_count in sorted(vacancies_count_by_areas, key=lambda vacancy_count: vacancy_count['name']):
        print(f'{vacancy_count["name"]} ({vacancy_count["count"]} вакансий)')
    print()

def get_avalable_salaries(vacancies):
    salaries = [vacancy['salary'] for vacancy in vacancies if vacancy['salary']]

    return salaries

def get_mean_salaries_by_curr(salaries):
    currencies = {salary['currency'] for salary in salaries}
    mean_salaries_by_curr = []
    for currency in currencies:
        salaries_cur = [salary for salary in salaries if salary['currency']==currency]
        salary_amounts_cur = [salary['from'] if salary['from'] else salary['to'] for salary in salaries_cur]
        mean_salaries_by_curr.append({
            'currency': currency,
            'value': floor(mean(salary_amounts_cur)),
            'salaries_count': len(salary_amounts_cur)
        })
    
    return mean_salaries_by_curr

def print_mean_salaries(mean_salaries_by_curr):
    for item in mean_salaries_by_curr:
        print(f'Средняя ЗП в валюте {item["currency"]}: {item["value"]} {item["currency"]}. ({item["salaries_count"]} вакансий)')

def get_vacancies_detailed(vacancies, print_progress=False):
    vacancies_detailed = []
    for count, vacancy in enumerate(vacancies):
        vacancies_detailed.append(requests.get(vacancy['url']).json())
        if count>0 and not count%100 or count==len(vacancies):
            time.sleep(6)
            print('загружено', count, 'вакансий...') if print_progress else None

    return vacancies_detailed

def get_key_skills(vacancies_detailed):
    key_skills_dict = dict()
    for vacancy_detailed in vacancies_detailed:
        if len(vacancy_detailed['key_skills']):
            key_skill_names = [skill['name'] for skill in vacancy_detailed['key_skills']]
            for key_skill_name in key_skill_names:
                key_skills_dict.update({
                    key_skill_name: key_skills_dict.get(key_skill_name, 0)+1
                })
    skill_counts_sum = sum([int(key_skill_kv[1]) for key_skill_kv in key_skills_dict.items()])
    key_skills = []
    for skill, count in sorted(key_skills_dict.items(), key=lambda kv: kv[1], reverse=True):
        key_skills.append({
            'name': skill,
            'count': count,
            'persentage': ceil(100/(skill_counts_sum/count))
        })

    return key_skills

def get_json_report(vacancy_name, key_skills, vacancies_count_by_areas, area_vacancies, chosen_area=None, salaries=None, mean_salaries_by_curr=None):
    return {
        'vacancy_name': vacancy_name,
        'chosen_area': chosen_area if len(chosen_area) else None,
        'key_skills': key_skills,
        'mean_salaries_by_curr': mean_salaries_by_curr,
        'salaries_info': salaries,
        'vacancies_count_by_areas': vacancies_count_by_areas,
        'area_vacancies': area_vacancies,
    }

def scrape_region_names():
    regions_response = requests.get('https://api.hh.ru/areas').json()
    districts = itertools.chain.from_iterable([region['areas'] for region in regions_response])
    city_names = [
        city['name'] for city in
        itertools.chain.from_iterable([district['areas'] for district in districts])
    ]
    city_names = sorted(city_names)
    return city_names

def scrape_vacancies_info(input_vacancy, input_region):
    if input_vacancy:
        vacancies = get_vacancies(input_vacancy)
        if input_region:
            vacancies = get_area_vacancies(vacancies, input_region)
        salaries = get_avalable_salaries(vacancies if len(vacancies) else vacancies)
        mean_salaries_by_curr = get_mean_salaries_by_curr(salaries)
        key_skills = get_key_skills(
            get_vacancies_detailed(vacancies[:20] if len(vacancies)>20 else vacancies)
        )
        return {
            'count': len(vacancies),
            'mean_salaries_by_curr': mean_salaries_by_curr,
            'key_skills': key_skills[:15] if len(key_skills)>15 else key_skills
        }
    else:
        return None

def db_create_tables():
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        cursor.executescript("""
            CREATE TABLE regions (
                id   INTEGER       PRIMARY KEY
                                NOT NULL
                                UNIQUE,
                name VARCHAR (100) UNIQUE ON CONFLICT IGNORE
                                NOT NULL
            );

            CREATE TABLE vacancy_queries (
                id               INTEGER  PRIMARY KEY AUTOINCREMENT
                                        NOT NULL,
                vacancy_query    STRING   NOT NULL,
                query_region     INTEGER  REFERENCES regions (name),
                vacancies_count  INTEGER  NOT NULL,
                datetime_created DATETIME NOT NULL
                                        DEFAULT (CURRENT_TIMESTAMP) 
            );

            CREATE TABLE key_skills (
                id         INTEGER      PRIMARY KEY AUTOINCREMENT
                                        NOT NULL,
                vacancy_id INTEGER      REFERENCES vacancy_queries (id) 
                                        NOT NULL,
                name       VARCHAR (50) NOT NULL,
                count      INTEGER      NOT NULL,
                persentage INTEGER      NOT NULL
            );

            CREATE TABLE mean_salaries_by_curr (
                id             INTEGER     PRIMARY KEY AUTOINCREMENT
                                        NOT NULL
                                        UNIQUE,
                vacancy_id     INTEGER     REFERENCES vacancy_queries (id) 
                                        NOT NULL,
                currency       VARCHAR (3) NOT NULL,
                value          INTEGER     NOT NULL,
                salaries_count INTEGER     NOT NULL
            );

            CREATE TABLE contacts (
                id       INTEGER PRIMARY KEY AUTOINCREMENT
                                NOT NULL
                                UNIQUE,
                name     STRING  NOT NULL,
                city     STRING,
                email    STRING,
                vk       STRING,
                telegram STRING,
                img_src  STRING
            );
        """)

def db_save_vacancy_queries_cache(vacancy_query, query_region, vacancies_count, key_skills, mean_salaries_by_curr):
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        cursor.execute(
            'insert into vacancy_queries (vacancy_query, query_region, vacancies_count) values (?, ?, ?)',
            (vacancy_query, query_region, vacancies_count)
        )
        vacancy_id = cursor.lastrowid
        for key_skill in key_skills:
            cursor.execute(
                'insert into key_skills (vacancy_id, name, count, persentage) values (?, ?, ?, ?)',
                (vacancy_id, key_skill.get('name'), key_skill.get('count'), key_skill.get('persentage'))
            )
        for item in mean_salaries_by_curr:
            cursor.execute(
                'insert into mean_salaries_by_curr (vacancy_id, currency, value, salaries_count) values (?, ?, ?, ?)',
                (vacancy_id, item.get('currency'), item.get('value'), item.get('salaries_count'))
            )
        connection.commit()

def db_get_vacancy_queries_cache(vacancy_query, query_region=None):
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        if query_region is not None:
            vacancies_result = cursor.execute(
                'select id, vacancy_query, query_region, vacancies_count from vacancy_queries where vacancy_query is ? and query_region is ?',
                (vacancy_query, query_region)
            ).fetchone()
        else:
            vacancies_result = cursor.execute(
                'select id, vacancy_query, query_region, vacancies_count from vacancy_queries where vacancy_query is ? and query_region is null',
                (vacancy_query,)
            ).fetchone()
        if vacancies_result is not None:
            vacancy_id = vacancies_result[0]
            key_skills_result = cursor.execute(
                    'select name, count, persentage from key_skills where vacancy_id is ?',
                    (vacancy_id,)
                ).fetchall()
            mean_salaries_result = cursor.execute(
                    'select currency, value, salaries_count from mean_salaries_by_curr where vacancy_id is ?',
                    (vacancy_id, )
                ).fetchall()
            key_skills = [
                {'name': key_skill[0], 'count': key_skill[1], 'persentage': key_skill[2]} for key_skill in key_skills_result
            ]
            mean_salaries = [
                {'currency': mean_salary[0], 'value': mean_salary[1], 'salaries_count': mean_salary[2]} for mean_salary in mean_salaries_result
            ]
        else:
            return None
    
    return {
        'vacancy_query': vacancies_result[1],
        'query_region': vacancies_result[2],
        'count': vacancies_result[3],
        'key_skills': key_skills,
        'mean_salaries_by_curr': mean_salaries
    }

def db_delete_inactual_queries():
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        inactual_query_ids = cursor.execute(
            "select id from vacancy_queries where date(datetime_created) is not date('now')"
        ).fetchall()
        inactual_query_ids = [tupl[0] for tupl in inactual_query_ids]
        cursor.execute(
            "delete from vacancy_queries where date(datetime_created) is not date('now')"
        )
        for id in inactual_query_ids:
            cursor.execute(
                "delete from key_skills where vacancy_id is ?",
                (id,)
            )
            cursor.execute(
                "delete from mean_salaries_by_curr where vacancy_id is ?",
                (id,)
            )
        connection.commit()

def db_save_regions_cache(region_names):
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        for region_name in region_names:
            cursor.execute(
                'insert into regions (name) values (?)',
                (region_name,)
            )
        connection.commit()

def db_get_region_names_cache():
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        result = cursor.execute(
            'select name from regions'
        ).fetchall()
        if len(result):
            result = [tupl[0] for tupl in result]
        else:
            result = None

    return result

def db_get_contacts():
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        result = cursor.execute(
            'select name, city, email, vk, telegram, img_src from contacts'
        ).fetchall()
        if len(result):
            contacts = [
                {
                    'name': contact_tupl[0],
                    'city': contact_tupl[1],
                    'email': contact_tupl[2],
                    'vk': contact_tupl[3],
                    'telegram': contact_tupl[4],
                    'img_src': contact_tupl[5],
                } for contact_tupl in result
            ]
        else:
            contacts = None

    return contacts