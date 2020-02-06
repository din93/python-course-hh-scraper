import requests, time, itertools
from statistics import mean
from math import floor, ceil

def scrape_vacancies(vacancy_name):
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

def scrape_vacancies_detailed(vacancies, print_progress=False):
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
        vacancies = scrape_vacancies(input_vacancy)
        if input_region:
            vacancies = get_area_vacancies(vacancies, input_region)
        salaries = get_avalable_salaries(vacancies if len(vacancies) else vacancies)
        mean_salaries_by_curr = get_mean_salaries_by_curr(salaries)
        key_skills = get_key_skills(
            scrape_vacancies_detailed(vacancies[:20] if len(vacancies)>20 else vacancies)
        )
        return {
            'count': len(vacancies),
            'mean_salaries_by_curr': mean_salaries_by_curr,
            'key_skills': key_skills[:15] if len(key_skills)>15 else key_skills
        }
    else:
        return None
