from controllers import app, db
from controllers.models import Service, Admin, Professional, ServiceRequests, Customer, ServiceLocation
from werkzeug.security import generate_password_hash

# def update_db():
if __name__ == "__main__":
    with app.app_context():
        # # Delete all instances of the Professional model
        # db.session.query(ServiceLocation).delete()
        # db.session.commit()

        # admin1=Admin(email='Ay@yahoo.com', password=generate_password_hash('123456'))
        # db.session.add(admin1)
        # db.session.commit()
        # professionals = Professional.query.all()
        # for prof in professionals:
        #     print(prof.document_path)
        db.create_all()
        # db.drop_all()
        # services=Service.query.all()
    app.run(debug=True)