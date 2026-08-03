"""FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    chatting = State()        # foydalanuvchi chat rejimida
    feedback_rating = State() # baho kutayotgan
    feedback_comment = State()


class AdminStates(StatesGroup):
    pin = State()                # PIN kiritish
    menu = State()               # admin panel
    broadcast = State()          # broadcast xabari
    search_user = State()        # user qidirish
    reply_to = State()           # kimga javob yozish
    block_confirm = State()      # bloklash tasdiqi
    set_welcome = State()        # welcome matn
    set_autoreply = State()      # auto-reply matn
    ban_user = State()           # ban user
    warn_user = State()          # warn user
    export = State()             # export
