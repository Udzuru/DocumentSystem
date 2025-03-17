from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField
from wtforms.validators import DataRequired
from wtforms import DateField
from wtforms import StringField, SelectField, SubmitField

class UploadForm(FlaskForm):
    number = StringField('Номер приказа', validators=[DataRequired()])
    files = FileField('Файлы приказа', validators=[DataRequired()])  # Изменено на files для поддержки нескольких файлов
    submit = SubmitField('Загрузить приказ')
    date = DateField('Дата', format='%Y-%m-%d', validators=[DataRequired()])  # Добавлено поле даты



class SearchForm(FlaskForm):
    name = StringField('Поиск по номеру приказа или сотруднику')
    sort = SelectField('Сортировка', choices=[
        ('date_desc', 'Дате (по убыванию)'),
        ('date_asc', 'Дате (по возрастанию)'),
        ('number_asc', 'Номеру (по возрастанию)'),
        ('number_desc', 'Номеру (по убыванию)')
    ])
    submit = SubmitField('Поиск')


class EmployeeForm(FlaskForm):
    name = StringField('ФИО сотрудника', validators=[DataRequired()])
    submit = SubmitField('Добавить сотрудника')