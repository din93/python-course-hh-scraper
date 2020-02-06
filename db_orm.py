from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Table, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import datetime

engine = create_engine('sqlite:///va_cache_orm.sqlite', echo=False)

Base = declarative_base()

class Region(Base):
    __tablename__ = 'regions'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f'<Region "{self.name}", id: {self.id}>'

class VacancyQuery(Base):
    __tablename__ = 'vacancy_queries'
    id = Column(Integer, primary_key=True)
    vacancy_query = Column(String, nullable=False)
    query_region = Column(Integer, ForeignKey('regions.name'))
    vacancies_count = Column(Integer, nullable=False)
    datetime_created = Column(DateTime, nullable=False, server_default=func.now())

    def __init__(self, vacancy_query, query_region, vacancies_count):
        self.vacancy_query = vacancy_query
        self.query_region = query_region
        self.vacancies_count = vacancies_count
        self.datetime_created
    
    def __repr__(self):
        return f'<VacancyQuery "{self.vacancy_query}", query_region:  {self.query_region}, id: {self.id}>'

class KeySkill(Base):
    __tablename__ = 'key_skills'
    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancy_queries.id'), nullable=False)
    name = Column(String(50), nullable=False)
    count = Column(Integer, nullable=False)
    persentage = Column(Integer, nullable=False)

    def __init__(self, vacancy_id, name, count, persentage):
        self.vacancy_id = vacancy_id
        self.name = name
        self.count = count
        self.persentage = persentage
    
    def __repr__(self):
        return f'<KeySkill "{self.name}", vacancy_id:  {self.vacancy_id}, id: {self.id}>'

class MeanSalary(Base):
    __tablename__ = 'mean_salaries_by_curr'
    id = Column(Integer, primary_key=True)
    vacancy_id = Column(Integer, ForeignKey('vacancy_queries.id'), nullable=False)
    currency = Column(String(3), nullable=False)
    value = Column(Integer, nullable=False)
    salaries_count = Column(Integer, nullable=False)

    def __init__(self, vacancy_id, currency, value, salaries_count):
        self.vacancy_id = vacancy_id
        self.currency = currency
        self.value = value
        self.salaries_count = salaries_count
    
    def __repr__(self):
        return f'<MeanSalary "{self.value} {self.currency}", vacancy_id:  {self.vacancy_id}, id: {self.id}>'

class ContactInfo(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String)
    email = Column(String)
    vk = Column(String)
    telegram = Column(String)
    img_src = Column(String)

    def __init__(self, name, city, email, vk, telegram, img_src):
        self.name = name
        self.city = city
        self.email = email
        self.vk = vk
        self.telegram = telegram
        self.img_src = img_src
    
    def __repr__(self):
        return f'<ContactInfo "{self.name}", city:  {self.city}, email: {self.email}, id: {self.id}>'

Base.metadata.create_all(engine)


def add_vacancy_queries_cache(vacancy_query, query_region, vacancies_count, key_skills, mean_salaries_by_curr):
    Session = sessionmaker(bind=engine)
    session = Session()
    vacancy_query_object = VacancyQuery(vacancy_query, query_region, vacancies_count)
    session.add(vacancy_query_object)
    session.flush()
    vacancy_id = vacancy_query_object.id
    session.add_all([
        KeySkill(
            vacancy_id,
            key_skill.get('name'),
            key_skill.get('count'),
            key_skill.get('persentage')
        ) for key_skill in key_skills
    ])
    session.add_all([
        MeanSalary(
            vacancy_id,
            item.get('currency'),
            item.get('value'),
            item.get('salaries_count')
        ) for item in mean_salaries_by_curr
    ])
    session.commit()

def get_vacancy_queries_cache(vacancy_query, query_region=None):
    Session = sessionmaker(bind=engine)
    session = Session()
    query = session.query(VacancyQuery).filter(VacancyQuery.vacancy_query == vacancy_query)
    if query_region:
        vacancy_query_result = query.filter(VacancyQuery.query_region == query_region).first()
    else:
        vacancy_query_result = query.filter(VacancyQuery.query_region == None).first()
    if vacancy_query_result:
        key_skills_result = session.query(KeySkill).filter(KeySkill.vacancy_id == vacancy_query_result.id).all()
        mean_salaries_result = session.query(MeanSalary).filter(MeanSalary.vacancy_id == vacancy_query_result.id).all()
        key_skills = [
            {'name': key_skill.name, 'count': key_skill.count, 'persentage': key_skill.persentage} for key_skill in key_skills_result
        ]
        mean_salaries = [
            {'currency': mean_salary.currency, 'value': mean_salary.value, 'salaries_count': mean_salary.salaries_count} for mean_salary in mean_salaries_result
        ]
    else:
        return None
    
    return {
        'vacancy_query': vacancy_query_result.vacancy_query,
        'query_region': vacancy_query_result.query_region,
        'count': vacancy_query_result.vacancies_count,
        'key_skills': key_skills,
        'mean_salaries_by_curr': mean_salaries
    }

def delete_inactual_queries():
    Session = sessionmaker(bind=engine)
    session = Session()
    inactual_vacancy_queries = session.query(VacancyQuery).filter(VacancyQuery.datetime_created < func.current_date()).all()
    inactual_vacancy_ids = [vacancy_query.id for vacancy_query in inactual_vacancy_queries]
    session.query(VacancyQuery).filter(VacancyQuery.datetime_created < func.current_date()).delete(synchronize_session='fetch')
    session.query(KeySkill).filter(KeySkill.vacancy_id.in_(inactual_vacancy_ids)).delete(synchronize_session='fetch')
    session.query(MeanSalary).filter(MeanSalary.vacancy_id.in_(inactual_vacancy_ids)).delete(synchronize_session='fetch')
    session.commit()

def add_regions(region_names):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add_all([Region(region_name) for region_name in region_names])
    session.commit()

def get_region_names():
    Session = sessionmaker(bind=engine)
    session = Session()
    regions_result = session.query(Region).all()

    if len(regions_result):
        regions_result = [region.name for region in regions_result]

    return regions_result

def add_contact(name, city, email, vk, telegram, img_src):
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(ContactInfo(name, city, email, vk, telegram, img_src))
    session.commit()


def get_contacts():
    Session = sessionmaker(bind=engine)
    session = Session()
    contacts_result = session.query(ContactInfo).all()

    if len(contacts_result):
        contacts_result = [
            {
                'name': contact_info.name,
                'city': contact_info.city,
                'email': contact_info.email,
                'vk': contact_info.vk,
                'telegram': contact_info.telegram,
                'img_src': contact_info.img_src,
            } for contact_info in contacts_result
        ]

    return contacts_result
