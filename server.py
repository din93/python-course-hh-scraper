from flask import Flask, render_template, request
import requests, utils, db_orm

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/form")
def form():
    db_orm.delete_inactual_queries()
    region_names = db_orm.get_region_names()
    if not len(region_names):
        region_names = utils.get_big_city_names()
        db_orm.add_regions(region_names)

    input_vacancy = request.args.get('input_vacancy', '').strip().capitalize()
    input_region = request.args.get('input_region', '')
    if input_vacancy:
        vacancies_info = db_orm.get_vacancy_queries_cache(input_vacancy, input_region)
        if vacancies_info is None:
            vacancies_info = utils.scrape_vacancies_info(input_vacancy, input_region)
            db_orm.add_vacancy_queries_cache(
                input_vacancy,
                None if input_region=='' else input_region,
                vacancies_info['count'],
                vacancies_info['key_skills'],
                vacancies_info['mean_salaries_by_curr']
            )
    else:
        vacancies_info = None

    template_params = dict(
        vacancies_info=vacancies_info,
        region_names=region_names,
        input_vacancy=input_vacancy,
        input_region=input_region.capitalize()
    )

    return render_template('form.html', **template_params)

@app.route("/contacts")
def contacts():
    contacts = db_orm.get_contacts()

    if not len(contacts):
        db_orm.add_contact('Радик Динов', 'Уфа', None, 'https://vk.com/din_93', 'https://t.me/din_93', '/static/img/author.png')
        contacts = db_orm.get_contacts()
    
    return render_template('contacts.html', contacts=contacts)

if __name__ == "__main__":
    app.run(debug=True)
