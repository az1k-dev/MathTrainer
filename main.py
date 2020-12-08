# coding=UTF-8
# Проект PyQT
# Математический тренажер
# Автор: Байрамов Азамат

import sys
from PyQt5 import uic
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QTime, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, \
    QTableWidgetItem
from PyQt5.QtGui import QIntValidator
import sqlite3
import threading
from random import choice, randint
import time
import datetime


def sql_user_to_dict(user_sql):
    # Функция для преобразования SQL-запроса данных пользователя в словарь
    if user_sql:
        return {
            'id': user_sql[0],
            'login': user_sql[1],
            'password': user_sql[2],
            'name': user_sql[3],
            'surname': user_sql[4],
        }
    else:
        return False


def sql_settings_to_dict(setttings_sql):
    # Функция для преобразования SQL-запроса настроек в словарь
    out = {}
    for i in setttings_sql:
        out[i[1]] = i[2]
    return out


def thread(func):
    # Функция-декоратор для выведения функции в отдельный поток
    def threading_func(*args, **kwargs):
        new_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        new_thread.start()

    return threading_func


def make_question(difficult):
    # Функция для создания примеров
    funcs = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: int(a * b),
        '/': lambda a, b: int(a / b)
    }

    ints = DIFFICUTL_DICT[difficult]

    if len(ints) == 2:
        znak = choice(['+', '-'])
        a = randint(ints[0], ints[1])
        b = randint(ints[0], ints[1])
    elif len(ints) == 4:
        znak = choice(['+', '-', '*', '/'])
        if znak in ['+', '-']:
            a = randint(ints[0], ints[1])
            b = randint(ints[0], ints[1])
        else:
            a = randint(ints[2], ints[3])
            b = randint(ints[2], ints[3])
            if znak == '/':
                a = a * b

    question = str(a) + znak + str(b)
    func = funcs[znak]
    answer = func(a, b)

    return {'question': question, 'answer': str(answer)}


class Communicate(QObject):
    # Класс для хранения сигналов
    # Создается один раз
    # При инициализации разных окон передается из класса в класс
    account_deleted = pyqtSignal()
    password_changed = pyqtSignal(str)
    registered = pyqtSignal()
    round_started = pyqtSignal(int)
    settings_updated = pyqtSignal(dict)


# Создаем постоянные
DATABASE_NAME = 'math_training.db'
sql_con = sqlite3.connect(DATABASE_NAME)
sql_cur = sql_con.cursor()
SQL = {'con': sql_con, 'cur': sql_cur}
COMMUNICATE_CLASS = Communicate()
DIFFICUTL_DICT = {
    0: [1, 10],
    1: [10, 20, 2, 10],
    2: [20, 100, 10, 20],
    3: [100, 1000, 20, 50]
}


def main():
    app = QApplication(sys.argv)
    ex = AuthorizationWindow()
    sys.exit(app.exec_())


class AuthorizationWindow(QMainWindow):
    # Класс окна авторизации

    def __init__(self):
        # Инициализация класса

        # Инициализация родителского класса и
        # загрузка дизайна программы из ui файла
        super().__init__()
        uic.loadUi('UI/AuthorizationWindow.ui', self)

        # Проверка наличия сохраненного пользователя
        remembered_user = sql_user_to_dict(SQL['cur'].execute(
            """SELECT * FROM Users
            WHERE remember = 1"""
        ).fetchone())

        if remembered_user:
            # При наличии сохраненного пользователя,
            # программа запускает главное окно программы
            self.show_main_window(remembered_user)
        else:
            # Создание слотов для нажатия кнопок
            self.login_button.clicked.connect(self.login)
            self.registration_button.clicked.connect(
                self.show_registration_window
            )

            # Показ окна авторизации
            self.show()

    def login(self):
        # Функция для проверки авторизационных данных
        # и выполнения последующих действий

        # Получение данных из полей ввода
        login = self.login_input.text()
        password = self.password_input.text()
        remember = self.remember_box.isChecked()

        # Проверка корректоности ввода данных и последующие действия
        if not login:
            self.error_line.setText('Введите логин и пароль')
        elif not password:
            self.error_line.setText('Введите логин и пароль')
        else:
            # При корректности введенных данных
            # начинается проверка по базе данных
            user_sql = sql_user_to_dict(SQL['cur'].execute(
                """SELECT * FROM Users
                WHERE login = ?""", (login,)
            ).fetchone())

            if user_sql:
                if password == user_sql['password']:
                    if remember:
                        SQL['cur'].execute("""UPDATE Users
                            SET remember = 1
                            WHERE id = ?""", (user_sql['id'],)).fetchall()
                        SQL['con'].commit()
                    self.show_main_window(user_sql)

            self.error_line.setText('Неверный логин или пароль')

    def show_main_window(self, user_info):
        # Функция для инициализации и показа главного окна программы
        self.main_window = MainWindow(user_info)
        self.main_window.show()

        self.close()

    def show_registration_window(self):
        # Функция для инициализации и показа окна регистрации
        self.reg_window = RegistrationWindow()
        self.reg_window.show()

        self.close()


class RegistrationWindow(QMainWindow):
    # Класс окна регистрации

    def __init__(self):
        # Инициализация класса

        # Инициализация родителского класса и
        # загрузка дизайна программы из ui файла
        super().__init__()
        uic.loadUi('UI/RegistrationWindow.ui', self)

        # Создание слотов для нажатия кнопок
        self.registration_button.clicked.connect(self.registration)
        self.auth_window_button.clicked.connect(self.show_auth_window)

        # Создание переменной для проверки регистрации
        self.registered = False

    def closeEvent(self, event):
        # Переопределение сигнала closeEvent для
        # открытия окна авторизации при закрытии окна
        if not self.registered:
            # Окно авторизации создается только при отсутствии регистрации
            self.show_auth_window()

    def registration(self):
        # Функция для проверки регистрационных
        # данных и выполнения последующих действий

        # Получение данных из полей ввода
        name = self.name_input.text()
        surname = self.surname_input.text()
        login = self.login_input.text()
        password_1 = self.password_input.text()
        password_2 = self.password_input_2.text()
        remember = self.remember_box.isChecked()

        # Переменная для проверки правильности данных
        reg_check = True

        # SQL-запрос для проверки отсутсвия логина
        login_check = SQL['cur'].execute("""SELECT * from Users
            WHERE login = ?""", (login,)).fetchall()

        # Проверка данных
        if password_1 != password_2:
            self.error_line.setText('Пароли не совпадают')
            reg_check = False
        if login_check:
            self.error_line.setText('Логин занят')
            reg_check = False
        if not name or not surname or not \
                login or not password_1 or not password_2:
            self.error_line.setText('Заполните все поля')
            reg_check = False

        # При успешной проверке регистрация пользователя
        # и показ главного окна программы
        if reg_check:
            # Занесение данных в базу данных
            SQL['cur'].execute(
                """INSERT INTO Users(login, password, name, surname, remember)
                VALUES(?, ?, ?, ?, ?)""",
                (login, password_1, name, surname, remember)
            ).fetchall()

            SQL['con'].commit()

            # Получение данных для передачи в главное окно
            self.user_info = sql_user_to_dict(SQL['cur'].execute(
                """SELECT * from Users
                WHERE login = ?""", (login,)
            ).fetchone())

            # Изменение переменной для предотвращения открытия окна
            # авторизации событием closeEvent при закрытии данного
            # окна в функции show_main_window
            self.registered = True

            # Показ главного окна программы
            self.show_main_window()

    def show_main_window(self):
        # Функция для инициализации и показа главного окна программы
        self.main_window = MainWindow(self.user_info)
        self.main_window.show()

        self.close()

    def show_auth_window(self):
        # Функция для возвращения к окну авторизации
        self.auth_window = AuthorizationWindow()
        self.auth_window.show()

        self.close()


class MainWindow(QMainWindow):
    # Класс главного окна

    def __init__(self, user_info):
        # Инициализация класса

        # Инициализация родителского класса и
        # загрузка дизайна программы из ui файла
        super().__init__()
        uic.loadUi('UI/MainWindow.ui', self)

        # Закрепление данных о пользователе
        self.user_info = user_info

        # Создание слотов для кастомных сигналов
        COMMUNICATE_CLASS.password_changed.connect(self.update_password_info)
        COMMUNICATE_CLASS.account_deleted.connect(self.show_auth_window)

        # Создание слотов для нажатий кнопок верхнего меню
        self.exit_account_button.triggered.connect(self.exit_account)
        self.exit_program_button.triggered.connect(self.close)
        self.help_button.triggered.connect(self.show_help_window)
        self.personal_info_button.triggered.connect(
            self.show_personal_info_window)
        self.settings_button.triggered.connect(self.show_settings_window)
        self.statistic_button.triggered.connect(self.show_statistic_window)

        # Создание слотов для смены ComboBox-ов
        self.difficult_box.currentIndexChanged.connect(self.update_top_list)
        self.difficult_box.currentIndexChanged.connect(
            self.update_difficult_info)
        self.stop_mode_box.currentIndexChanged.connect(
            self.update_stop_count_line)

        # Создание слотов для нажатия кнопки основного экрана
        self.start_button.clicked.connect(self.show_solve_window)

        # Обновление таблицы и информации на главном экране
        self.update_top_list(0)
        self.update_difficult_info(0)
        self.update_stop_count_line(0)

        # Установка валидатора для поля ввода(только целые числа)
        self.stop_count_line.setValidator(QIntValidator(5, 50000000))

    def exit_account(self):
        # Функция для выхода из аккаунта

        # В базе данных параметр remember пользователя меняется на 0
        SQL['cur'].execute("""UPDATE Users
            SET remember = 0
            WHERE id = ?""", (self.user_info['id'],)).fetchall()
        SQL['con'].commit()

        # Показывается окно авторизации
        self.show_auth_window()

    def show_auth_window(self):
        # Функция для инициализации и показа окна авторизации
        self.auth_window = AuthorizationWindow()
        self.auth_window.show()
        self.close()

    def show_help_window(self):
        # Функция для инициализации и показа окна помощи
        self.help_window = HelpWindow()
        self.help_window.show()

    def show_personal_info_window(self):
        # Функция для инициализации и показа окна личных данных
        self.personal_info_window = PersonalInfoWindow(self.user_info)
        self.personal_info_window.show()

    def show_settings_window(self):
        # Функция для инициализации и показа окна настроек
        self.settings_window = SettingsWindow()
        self.settings_window.show()

    def update_password_info(self, new_password):
        # Функция для изменения данных о пароле в словаре user_info
        self.user_info['password'] = new_password

    def update_difficult_info(self, index):
        # Функция для заполнения информации об уровне сложности
        # Запускается каждый раз при выборе уровня сложности
        # Принимает индекс выбранного уровня
        difficult_info = DIFFICUTL_DICT[index]

        if len(difficult_info) == 2:
            fill_lst = [str(difficult_info[0]) + '-' + str(difficult_info[1]),
                        'отсутствует']

        elif len(difficult_info) == 4:
            fill_lst = [str(difficult_info[0]) + '-' + str(difficult_info[1]),
                        str(difficult_info[2]) + '-' + str(difficult_info[3])]
        else:
            fill_lst = ['', '']

        self.difficult_info.setText(
            'Сложение и вычитание: {}\nУмножение и деление: {}'
                .format(*fill_lst)
        )

    def update_top_list(self, index):
        # Функция для заполнения таблицы лучших результатов
        # пользователя для определенного уровня
        # Запускается каждый раз при выборе уровня сложности
        # Принимает индекс выбранного уровня

        # Получаем результаты из базы данных и сортируем по коэфифиценту
        results = SQL['cur'].execute(
            '''SELECT * from Results
            WHERE user_id = ? AND difficult = ?''',
            (self.user_info['id'], index)
        ).fetchall()

        results.sort(key=lambda s: s[-1], reverse=True)

        # Очищаем виджет от предыдущих результатов
        # и заполняем навзвания столбцов
        self.best_results_table_widget.clear()
        self.best_results_table_widget.setHorizontalHeaderLabels(
            ['Дата', 'Время', 'Ответов', 'Верных ответов', 'Коэфицент']
        )

        # Заполняем первыми 5 результатами и ровняем таблицу
        for i, lst in enumerate(results[:5]):
            self.best_results_table_widget.setItem(
                i, 0, QTableWidgetItem(lst[2][:16])
            )
            self.best_results_table_widget.setItem(
                i, 1, QTableWidgetItem(str(round(lst[4], 2)))
            )
            self.best_results_table_widget.setItem(
                i, 2, QTableWidgetItem(str(lst[-3]))
            )
            self.best_results_table_widget.setItem(
                i, 3, QTableWidgetItem(str(lst[-2]))
            )
            self.best_results_table_widget.setItem(
                i, 4, QTableWidgetItem(str(round(lst[-1], 2)))
            )

        self.best_results_table_widget.resizeColumnsToContents()

    def update_stop_count_line(self, index):
        # Функция для изменения фонового текста поля ввода количества
        # времени, примеров или верных ответов для остановки решения
        # в зависимости от выбранного режима
        # Запускается каждый раз при выборе режима остноавки
        # Принимает индекс выбранного режима

        mode_information = {
            0: 'Время решения(сек.)',
            1: 'Количество ответов(шт.)',
            2: 'Количество ответов(шт.)'
        }

        self.stop_count_line.setPlaceholderText(mode_information[index])

    def show_solve_window(self):
        # Функция для инициализации и показа окна решения примеров
        # с проверкой корректности введенного в поле значения

        if self.stop_count_line.text():
            if int(self.stop_count_line.text()) > 0:
                self.solve_window = SolveWindow(
                    difficult=self.difficult_box.currentIndex(),
                    stop_mode=self.stop_mode_box.currentIndex(),
                    stop_count=int(self.stop_count_line.text()),
                    user_info=self.user_info
                )
                self.solve_window.show()
                self.close()
            else:
                self.error_label.setText('Число должно быть больше нуля')
        else:
            self.error_label.setText('Заполните поле')

    def show_statistic_window(self):
        self.statistic_window = StatisticWindow(self.user_info)
        self.statistic_window.show()


class HelpWindow(QMainWindow):
    # Класс окна помощи
    def __init__(self):
        super().__init__()
        uic.loadUi('UI/HelpWindow.ui', self)


class PersonalInfoWindow(QMainWindow):
    # Класс окна личных данных

    def __init__(self, user_info):
        # Инициализация класса

        # Инициализация родителского класса и
        # загрузка дизайна программы из ui файла
        super().__init__()
        uic.loadUi('UI/PersonalInfoWindow.ui', self)

        # Закрепление данных о пользователе
        self.user_info = user_info

        # Создание слотов для кастомных сигналов
        COMMUNICATE_CLASS.account_deleted.connect(self.close)
        COMMUNICATE_CLASS.password_changed.connect(self.update_password_info)

        # Создание слотов для нажатий кнопок

        self.password_change_button.clicked.connect(
            self.show_change_password_window
        )

        self.account_delete_button.clicked.connect(self.delete_account)

        # Заполнение окна данными
        self.login_label.setText('Логин: ' + self.user_info['login'])
        self.name_label.setText(
            self.user_info['surname'] + ' ' + self.user_info['name']
        )
        self.id_label.setText('ID: ' + str(self.user_info['id']))

    def show_change_password_window(self):
        # Функция для инициализации и показа окна смены пароля
        self.change_password_window = PasswordChange(self.user_info)
        self.change_password_window.show()

    def update_password_info(self, new_password):
        # Функция для изменения данных о пароле в словаре user_info
        self.user_info['password'] = new_password

    def delete_account(self):
        # Функция для удаления аккауна с подтверждением
        text, ok = QInputDialog.getText(self, "Подтверждение",
                                        "Введите слово 'Подтверждение'")
        if ok and text.lower() == 'подтверждение':
            # Удаляется информация о пользователе и все его резултаты
            SQL['cur'].execute("""DELETE from Users
                WHERE id = ?""", (self.user_info['id'],)).fetchall()
            SQL['cur'].execute("""DELETE from Results
                WHERE user_id = ?""", (self.user_info['id'],)).fetchall()
            SQL['con'].commit()

            # Посылается сигнал об удалении аккаунта
            COMMUNICATE_CLASS.account_deleted.emit()


class PasswordChange(QMainWindow):
    # Класс окна смены пароля
    def __init__(self, user_info):
        super().__init__()
        uic.loadUi('UI/PasswordChangeWindow.ui', self)

        self.user_info = user_info

        self.change_button.clicked.connect(self.change)

    def change(self):
        # Функция для смены пароля с проверкой корректности введенных данных

        # Получение данных из полей ввода
        old_password = self.old_password_line.text()
        new_password_1 = self.new_password_line.text()
        new_password_2 = self.new_password2_line.text()

        # Проверка корректности введенных данных
        change = True
        if not old_password or not new_password_1 or not new_password_2:
            self.error_label.setText('Заполните все поля')
            change = False
        if new_password_1 != new_password_2:
            self.error_label.setText('Новые пароли не совпадают')
            change = False
        if old_password != self.user_info['password']:
            self.error_label.setText('Старый пароль неверен')
            change = False

        # При корректности введенных данных:
        if change:
            # Меняется пароль в базе данных
            SQL['cur'].execute("""UPDATE Users
            SET password = ?
            WHERE id = ?""", (new_password_1, self.user_info['id'])).fetchall()
            SQL['con'].commit()

            # Посылается сигнал о смене пароля
            COMMUNICATE_CLASS.password_changed.emit(new_password_1)

            self.close()


class SolveWindow(QMainWindow):
    # Класс окна решения примеров
    def __init__(self, stop_mode, difficult, stop_count, user_info):
        super().__init__()
        uic.loadUi('UI/SolveWindow.ui', self)

        # Закрепление данных о уровне сложности и тд.
        self.stop_mode = stop_mode
        self.difficult = difficult
        self.stop_count = stop_count
        self.user_info = user_info

        # Создаются переменные, используемые в программе
        self.right_count = 0  # Количество верных ответов
        self.count = 0  # Общее количество ответов
        self.input_answer = ''  # Введенный ответ пользователя
        self.started = False  # Переменная, показывающая началось ли решение
        self.closed = False  # Переменная, показывающая закрыто ли окно

        mode_dict = {
            0: 'Осталось времени:',
            1: 'Осталось примеров:',
            2: 'Осталось верных ответов:'
        }

        # Редактируются и скрываются виджеты до начала решения
        self.remained.setText(mode_dict[stop_mode])
        self.lcd.hide()
        self.remained.hide()

        # Из базы данных загружаются настройки
        self.settings = sql_settings_to_dict(
            SQL['cur'].execute('''SELECT * from Settings''').fetchall()
        )

        # Создается слот для начала решения после отсчета
        COMMUNICATE_CLASS.round_started.connect(self.start)

        # Показывается окно и начинается обратный отсчет
        self.show()
        self.start_countdown()

    @thread  # Функция выведена в отдельный поток
    def start_countdown(self):
        # Функция для обратного отсчета времени
        for i in range(self.settings['countdown_duration'], -1, -1):
            # В виджет label помещается оставшееся время в секундах
            self.countdown_label.setText(str(i))

            # Создается и запускатся объект QTime
            time = QTime()
            time.start()
            while True:
                # При достижении 1 секунды, основной цикл перезапускается
                if time.elapsed() > 1000 or self.closed:
                    break

            # При закрытии окна отсчет останавливается
            if self.closed:
                break

        # Отправляется сигнал о начале решения
        COMMUNICATE_CLASS.round_started.emit(self.stop_mode)

    def start(self, stop_mode):
        # Функция для начала решения примеров

        if not self.started:
            self.started = True

            # Скрываются и показываются объекты
            self.label.hide()
            self.countdown_label.hide()
            if self.settings['show_count'] == 2:
                self.lcd.show()
                self.remained.show()

            if stop_mode == 0:
                # При остановке по времени создается таймер
                self.timer = QTimer()
                self.timer.timeout.connect(self.stop)
                self.timer.start(self.stop_count * 1000)
                self.show_time()
            else:
                # При остановке по количеству примеров начинается замер времени
                self.start_time = time.time()
                self.show_count()

            # Создается первый пример
            self.new_question()

    def stop(self):
        # Функция для остановки решения задачи

        # Определение времени решения
        if self.stop_mode == 0:
            self.solve_time = self.stop_count
            self.timer = 0
        else:
            self.solve_time = time.time() - self.start_time

        # Вычисление коэффицента
        coef = self.right_count / self.solve_time

        # Загрузка данных о решении в базу данных
        values = (
            self.user_info['id'], datetime.datetime.today(),
            self.difficult, self.solve_time, self.count,
            self.right_count, coef)
        SQL['cur'].execute(
            '''INSERT INTO Results(user_id, datetime, difficult, 
            solve_duration, tasks_count,correct_answers_count, coefficient)
            VALUES(?, ?, ?, ?, ?, ?, ?)''', values
        ).fetchall()
        SQL['con'].commit()

        # Создается словарь для передачи в следующее окно
        self.result = {'time': round(self.solve_time, 2), 'count': self.count,
                       'right_count': self.right_count, 'coef': round(coef, 2)}

        self.show_result_window()

    def show_result_window(self):
        # Функция для инициализации и показа окна результатов
        self.result_window = ResultWindow(self.user_info, self.result)
        self.result_window.show()
        self.close()

    def send_answer(self):
        # Функция для проверки введенного ответа и последующих действий
        if self.question['answer'] == self.input_answer:
            self.count_plus(True)
        else:
            self.count_plus()

        if self.stop_mode == 0:
            self.new_question()
        elif self.stop_mode == 1:
            if self.count == self.stop_count:
                self.stop()
            else:
                self.show_count()
                self.new_question()
        elif self.stop_mode == 2:
            if self.right_count == self.stop_count:
                self.stop()
            else:
                self.show_count()
                self.new_question()

    def count_plus(self, right=False):
        # Функция для увеличения количества ответов и,
        # при необходимости, количества верных ответов
        self.count += 1
        if right:
            self.right_count += 1

    def new_question(self):
        # Функция для создания и отображения примера
        self.input_answer = ''
        self.question = make_question(self.difficult)
        self.question_label.setText(self.question['question'])

    def keyPressEvent(self, event):
        # Функция для обработки нажатий кнопок
        if self.started:
            key_dict = {
                Qt.Key_0: '0',
                Qt.Key_1: '1',
                Qt.Key_2: '2',
                Qt.Key_3: '3',
                Qt.Key_4: '4',
                Qt.Key_5: '5',
                Qt.Key_6: '6',
                Qt.Key_7: '7',
                Qt.Key_8: '8',
                Qt.Key_9: '9',
            }
            if event.key() in key_dict.keys():
                # К введенному ответу добавляется символ
                self.input_answer += key_dict[event.key()]
            elif event.key() == Qt.Key_Backspace:
                # Удаляется последний символ введенного ответа
                self.input_answer = self.input_answer[:-1]
            elif event.key() in [Qt.Key_Enter - 1, Qt.Key_Enter]:
                # Ответ отправляется на проверку
                self.send_answer()
            elif event.key() == Qt.Key_Minus:
                # Введенный ответ заменяется на противоположный
                if self.input_answer:
                    if self.input_answer[0] == '-':
                        self.input_answer = self.input_answer[1:]
                    else:
                        self.input_answer = '-' + self.input_answer
                else:
                    self.input_answer = '-'
            # Введенный ответ выводится на экран
            self.show_input_answer()

    def closeEvent(self, event):
        # При закрытии окна переменная closed меняется на True
        self.closed = True

    def show_input_answer(self):
        # Функция для показа введенного пользователем ответа
        self.answer_label.setText(self.input_answer)

    @thread
    def show_time(self):
        # Функция для отображения оставшегося времени в виджете
        for i in range(self.stop_count + 1):
            if not self.closed:
                self.lcd.display(self.stop_count - i)
                time.sleep(1)
            else:
                break

    def show_count(self):
        # Функция для отображения оставшегося количества примеров в виджете
        if self.stop_mode == 1:
            self.lcd.display(self.stop_count - self.count)
        elif self.stop_mode == 2:
            self.lcd.display(self.stop_count - self.right_count)


class SettingsWindow(QMainWindow):
    # Класс окна настроек
    def __init__(self):
        super().__init__()
        uic.loadUi('UI/SettingsWindow.ui', self)

        # Загрузка настроек из базы данных
        self.settings = sql_settings_to_dict(
            SQL['cur'].execute('''SELECT * from Settings''').fetchall())

        # Показ загруженных настроек в окне
        index = self.countdown_duration_box.findText(
            str(self.settings['countdown_duration'])
        )
        self.countdown_duration_box.setCurrentIndex(index)

        self.show_count_box.setTristate(False)
        self.show_count_box.setCheckState(self.settings['show_count'])

        # Создание слота для нажатия кнопок
        self.ok_button.clicked.connect(self.save_settings)

    def save_settings(self):
        # Функция для сохранения настроек в базу данных

        settings = {
            'countdown_duration': int(
                self.countdown_duration_box.currentText()
            ),
            'show_count': self.show_count_box.checkState()
        }

        for i in settings.keys():
            SQL['cur'].execute('''UPDATE Settings
            SET value = ?
            WHERE name = ?''', (settings[i], i))
            SQL['con'].commit()

        self.close()


class ResultWindow(QMainWindow):
    # Класс окна отображения результатов решения примеров
    def __init__(self, user_info, result):
        super().__init__()
        uic.loadUi('UI/ResultWindow.ui', self)

        self.user_info = user_info

        self.ok_button.clicked.connect(self.show_main_window)

        # Окно заполняется информацией
        self.result_time.setText(str(result['time']))
        self.result_count.setText(str(result['count']))
        self.result_right_count.setText(str(result['right_count']))
        self.result_coef.setText(str(result['coef']))

    def closeEvent(self, event):
        # При закрытии окна открывается главное окно программы
        self.show_main_window()

    def show_main_window(self):
        # Функция для инициализации и показа главного окна программы
        self.main_window = MainWindow(self.user_info)
        self.main_window.show()
        self.close()


class StatisticWindow(QMainWindow):
    # Класс окна отображения статистики по уровням сложности
    def __init__(self, user_info):
        super().__init__()
        uic.loadUi('UI/StatisticWindow.ui', self)

        self.user_info = user_info

        self.ok_button.clicked.connect(self.close)
        self.difficult_box.currentIndexChanged.connect(self.update_table_widget)

        # Запускаем заполнение данных
        self.update_table_widget(0)

    def update_table_widget(self, index):
        # Функция для заполнения таблицы результатов и остальной
        # информации пользователя для определенного уровня
        # Запускается каждый раз при выборе уровня сложности
        # Принимает индекс выбранного уровня

        # Получаем данные из базы данных
        results = SQL['cur'].execute(
            '''SELECT * from Results 
            WHERE user_id = ? AND difficult = ?''',
            (self.user_info['id'], index)
        ).fetchall()

        # Очищаем таблицу
        self.results_table_widget.clear()
        self.results_table_widget.setRowCount(0)

        # Заполняем информацией
        if results:
            # При наличии результатов вычисляем средние значения
            total_task_count = sum(map(lambda s: s[-2], results))
            average_coef = round(
                sum(map(lambda s: s[-1], results)) / len(results), 4
            )
            average_time = round(1 / average_coef, 4)

            # Заполняем поля
            self.total_task_count_label.setText(
                'Всего решено примеров: ' + str(total_task_count)
            )
            self.average_coef_label.setText(
                'Средний коэфицент: ' + str(average_coef)
            )
            self.average_time_label.setText(
                'Среднее время на один пример: ' + str(average_time) + ' сек.'
            )

            # Готовим таблицу
            self.results_table_widget.setColumnCount(5)
            self.results_table_widget.setHorizontalHeaderLabels(
                ['Дата', 'Время', 'Ответов', 'Верных ответов', 'Коэфицент']
            )

            # Заполняем и равняем таблицу
            for i, lst in enumerate(results):
                self.results_table_widget.setRowCount(
                    self.results_table_widget.rowCount() + 1
                )
                self.results_table_widget.setItem(
                    i, 0, QTableWidgetItem(lst[2][:16])
                )
                self.results_table_widget.setItem(
                    i, 1, QTableWidgetItem(str(round(lst[4], 2)))
                )
                self.results_table_widget.setItem(
                    i, 2, QTableWidgetItem(str(lst[-3]))
                )
                self.results_table_widget.setItem(
                    i, 3, QTableWidgetItem(str(lst[-2]))
                )
                self.results_table_widget.setItem(
                    i, 4, QTableWidgetItem(str(round(lst[-1], 2)))
                )
            self.results_table_widget.resizeColumnsToContents()
        else:
            # При отсутствии данных очищаем окно
            self.results_table_widget.setColumnCount(0)
            self.total_task_count_label.setText('Всего решено примеров: 0')
            self.average_coef_label.setText('Средний коэфицент: 0')
            self.average_time_label.setText(
                'Среднее время на один пример: 0 сек.'
            )


if __name__ == '__main__':
    main()
