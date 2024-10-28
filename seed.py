from app import db, app
from app.models import Country

def seed_countries():
    countries = [
        {'name': 'Kenya', 'code': 'KE'},
        {'name': 'United States', 'code': 'US'},
        {'name': 'United Kingdom', 'code': 'GB'},
        {'name': 'Canada', 'code': 'CA'},
        {'name': 'Australia', 'code': 'AU'},
        {'name': 'India', 'code': 'IN'},
        {'name': 'Germany', 'code': 'DE'},
        {'name': 'France', 'code': 'FR'},
        {'name': 'South Africa', 'code': 'ZA'},
        {'name': 'Nigeria', 'code': 'NG'},
        {'name': 'Japan', 'code': 'JP'},
        {'name': 'China', 'code': 'CN'},
        {'name': 'Brazil', 'code': 'BR'},
        {'name': 'Mexico', 'code': 'MX'},
        {'name': 'Argentina', 'code': 'AR'},
    ]
    
    for country in countries:
        new_country = Country(name=country['name'], code=country['code'])
        db.session.add(new_country)

    db.session.commit()
    print("Countries seeded successfully.")

if __name__ == "__main__":
       with app.app_context():  # Set the application context
        seed_countries()
