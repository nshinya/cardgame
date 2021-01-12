#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit
import cardgame_core as cardgame

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__, static_folder="static", static_url_path="/")
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

DIST_NUM = 5
CARD_MAX = 11
CARD_MIN = 0
game_session = cardgame.Game(CARD_MAX, CARD_MIN)

# ユーザ情報
USERS = {
}

# cards
card_file = 'static/cards.png'

@app.route('/', methods=["GET"])
def index():
    return render_template('index.html', msg="")

def add_user(player_name):
    USERS[player_name] = len(USERS) + 1
    print(USERS)

def del_user(player_name):
    del USERS[player_name]
    print(USERS)

@app.route('/game', methods=["POST"])
def game():
    player_name = request.form["playerName"]
    # player_id = USERS[player_name]
    add_user(player_name)
    player_id = USERS[player_name]
    res = game_session.login(player_name, player_id)
    if res < 0:
        return render_template('index.html', msg="すでに他に2人ログインしています。ログアウトまでお待ちください。")
    else:
        return render_template('cardgame.html', async_mode=socketio.async_mode,
                            card_file=card_file,
                            player_id=player_id, player_name=player_name)


@socketio.on('game_start', namespace='/test')
def game_start(message):
    player_id = message["player_id"]
    if len(game_session.get_members()) == 2:
        result = game_session.start(DIST_NUM)
        emit("start_res", {"attacker": game_session.attacker.id_num, "defender": game_session.defender.id_num}, broadcast=True)
        emit("info_text", {"player_id": game_session.attacker.id_num, "text": "> あなたのターンです カードを引いてください"}, broadcast=True)
        emit("info_text", {"player_id": game_session.defender.id_num, "text": "> あいてのターンです"}, broadcast=True)


@socketio.on('get_cards', namespace='/test')
def get_cards(message):
    player_id = message["player_id"]
    for p in game_session.players:
        cardcolors, cardnums, cardstatus = game_session.get_cards(p.id_num, p.id_num == player_id)
        emit("get_cards_res", {"player_id": p.id_num, "cardcolors": cardcolors, "cardnums": cardnums, "status": cardstatus})
        print(cardcolors, cardnums, cardstatus)
    # ゲーム終了か確認
    if game_session.result >= 0:
        emit("won", {"player_id": game_session.result}, broadcast=True)
        emit("info_text", {"player_id": game_session.attacker.id_num, "text": "> ゲーム終了！"}, broadcast=True)
        emit("info_text", {"player_id": game_session.defender.id_num, "text": "> ゲーム終了！"}, broadcast=True)


@socketio.on('draw_card', namespace='/test')
def draw_card(message):
    player_id = message["player_id"]
    res = game_session.draw_card(player_id)
    if res is None:
        emit("won", {"player_id": game_session.attacker.id_num})
        game_session.result = True
    if res:
        dcard = game_session.get_drawn_card()
        emit("draw_card_res", {"result": True, "drawn_card_color": dcard.color, "drawn_card_num": dcard.number})
        emit("info_text", {"player_id": game_session.attacker.id_num, "text": "> 番号を当てるカードを選んでください"}, broadcast=True)
    else:
        emit("draw_card_res", {"result": False})


@socketio.on("select", namespace="/test")
def select(message):
    player_id = message["player_id"]
    select_index = int(message["index"])
    if player_id == game_session.attacker.id_num:
        if game_session.get_drawn_card() is None:
            emit("info_text", {"player_id": game_session.attacker.id_num, "text": "> 山札からカードを引いてください"}, broadcast=True)
            return
        selected_card = game_session.defender.get_card(select_index)
        if not selected_card.isopen:
            emit("select_cast", {"index": select_index, "attacker": game_session.attacker.id_num}, broadcast=True)
            emit("info_text", {"player_id": game_session.defender.id_num, "text": "> あいてがカードを選択中です"}, broadcast=True)


@socketio.on('attack', namespace='/test')
def attack(message):
    if message["skip"]:
        emit("info_text", {"player_id": game_session.attacker.id_num, "text": "> 攻撃スキップ ターンが代わり、あいてのターンです"}, broadcast=True)
        emit("info_text", {"player_id": game_session.defender.id_num, "text": "> 攻撃スキップ ターンが代わり、あなたのターンです カードを引いてください"}, broadcast=True)
        game_session.turn_end()
        emit("attack_res", {"attacker": game_session.attacker.id_num, "result": False}, broadcast=True)
        return

    player_id = message["player_id"]
    target_index = int(message["target_index"])
    card_number = int(message["card_number"])

    res = game_session.attack(player_id, target_index, card_number)
    if res is not None:
        if not res:
            # 攻撃失敗
            emit("info_text", {"player_id": game_session.attacker.id_num, "text": "> 攻撃失敗！ (宣言: " + str(card_number) + ") ターンが代わり、あいてのターンです"}, broadcast=True)
            emit("info_text", {"player_id": game_session.defender.id_num, "text": "> 攻撃失敗！ (宣言: " + str(card_number) + ") ターンが代わり、あなたのターンです カードを引いてください"}, broadcast=True)
            game_session.turn_end()
        else:
            # 攻撃成功
            emit("info_text", {"player_id": game_session.attacker.id_num, "text": "> 攻撃成功！ 続けて攻撃するか、終了ボタンでターンを終えます"}, broadcast=True)
            emit("info_text", {"player_id": game_session.defender.id_num, "text": "> 攻撃成功されました！"}, broadcast=True)
        emit("attack_res", {"attacker": game_session.attacker.id_num, "result": res}, broadcast=True)


@socketio.on('reset', namespace='/test')
def reset(message):
    game_session.reset(CARD_MIN, CARD_MAX)
    result = game_session.start(DIST_NUM)
    emit("start_res", {"attacker": game_session.attacker.id_num, "defender": game_session.defender.id_num}, broadcast=True)
    emit("info_text", {"player_id": game_session.attacker.id_num, "text": "> あなたのターンです カードを引いてください"}, broadcast=True)
    emit("info_text", {"player_id": game_session.defender.id_num, "text": "> あいてのターンです"}, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, "0.0.0.0", port=8080, debug=False)
