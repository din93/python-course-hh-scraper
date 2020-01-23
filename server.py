from flask import Flask, render_template, request
import requests, itertools, utils

def get_region_names():
    regions_response = requests.get('https://api.hh.ru/areas').json()
    districts = itertools.chain.from_iterable([region['areas'] for region in regions_response])
    city_names = [
        city['name'] for city in
        itertools.chain.from_iterable([district['areas'] for district in districts])
    ]
    city_names = sorted(city_names)
    return city_names

def get_vacancies_info(input_vacancy, input_region):
    if input_vacancy:
        vacancies = utils.get_vacancies(input_vacancy)
        if input_region:
            vacancies = utils.get_area_vacancies(vacancies, input_region)
        salaries = utils.get_avalable_salaries(vacancies if len(vacancies) else vacancies)
        mean_salaries_by_curr = utils.get_mean_salaries_by_curr(salaries)
        key_skills = utils.get_key_skills(
            utils.get_vacancies_detailed(vacancies[:20] if len(vacancies)>20 else vacancies)
        )
        return {
            'count': len(vacancies),
            'mean_salaries_by_curr': mean_salaries_by_curr,
            'key_skills': key_skills[:15] if len(key_skills)>15 else key_skills
        }
    else:
        return None

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/form")
def form():
    region_names = get_region_names()

    input_vacancy = request.args.get('input_vacancy', '').strip().capitalize()
    input_region = request.args.get('input_region', '')
    vacancies_info = get_vacancies_info(input_vacancy, input_region)

    template_params = dict(
        vacancies_info=vacancies_info,
        region_names=region_names,
        input_vacancy=input_vacancy,
        input_region=input_region.capitalize()
    )

    return render_template('form.html', **template_params)

@app.route("/contacts")
def contacts():
    contacts = [
        {'name': 'Радик Динов', 'city': 'Уфа', 'vk': 'https://vk.com/din_93', 'telegram': 'https://t.me/din_93', 'img_src': '/static/img/author.png'},
        {'name': 'Иванов Иван', 'city': 'Москва', 'vk': 'https://vk.com/ivanov_ivan'}
    ]
    return render_template('contacts.html', contacts=contacts)

if __name__ == "__main__":
    app.run(debug=True)