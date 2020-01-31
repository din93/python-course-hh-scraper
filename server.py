from flask import Flask, render_template, request
import requests, utils

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/form")
def form():
    utils.db_delete_inactual_queries()
    region_names = utils.db_get_region_names_cache()
    if region_names is None:
        region_names = utils.scrape_region_names()
        utils.db_save_regions_cache(region_names)

    input_vacancy = request.args.get('input_vacancy', '').strip().capitalize()
    input_region = request.args.get('input_region', '')
    if input_vacancy:
        vacancies_info = utils.db_get_vacancy_queries_cache(input_vacancy, None if input_region=='' else input_region)
        if vacancies_info is None:
            vacancies_info = utils.scrape_vacancies_info(input_vacancy, input_region)
            utils.db_save_vacancy_queries_cache(
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
    contacts = utils.db_get_contacts()
    
    return render_template('contacts.html', contacts=contacts)

if __name__ == "__main__":
    app.run(debug=True)