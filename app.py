from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from forms import UploadForm, SearchForm, EmployeeForm
import os
from testOCR import find_names_all
from datetime import datetime
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_principal import Permission, RoleNeed

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.secret_key = 'your_secret_key'  # Для использования flash сообщений
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'your_secret_key'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref='users')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), nullable=False)
    filenames = db.Column(db.String(100), nullable=False)
    employees = db.Column(db.String(200), nullable=True)  # Список сотрудников
    otmetka = db.Column(db.Boolean, nullable=False, default=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)  # Новое поле для даты

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# Инициализация ролей и пользователей
@app.route('/init_db')
def init_db():
    with app.app_context():
        db.create_all()  # Создание всех таблиц в базе данных

        # Проверка на существование ролей
        if not Role.query.filter_by(name='admin').first():
            admin_role = Role(name='admin')
            db.session.add(admin_role)

        if not Role.query.filter_by(name='manager').first():
            manager_role = Role(name='manager')
            db.session.add(manager_role)

        db.session.commit()

        # Проверка на существование пользователей
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', password=generate_password_hash('DUALMESH'), role_id=admin_role.id)
            db.session.add(admin_user)

        if not User.query.filter_by(username='manager').first():
            manager_user = User(username='manager', password=generate_password_hash('DUALMESH'), role_id=manager_role.id)
            db.session.add(manager_user)

        db.session.commit()
    return 'База данных инициализирована!'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
@app.route("/admin")
def admin():
    if current_user.role.name not in ['admin', 'manager']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    return render_template("home.html")
@app.route('/')
def home():
    return redirect(url_for('search_order'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_order():
    # Проверка на роль пользователя
    if current_user.role.name not in ['admin', 'manager']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))

    form = UploadForm()
    if form.validate_on_submit():
        files = request.files.getlist('files')  # Получаем список загружаемых файлов
        filenames = []
        
        for file in files:
            if file:
                filename = file.filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filenames.append(filename)

        # Получаем список сотрудников из базы данных
        employees = Employee.query.all()
        names_list = [employee.name.split()[0] for employee in employees]

        # Предполагаем, что вы хотите использовать первый загруженный файл для поиска имен
        if filenames:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filenames[0])
            found_names = find_names_all(names_list, pdf_path)
        else:
            found_names = []

        # Сохраняем все имена файлов и найденные имена сотрудников в базу данных
        new_order = Order(
            number=form.number.data,
            filenames=','.join(filenames),
            employees=','.join(found_names),
            date=form.date.data  # Сохраняем дату
        )
        db.session.add(new_order)
        db.session.commit()
        flash('Приказ успешно загружен!', 'success')
        return redirect(url_for('upload_order'))
    
    return render_template('upload.html', form=form)

@app.route('/edit_employee/<int:id>', methods=['POST'])
@login_required
def edit_employee(id):
    if current_user.role.name not in ['admin']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    employee = Employee.query.get_or_404(id)
    new_name = request.form.get('new_name')
    if new_name:
        employee.name = new_name
        db.session.commit()
        flash('Сотрудник успешно обновлен!', 'success')
    else:
        flash('Имя сотрудника не может быть пустым.', 'danger')
    return redirect(url_for('manage_employees'))

@app.route('/search', methods=['GET', 'POST'])
def search_order():
    form = SearchForm()
    results = []
    employees_set = set()  # Множество для уникальных сотрудников
    sort_option = request.form.get('sort', 'date_desc')  # Получаем выбранный параметр сортировки

    if form.validate_on_submit():
        # Поиск по номеру приказа
        if form.name.data:
            results = Order.query.filter(Order.employees.contains(form.name.data) | Order.number.contains(form.name.data)).all()
        else:
            results = Order.query.all()

        # Сортировка
        if sort_option == 'date_asc':
            results = sorted(results, key=lambda x: x.date)
        elif sort_option == 'date_desc':
            results = sorted(results, key=lambda x: x.date, reverse=True)
        elif sort_option == 'number_asc':
            results = sorted(results, key=lambda x: x.number)
        elif sort_option == 'number_desc':
            results = sorted(results, key=lambda x: x.number, reverse=True)

        # Собираем уникальные ФИО сотрудников из найденных приказов
        for order in results:
            employees = order.employees.split(',')
            for employee in employees:
                employees_set.add(employee.strip())

        if not results:
            flash('Приказы не найдены.', 'warning')
    else:
        results = Order.query.all()

    return render_template('search.html', form=form, results=results, employees=employees_set)
@login_required
@app.route('/employees', methods=['GET', 'POST'])
def manage_employees():
    if current_user.role.name not in ['admin']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    form = EmployeeForm()
    if form.validate_on_submit():
        new_employee = Employee(name=form.name.data)
        db.session.add(new_employee)
        db.session.commit()
        flash('Сотрудник успешно добавлен!', 'success')
        return redirect(url_for('manage_employees'))
    employees = Employee.query.all()
    return render_template('employees.html', form=form, employees=employees)

@app.route('/delete_employee/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    if current_user.role.name not in ['admin']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    flash('Сотрудник успешно удален!', 'success')
    return redirect(url_for('manage_employees'))
@app.route('/employee_orders/<employee_name>')
def employee_orders(employee_name):
    orders = Order.query.filter(Order.employees.contains(employee_name)).all()
    return render_template('employee_orders.html', employee_name=employee_name, orders=orders)
@app.route('/order/<int:order_id>')
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('view_order.html', order=order)

@app.route('/admin_order/<int:order_id>')
@login_required
def admin_order(order_id):
    if current_user.role.name not in ['admin']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    order = Order.query.get_or_404(order_id)
    return render_template('admin_order.html', order=order)

@app.route('/master')
@login_required
def master():
    if current_user.role.name not in ['admin']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    results_new = []
    results=[]
    for order in Order.query.all():
        if order.otmetka:
            results.append(order)
        else:
            results_new.append(order)
    return render_template('master.html',results_new=results_new,results=results)
@app.route('/update_employee_names/<int:order_id>', methods=['POST'])
@login_required
def update_employee_names(order_id):
    if current_user.role.name not in ['admin']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    order = Order.query.get_or_404(order_id)
    
    new_names = request.form.get('new_names')
    
    if new_names:
        # Обновляем имена сотрудников в заказе
        order.employees = new_names
        db.session.commit()
        flash('Имена сотрудников успешно обновлены!', 'success')
    else:
        flash('Имена сотрудников не могут быть пустыми.', 'danger')
    
    return redirect(url_for('admin_order', order_id=order_id))
@app.route('/use_ai/<int:order_id>')
@login_required
def use_ai(order_id):
    if current_user.role.name not in ['admin']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    order = Order.query.get_or_404(order_id)
    file=order.filenames.split(',')[0]
    if file:
        # Получаем список сотрудников из базы данных
        employees = Employee.query.all()
        names_list = [employee.name.split()[0] for employee in employees]

        # Предполагаем, что вы хотите использовать первый загруженный файл для поиска имен
        if file:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
            found_names = find_names_all(names_list, pdf_path)
        else:
            found_names = []

        # Сохраняем все имена файлов и найденные имена сотрудников в базу данных
        order.employees=','.join(found_names)
        db.session.commit()
    return redirect(url_for('admin_order', order_id=order_id))
@app.route('/checked/<int:order_id>')
@login_required
def checked(order_id):
    if current_user.role.name not in ['admin']:
        flash('У вас нет доступа к этой странице.', 'danger')
        return redirect(url_for('home'))
    order = Order.query.get_or_404(order_id)
    order.otmetka=True
    db.session.commit()
    return redirect(url_for('admin_order', order_id=order_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создание всех таблиц в базе данных
    app.run(debug=True)