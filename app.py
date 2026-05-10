import os
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

HTML_PAGE = """
<!doctype html>
<html>
<head><title>MyFitBot - Cloud Storage</title></head>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
    <h1>Загрузка медиафайлов тренировок</h1>
    <p>Загрузите фото или музыку для вашего плейлиста</p>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file"><br><br>
        <input type="submit" value="Загрузить на сервер">
    </form>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return "Файл успешно сохранен!"
    return render_template_string(HTML_PAGE)

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
    user_id = req['session']['user_id']
    user = AliceUser.query.filter_by(user_id=user_id).first()
    if not user:
        user = AliceUser(user_id=user_id)
        db.session.add(user)
        db.session.commit()

    if req['session']['new']:
        res['response']['text'] = 'Привет в MyFitBot! Я запишу твой результат. Скажи, сколько ты пробежал?'
        return

    tokens = req['request']['nlu']['tokens']
    command = req['request']['command'].lower()

    if 'отчет' in command or 'статистика' in command:
        total = sum(w.distance for w in user.workouts)
        res['response']['text'] = f'Твой суммарный результат: {total} км. Продолжай в том же духе!'
        return

    if 'погода' in command:
        city = "Москва"
        for ent in req['request']['nlu']['entities']:
            if ent['type'] == 'YANDEX.GEO':
                city = ent['value'].get('city', 'Москва')
        res['response']['text'] = get_weather(city)
        return

    dist = None
    for ent in req['request']['nlu']['entities']:
        if ent['type'] == 'YANDEX.NUMBER':
            dist = float(ent['value'])
    
    if dist is not None:
        workout = Workout(user_id=user.id, distance=dist)
        db.session.add(workout)
        db.session.commit()
        res['response']['text'] = f'Записала: {dist} км. Ты молодец!'
    else:
        res['response']['text'] = 'Не поняла команду. Ты можешь сказать "Я пробежал 5 км", "Погода" или "Отчет".'

if __name__ == '__main__':
    app.run()
