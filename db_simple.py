import sqlite3

def create_tables():
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        with open('script_va_create_tables.txt') as file:
            text_script = file.read()
            cursor.executescript(text_script)

def add_vacancy_queries_cache(vacancy_query, query_region, vacancies_count, key_skills, mean_salaries_by_curr):
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

def get_vacancy_queries_cache(vacancy_query, query_region=None):
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

def delete_inactual_queries():
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

def add_regions(region_names):
    with sqlite3.connect('va_cache.sqlite') as connection:
        cursor = connection.cursor()
        for region_name in region_names:
            cursor.execute(
                'insert into regions (name) values (?)',
                (region_name,)
            )
        connection.commit()

def get_region_names():
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

def get_contacts():
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
