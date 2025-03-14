from controllers import app, db
from controllers.models import Admin, User
from werkzeug.security import generate_password_hash

# def update_db():
if __name__ == "__main__":
    with app.app_context():
        # # Delete all instances of the Professional model
        # db.session.query(Admin).delete()
        # db.session.commit()

        # admin1=Admin(email='Ay@admin.com', password=generate_password_hash('123456'))
        # # quiz1=Quiz(chapter_id=1, date_of_quiz=word=, time_duration='01:00')
        # db.session.add(admin1)
        # db.session.commit()
        # professionals = Professional.query.all()
        # for prof in professionals:
        #     print(prof.document_path)
        # db.drop_all()
        db.create_all()
        # services=Service.query.all()
    app.run(debug=True, port=8000)


