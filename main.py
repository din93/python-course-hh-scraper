import requests, json, time
from statistics import mean
from math import floor
from os import mkdir, path
import utils

print('Добро пожаловать в мини-агрегатор информации по вакансиям!\n(При поддержке api.hh.ru)')

vacancy_name = input('Введите желаемую профессию для получения по ней общей информации: ').strip().capitalize()

vacancies = utils.get_vacancies(vacancy_name)

vacancies_count_by_areas = utils.get_vacancies_count_by_areas(vacancies)

area_vacancies = []
while len(area_vacancies)==0:
    chosen_area = input('Введите название желаемого региона (либо пропустите): ').strip().capitalize()
    area_vacancies = utils.get_area_vacancies(vacancies, chosen_area)
    if len(area_vacancies)>0:
        chosen_area = area_vacancies[0]["area"]["name"]
        print(f'\nВ регионе "{chosen_area}" найдено {len(area_vacancies)} вакансий')
    elif chosen_area:
        print(f'\nНе найдено вакансий в области "{chosen_area}"')
        print(f'Доступные области с вакансиями "{vacancy_name}":')
        time.sleep(3)
        utils.print_avalable_areas(vacancies_count_by_areas)
    elif not chosen_area:
        break

if len(area_vacancies)==0:
    print(f'\nВсего найдено вакансий по специальности "{vacancy_name}":', len(vacancies))

salaries = utils.get_avalable_salaries(area_vacancies if len(area_vacancies) else vacancies)

mean_salaries_by_curr = None
if len(salaries):
    print('\nВакансий с указанной заработной платой:', len(salaries))
    mean_salaries_by_curr = utils.get_mean_salaries_by_curr(salaries)
    utils.print_mean_salaries(mean_salaries_by_curr)
else:
    print(f'К сожалению нет возможности получить информацию о заработной плате в выбранном регионе')

print(f'\nЗагрузка детальной информации для {len(vacancies)} вакансий...')
vacancies_detailed = utils.get_vacancies_detailed(vacancies, print_progress=True)

key_skills = utils.get_key_skills(vacancies_detailed)

print(f'\nВостребованность навыков по существующим вакансиям "{vacancy_name}":')
for key_skill in key_skills:
    print(f'{key_skill["name"]}: {key_skill["count"]} ({key_skill["persentage"]}%)')
print()

json_report = utils.get_json_report(
    vacancy_name,
    key_skills,
    vacancies_count_by_areas,
    area_vacancies if len(area_vacancies) else vacancies,
    chosen_area,
    salaries,
    mean_salaries_by_curr
)

if not path.exists('./reports'):
    mkdir('./reports')
report_filename = f'report-{vacancy_name.replace(" ", "_")}-{chosen_area}.json'
with open(f'./reports/{report_filename}', 'w', encoding='utf8') as file:
    file.write(json.dumps(json_report, ensure_ascii=False, indent=2))
print(f'Результаты по вакансии записаны в файл {report_filename}.')
input('Нажмите Enter для завершения ')