import os
import random
import logging
from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename
from config import Config
from models import db, AliceUser, Workout
from weather_service import get_weather

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

logging.basicConfig(level=logging.INFO)

with app.app_context():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.create_all()

MOTIVATION_LIST = [
    "Движение — это жизнь. Начните с малого сегодня!",
    "Ваше тело может всё, главное — убедить в этом мозг.",
    "Единственная плохая тренировка — та, которой не было.",
    "Дисциплина — это решение делать то, чего не хочется, чтобы достичь того, чего хочется.",
    "Успех начинается за чертой вашего комфорта.",
    "Каждая пробежка делает вас сильнее, чем вы были вчера."
]

HTML_DASHBOARD = """
<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MyFitBot | Панель управления</title>
    <style>
        :root { --primary: #4f46e5; --secondary: #10b981; --dark: #1f2937; --light: #f3f4f6; }
        body { font-family: 'Inter', system-ui, sans-serif; background: var(--light); color: var(--dark); margin: 0; padding: 40px; }
        .container { max-width: 1100px; margin: auto; }
        .card { background: white; border-radius: 20px; padding: 30px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 30px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 25px; }
        .stat-box { padding: 20px; border-radius: 15px; background: #fff; border: 1px solid #e5e7eb; text-align: center; }
        .stat-box h2 { margin: 0; color: var(--primary); font-size: 32px; }
        .stat-box p { margin: 5px 0 0; color: #6b7280; font-weight: 500; }
        table { width: 100%; border-collapse: collapse; margin-top: 25px; }
        th { text-align: left; padding: 15px; border-bottom: 2px solid #f3f4f6; color: #6b7280; text-transform: uppercase; font-size: 12px; }
        td { padding: 15px; border-bottom: 1px solid #f3f4f6; }
        .btn { background: var(--primary); color: white; border: none; padding: 12px 25px; border-radius: 10px; cursor: pointer; font-weight: 600; transition: 0.3s; }
        .btn:hover { opacity: 0.9; transform: translateY(-2px); }
        .level-badge { background: var(--secondary); color: white; padding: 5px 12px; border-radius: 50px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <header style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px;">
            <div>
                <h1 style="margin: 0; font-size: 36px;">MyFitBot <span style="color: var(--primary);">Pro</span></h1>
                <p style="color: #6b7280;">Аналитическая платформа вашего прогресса</p>
            </div>
            <div class="level-badge">Глобальная статистика</div>
        </header>

        <div class="grid">
            <div class="stat-box"><h2>{{ stats.users }}</h2><p>Пользователей</p></div>
            <div class="stat-box"><h2>{{ stats.km }}</h2><p>Км пройдено</p></div>
            <div class="stat-box"><h2>{{ stats.cal }}</h2><p>Ккал сожжено</p></div>
            <div class="stat-box"><h2>{{ stats.workouts }}</h2><p>Тренировок</p></div>
        </div>

        <div class="card">
            <h3>Последняя активность</h3>
            <table>
                <thead>
                    <tr><th>Дата</th><th>Дистанция</th><th>Время (мин)</th><th>Темп (мин/км)</th><th>Калории</th></tr>
                </thead>
                <tbody>
                    {% for w in recent %}
                    <tr>
                        <td>{{ w.timestamp.strftime('%d.%m.%Y %H:%M') }}</td>
                        <td>{{ w.distance }} км</td>
                        <td>{{ w.duration }}</td>
                        <td>{{ (w.duration / w.distance)|round(2) if w.distance > 0 else 0 }}</td>
                        <td>{{ w.calories }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="card" style="text-align: center;">
            <h3>Загрузка материалов</h3>
            <form method="post" enctype="multipart/form-data">
                <input type="file" name="file" style="margin-right: 15px;">
                <input type="submit" class="btn" value="Загрузить в облако">
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            fname = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    
    all_w = Workout.query.all()
    stats = {
        'users': AliceUser.query.count(),
        'km': round(sum(w.distance for w in all_w), 1),
        'cal': sum(w.calories for w in all_w),
        'workouts': len(all_w)
    }
    recent = Workout.query.order_by(Workout.timestamp.desc()).limit(15).all()
    return render_template_string(HTML_DASHBOARD, stats=stats, recent=recent)

@app.route('/post', methods=['POST'])
def main():
    req = request.json
    res = {
        'session': req['session'],
        'version': req['version'],
        'response': {'end_session': False}
    }
    handle_dialog(req, res)
    return jsonify(res)

def handle_dialog(req, res):
    uid = req['session']['user'].get('user_id') or req['session']['application']['application_id']
    user = AliceUser.query.filter_by(user_id=uid).first()
    
    if not user:
        user = AliceUser(user_id=uid)
        db.session.add(user)
        db.session.commit()

    res['response']['buttons'] = [
        {'title': 'Статистика', 'hide': True},
        {'title': 'Мой профиль', 'hide': True},
        {'title': 'Погода', 'hide': True},
        {'title': 'Помощь', 'hide': True}
    ]

    if req['session']['new']:
        tip = random.choice(MOTIVATION_LIST)
        res['response']['text'] = f'Привет! Я MyFitBot. Ваш уровень: {user.get_fitness_level()}. Совет дня: {tip}'
        return

    command = req['request']['command'].lower()

    if 'профиль' in command:
        bmi = user.calculate_bmi()
        cat = user.get_bmi_category()
        res['response']['text'] = (
            f"Ваш профиль:\n"
            f"Вес: {user.weight} кг, Рост: {user.height} см.\n"
            f"ИМТ: {bmi} ({cat}).\n"
            f"Уровень: {user.get_fitness_level()}.\n"
            f"Для изменения скажите 'мой вес 80' или 'мой рост 180'."
        )
        return

    if 'вес' in command:
        nums = [ent['value'] for ent in req['request']['nlu']['entities'] if ent['type'] == 'YANDEX.NUMBER']
        if nums:
            user.weight = float(nums[0])
            db.session.commit()
            res['response']['text'] = f"Вес обновлен: {user.weight} кг. Теперь расчеты точнее!"
        else:
            res['response']['text'] = f"Ваш вес: {user.weight} кг."
        return

    if 'рост' in command:
        nums = [ent['value'] for ent in req['request']['nlu']['entities'] if ent['type'] == 'YANDEX.NUMBER']
        if nums:
            user.height = int(nums[0])
            db.session.commit()
            res['response']['text'] = f"Рост обновлен: {user.height} см."
        return

    if 'статистика' in command or 'отчет' in command:
        an = user.get_analytics()
        if not an:
            res['response']['text'] = "У вас пока нет тренировок. Самое время начать!"
        else:
            forecast = round(1000 / an['avg_dist']) if an['avg_dist'] > 0 else 0
            res['response']['text'] = (
                f"Ваша аналитика:\n"
                f"Всего: {an['total_dist']} км за {an['count']} раз.\n"
                f"Рекорд: {an['max_dist']} км.\n"
                f"Средний темп: {an['avg_pace']} мин/км.\n"
                f"Прогноз: при таком темпе вы достигнете 1000 км через {forecast} дн."
            )
        return

    if 'погода' in command:
        city = "Москва"
        for ent in req['request']['nlu']['entities']:
            if ent['type'] == 'YANDEX.GEO':
                city = ent['value'].get('city', 'Москва')
        res['response']['text'] = get_weather(city)
        return

    if 'помощь' in command:
        res['response']['text'] = "Я умею: записывать пробежки (пробежал 5 км), хранить профиль (рост/вес), считать ИМТ, давать темп и аналитику. Просто скажите: 'запиши 7 км'."
        return

    entities = req['request']['nlu']['entities']
    nums = [e['value'] for e in entities if e['type'] == 'YANDEX.NUMBER']
    
    if nums:
        dist = float(nums[0])
        dur = int(dist * 6)
        cal = int(user.weight * dist * 0.75)
        
        workout = Workout(user_id=user.id, distance=dist, duration=dur, calories=cal)
        db.session.add(workout)
        db.session.commit()
        
        res['response']['text'] = f"Записала: {dist} км. Сожжено {cal} ккал. Средний темп: 6.0 мин/км. Так держать!"
    else:
        res['response']['text'] = "Не поняла команду. Попробуйте сказать 'пробежал 5 км' или спросите 'статистика'."

if __name__ == '__main__':
    app.run()
