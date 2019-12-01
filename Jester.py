import asyncio
import datetime
import logging
import os
import random
import time
import traceback
from datetime import datetime

import aiocron
import pymongo
from aiogram import Bot, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import exceptions
from aiogram.utils.exceptions import MessageToDeleteNotFound

API_TOKEN_JR = os.environ['token_jr']

logging.basicConfig(level=logging.WARNING)

loop = asyncio.get_event_loop()

client_jr = pymongo.MongoClient(os.environ['db_jr'])
db_jr = client_jr.test
collection2 = db_jr.bottle
col_private = db_jr.privates
jr = Bot(API_TOKEN_JR, loop=loop)
storage = MemoryStorage()
jp = Dispatcher(jr, storage=storage)
jester_user = 'jester_day_bot'
jester_id = loop.run_until_complete(jr.get_me())
jester_id = jester_id.id

developers = [879343317]
team = {'main_developer': {'dr_forse': 'George Forse'},
        'testers': [{'dr_forse': 'George Forse'}, {'P1von': 'ApelsinkaS'}, {'kelerne': 'Рин'},
                    {'P0LUNIN': 'polunin.ai'}, {'gbball': 'Брит'}],
        'ideas': {'guesses': {'kelerne': 'Рин'}}}

skyrim_frases = ['Дай-ка угадаю, кто-то украл твой сладкий рулет?',
                 ' Когда-то и меня вела дорога приключений... А потом мне прострелили колено.',
                 'Мой кузен борется с драконами, а мне что досталось? Караульная служба.',
                 'Поглядывай в небо и будь настороже!', 'В чем дело, каджит?', 'Это что, мех? У тебя из ушей торчит?',
                 'Если ты тут какой замок хоть пальцем ковырнешь — я тебе устрою кару божью.',
                 'Увижу твою руку у себя в кармане — отрублю!', 'Втяни свои когти, каджит.', ]


async def reset_game_command(m):
    try:
        collection2.update_one({'group': m.chat.id},
                               {'$set': {'status': '0'}})
        collection2.update_one({'group': m.chat.id},
                               {'$unset': {'mission_text': '$exists'}})
        collection2.update_one({'group': m.chat.id},
                               {'$unset': {'boyar': '$exists'}})
        collection2.update_one({'group': m.chat.id},
                               {'$unset': {'jester': '$exists'}})
        collection2.update_one({'group': m.chat.id},
                               {'$unset': {'mission_complete': '$exists'}})
    except:
        print(str(m.chat.id) + '\n' + traceback.format_exc())


@jp.message_handler(content_types=['left_chat_member'])
async def left_member(m):
    try:
        member = await jr.get_chat_member(m.chat.id, m.left_chat_member.id)
        doc = collection2.find_one({'group': m.chat.id})
        try:
            active_players = [doc['boyar'], doc['jester'], doc['king']]
            if member.user.id in doc['players'] and member.user.id not in active_players:
                collection2.update_one({'group': m.chat.id},
                                       {'$pull': {'players': m.from_user.id}})
                col_private.update_one({'user': m.from_user.id},
                                       {'$pull': {'groups': m.chat.id}})
            elif member.user.id in doc['players']:
                await reset_game_command(m)
                await jr.send_message(m.chat.id, 'Один из трех основных игроков покинул чат! Придется начать игру заново, нажмите /today_user')
        except (KeyError, TypeError):
            print(traceback.format_exc())
            if member.user.id in doc['players']:
                collection2.update_one({'group': m.chat.id},
                                       {'$pull': {'players': m.from_user.id}})
                col_private.update_one({'user': m.from_user.id},
                                       {'$pull': {'groups': m.chat.id}})
    except:
        print(traceback.format_exc())


class Form(StatesGroup):
    help_define1 = State()
    help_define = State()
    getting_mission = State()
    getting_feedback = State()
    mailing = State()


@jp.message_handler(lambda m: m.from_user.id in developers, commands=['mailing'])
async def mailing(message):
    try:
        await jr.send_message(message.from_user.id, 'Send the message to mail')
        await Form.mailing.set()
    except:
        print(traceback.format_exc())


@jp.message_handler(state=Form.mailing)
async def mail_handler(message, state: FSMContext):
    try:
        groups = collection2.find({'group': {'$exists': True}})
        users = col_private.find({'user': {'$exists': True}})
        for group in groups:
            chat_id = group['group']
            try:
                await jr.send_message(chat_id, 'Это автоматическая рассылка от разработчиков бота.\n'+message.text, parse_mode='markdown')
            except (exceptions.ChatNotFound, exceptions.Unauthorized, exceptions.BotKicked):
                continue
        for user in users:
            chat_id = user['user']
            try:
                await jr.send_message(chat_id, 'Это автоматическая рассылка от разработчиков бота.\n'+message.text, parse_mode='markdown')
            except (exceptions.CantInitiateConversation, exceptions.ChatNotFound, exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.CantTalkWithBots):
                continue
        await jr.send_message(message.chat.id, 'Finished.')
        await state.finish()
    except:
        print(traceback.format_exc())
        await state.finish()


@jp.message_handler(commands=['bot_team'])
async def bot_team(m):
    try:
        main_dev = team['main_developer']
        main_dev = '<a href="t.me/{}">{}</a>'.format(list(main_dev.keys())[0], main_dev[list(main_dev.keys())[0]])
        testers = team['testers']
        msg_text = f'<b>Автор идеи и главный (и единственный) разработчик</b>:\n{main_dev}\n<b>Бета-тестеры</b>:\n'
        for tester in testers:
            msg_text += '  ! <a href="t.me/{}">{}</a>\n'.format(list(tester.keys())[0], tester[list(tester.keys())[0]])
        await jr.send_message(chat_id=m.chat.id,
                              text=msg_text,
                              reply_to_message_id=m.message_id,
                              parse_mode='html',
                              disable_web_page_preview=True)
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['feedback'])
async def feedback(m: types.Message, state: FSMContext):
    try:
        if len(m.text.split()) > 1:
            await jr.forward_message(developers[0], m.chat.id, m.message_id)
            await jr.send_message(m.chat.id, 'Я передам Ваши слова богу', reply_to_message_id=m.message_id)
        else:
            await jr.send_message(m.chat.id, 'Говорите, что у Вас на уме',
                                  reply_to_message_id=m.message_id,reply_markup=types.ForceReply(selective=True))
            async with state.proxy() as data:
                data['feedback_sender_jr'] = m.from_user.id
            await Form.getting_feedback.set()
    except:
        print(traceback.format_exc())


@jp.message_handler(state=Form.getting_feedback)
async def feedback_handler(m, state: FSMContext):
    async with state.proxy() as data:
        feedback_sender_jr = data['feedback_sender_jr']
    if m.from_user.id == feedback_sender_jr and m.reply_to_message and m.reply_to_message.text == 'Говорите, что у Вас на уме' and (
            time.time() - (m.reply_to_message.date - datetime(1970, 1, 1)).total_seconds()) < 300:
        await jr.forward_message(developers[0], m.chat.id, m.message_id)
        await jr.send_message(m.chat.id, 'Я передам Ваши слова богу', reply_to_message_id=m.message_id)
        await state.finish()
    elif m.text.startswith('/') and jester_user in m.text:
        await state.finish()
    elif m.text.startswith('/') and m.chat.type == 'private':
        await state.finish()


@jp.message_handler(commands=['help_define'])
async def help_define(message):
    if message.from_user.id in developers:
        global help_definer
        help_definer = message.from_user.id
        await jr.send_message(message.from_user.id, 'Define the help-message')
        await Form.help_define.set()
    else:
        await jr.send_message(message.chat.id, 'Эта команда - только для разработчиков бота!')


@jp.message_handler(state=Form.help_define)
async def help_message_handler(message, state: FSMContext):
    global help_definer
    if message.chat.id == help_definer:
        collection2.update_one({'id': 0},
                               {'$set': {'help_msg': message.text}},
                               upsert=True)
        await jr.send_message(message.chat.id, 'Updated.')
        await state.finish()


@jp.message_handler(commands=['help'])
async def show_help(message):
    doc = collection2.find_one({'id': 0})
    help_msg = doc['help_msg']
    if message.chat.type != 'private' and message.text.startswith(f'/help@{jester_user}'):
        await jr.send_message(message.chat.id, help_msg, parse_mode='markdown')
    elif message.chat.type == 'private':
        await jr.send_message(message.chat.id, help_msg, parse_mode='markdown')


@jp.message_handler(commands=['players'])
async def players_list(m):
    try:
        if collection2.find_one({'group': m.chat.id}) is None:
            return
        players = ''
        for gamer in collection2.find_one({'group': m.chat.id})['players']:
            if not gamer:
                continue
            try:
                player = await jr.get_chat_member(m.chat.id, gamer)
                player = player.user.first_name
                players += str(player) + ', '
            except exceptions.InvalidUserId:
                collection2.update_one({'group': m.chat.id},
                                       {'$pull': {'players': gamer}})
        x = len(players) - 2
        players = players[:x]
        await jr.send_message(m.chat.id, players, reply_to_message_id=m.message_id)
    except exceptions.MessageTextIsEmpty:
        await jr.send_message(m.chat.id, "Пока никто не играет, нажмите /reg_me для регистрации.")
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['leave_jester'])
async def leave_game(m):
    try:
        member = await jr.get_chat_member(m.chat.id, m.from_user.id)
        doc = collection2.find_one({'group': m.chat.id})
        if doc is not None:
            try:
                active_players = [doc['boyar'], doc['jester'], doc['king']]
                if member.user.id in doc['players'] and member.user.id not in active_players:
                    collection2.update_one({'group': m.chat.id},
                                           {'$pull': {'players': m.from_user.id}})
                    col_private.update_one({'user': m.from_user.id},
                                           {'$pull': {'groups': m.chat.id}})
                elif member.user.id in doc['players']:
                    await jr.send_message(m.chat.id, 'Вы - один из основных участников сегодняшней игры, Вы не можете покинуть игру до окончания сегодняшней игры.')
            except (KeyError, TypeError):
                if member.user.id in doc['players']:
                    collection2.update_one({'group': m.chat.id},
                                           {'$pull': {'players': m.from_user.id}})
                    col_private.update_one({'user': m.from_user.id},
                                           {'$pull': {'groups': m.chat.id}})
        else:
            await jr.send_message(m.chat.id, 'Вы и так не играете.')
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['kick'])
async def kick_user(m):
    try:
        kicked_member = await jr.get_chat_member(m.chat.id, m.reply_to_message.from_user.id)
        member_kicker = await jr.get_chat_member(m.chat.id, m.from_user.id)
        if m.chat.type != 'private':
            if member_kicker.user.id in developers or member_kicker.status == 'creator' or member_kicker.can_change_info and member_kicker.can_delete_messages and member_kicker.can_invite_users and member_kicker.can_restrict_members and member_kicker.can_pin_messages and member_kicker.can_promote_members:
                if not kicked_member.can_promote_members and not kicked_member.can_pin_messages and not kicked_member.can_change_info and not kicked_member.can_restrict_members and not kicked_member.can_invite_users and not kicked_member.can_delete_messages and kicked_member.status != 'creator' and kicked_member.user.id not in developers:
                    if kicked_member in collection2.find_one({'group': m.chat.id})['players'] or m.chat.id in col_private.find_one({'user': m.reply_to_message.from_user.id})['groups']:
                        collection2.update_one({'group': m.chat.id},
                                               {'$pull': {'players': m.reply_to_message.from_user.id}})
                        col_private.update_one({'user': m.reply_to_message.from_user.id},
                                               {'$pull': {'groups': m.chat.id}})
                        await jr.send_message(m.chat.id, kicked_member.user.first_name+" был выкинут нахрен из игры")
                    else:
                        await jr.send_message(m.chat.id, kicked_member.user.first_name+" в общем то и не был в игре")
                else:
                    await jr.send_message(m.chat.id, 'Вы не можете его удалить из игры.\n P.s. <i>если вы создатель, а он всего лишь фулладмин, то звиняйте, разрабу лень было норм делать чет, заберите на пару секунд одно из прав прост</i>', parse_mode='html')
            else:
                await jr.send_message(m.chat.id, "Это подвластно только создателю и его приближенным, фулл-админам")
        else:
                await jr.send_message(m.chat.id, 'Эта команда - для групп.')
    except KeyError:
        pass
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['reset_game'])
async def reset_game_by_command(m):
    try:
        if m.from_user.id in developers:
            await reset_game_command(m)
            await jr.send_message(m.chat.id, 'Game reseted')
        else:
            await jr.send_message(m.chat.id, 'Эта команда - только для разработчиков бота')
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['reg_me'])
async def reg_user(message):
    try:
        if message.chat.type != 'private':
            doc = collection2.find_one({'group': message.chat.id})
            reg_kb = types.InlineKeyboardMarkup()
            reg = types.InlineKeyboardButton('Тык', url='telegram.me/{}?start=reg{}'.format(jester_user, message.chat.id))
            reg_kb.add(reg)
            if collection2.find_one({'group': message.chat.id}) is None:
                collection2.insert_one({'group': message.chat.id,
                                        'players': [],
                                        'status': '0'})
                await jr.send_message(message.chat.id, 'Нажмите для регистрации!', reply_to_message_id=message.message_id,
                                      reply_markup=reg_kb)
            elif message.from_user.id not in doc['players']:
                await jr.send_message(message.chat.id, 'Нажмите для регистрации!', reply_to_message_id=message.message_id,
                                      reply_markup=reg_kb)
            else:
                await jr.send_message(message.chat.id, 'Вы уже в игре!', reply_to_message_id=message.message_id)
        else:
            await jr.send_message(message.chat.id, 'Нихуя, дыра закрылась, пошел в группу, эта команда для привата!')
    except:
        await jr.send_message(message.chat.id, traceback.format_exc())


@jp.message_handler(commands=['finish_it'])
async def finish_game(m):
    try:
        doc = collection2.find_one({'group': m.chat.id})
        if doc is None:
            collection2.insert_one({'group': m.chat.id,
                                    'players': [],
                                    'status': '0'})
            await jr.send_message(m.chat.id,
                                  'Игра еще не начата, или уже закончена, или задание еще не выполнено (назначено)')
        if m.chat.type == 'private':
            await jr.send_message(m.chat.id, 'Так Вас никто не услышит!')
        elif m.from_user.id not in developers and m.from_user.id != doc['king'] and doc['king']:
            await jr.send_message(m.chat.id, 'Вы - не король!')
        elif doc['status'] == '2':
            if m.from_user.id  == doc['king'] or m.from_user.id in developers:
                if len(m.text.split()) < 2:
                    await jr.send_message(m.chat.id, 'Скажите, как Вам понривалось шоу после команды, Ваше Величество',
                                          reply_to_message_id=m.message_id)
                else:
                    list = m.text.split()
                    result = ''
                    for i in range(len(list) - 1):
                        result += list[i + 1] + ' '
                    await jr.send_message(m.chat.id, 'Мнение Его Величества:\n' + result)
                    collection2.update_one({'group': m.chat.id},
                                           {'$set': {'status': '3'}})
                    await jr.send_message(m.chat.id, "Задание было таким:\n" + doc['mission_text'])
                    await show_mission_complete(m)
                    await reset_game()
        else:

            await jr.send_message(m.chat.id,
                                  'Игра еще не начата, или уже закончена, или задание еще не выполнено (назначено)')
    except KeyError:
        await jr.send_message(m.chat.id, 'game not started yet')
        print(traceback.format_exc())
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['today_user'])
async def get_users(message):
    global x
    global message_chat_id
    message_chat_id = message.chat.id
    try:
        x = 0
        doc = collection2.find_one({'group': message.chat.id})
        if doc is None:
            collection2.insert_one({'group': message.chat.id,
                                    'players': [],
                                    'status': '0'})
            doc = collection2.find_one({'group': message.chat.id})
        list_users = doc['players']
        if len(doc['players']) < 3:
            await jr.send_message(message.chat.id, 'Not enough players, 3 needed.')
        elif doc['status'] == '0':
            if len(message.text.split()) > 1 and message.from_user.id in developers:
                boyar = int(message.text.split()[1])
                jester = int(message.text.split()[2])
                king = int(message.text.split()[3])
            else:
                boyar = random.choice(list_users)
                jester = random.choice(list_users)
                king = random.choice(list_users)
                while boyar == jester:
                    jester = random.choice(list_users)
                while king == boyar or king == jester:
                    king = random.choice(list_users)
            try:
                member = await jr.get_chat_member(message.chat.id, boyar)
            except exceptions.InvalidUserId:
                collection2.update_one({'group': message.chat.id},
                                       {'$pull': {'players': boyar}})
                await get_users(message)
            boyar_name = member.user.first_name
            try:
                member = await jr.get_chat_member(message.chat.id, jester)
            except exceptions.InvalidUserId:
                collection2.update_one({'group': message.chat.id},
                                       {'$pull': {'players': jester}})
                await get_users(message)
            jester_name = member.user.first_name
            to_mission = types.InlineKeyboardMarkup()
            butt = types.InlineKeyboardButton('{}, придумывай задание и жми сюда'.format(boyar_name),
                                              url='https://telegram.me/{}?start={}'.format(jester_user,
                                                                                           message.chat.id))
            to_mission.add(butt)
            await jr.send_message(message.chat.id, 'Loading...')
            await jr.send_message(message.chat.id,
                                  '<a href="tg://user?id={}">{}</a>, {}'.format(boyar, boyar_name,
                                                                                'Вы грустите на пиру, король, обратив на Вас свое внимание, предлагает Вам придумать смешное задание для его шута, нравится вам это или нет - ничего не поделаешь, придется заняться, иначе кого-нибудь казнят, даже если не вас, ответственность нести за это Вам точно не хочется!'),
                                  parse_mode='html', reply_markup=to_mission)
            collection2.update_one({'group': message.chat.id},
                                   {'$set': {'status': '1'}})
            collection2.update_one({'group': message.chat.id},
                                   {'$set': {'boyar': boyar}})
            collection2.update_one({'group': message.chat.id},
                                   {'$set': {'jester': jester}})
            collection2.update_one({'group': message.chat.id},
                                   {'$set': {'king': king}})
            try:
                if message.chat.username is not None:
                    await jr.send_message(king,
                                          'Вы - король в мире ' + '@' + message.chat.username + '! Вы будете решать, понравилось ли Вам то, как шут выполнил задание! (От этого ничего не зависит, кроме перехода игры в статус "Закончена"')
                else:
                    for_link_chat_id = str(message.chat.id).replace('-100', '')
                    await jr.send_message(king, 'Вы - король в мире ' + '[{}](t.me/c/{})'.format(message.chat.title,
                                                                                                 for_link_chat_id) + '! Вы будете решать, понравилось ли Вам то, как шут выполнил задание! (От этого ничего не зависит, кроме перехода игры в статус "Закончена")',
                                          parse_mode='markdown')
            except (exceptions.CantInitiateConversation, exceptions.BotBlocked):
                try:
                    collection2.update_one({'group': message.chat.id},
                                           {'$inc': {f'{king} to_kick': 1}})
                except KeyError:
                    collection2.update_one({'group': message.chat.id},
                                           {'$set': {f'{king} to_kick': 1}})
                if collection2.find_one({'group': message.chat.id})[f'{king} to_kick'] < 3:
                    await jr.send_message(message.chat.id, f'<a href="tg://user?id={king}">Король</a>, напишите, пожалуйста боту в лс.\nВы будете решать, понравилось ли Вам то, как шут выполнил задание! (От этого ничего не зависит, кроме перехода игры в статус "Закончена"\n<b>Предупреждение! У каждого игрока есть возможность лишь два раза проигнорировать просьбу о написании в лс, после вы будете кикнуты из игры.</b>', parse_mode='html')
                else:
                    await reset_game_command(message)
                    collection2.update_one({'group': message.chat.id},
                                           {'$set': {'status': '0'}})
                    collection2.update_one({'group': message.chat.id},
                                           {'$set': {'voted_users': []}})
                    collection2.update_one({'group': message.chat.id},
                                           {'$set': {'guesses': []}})
                    collection2.update_one({'group': message.chat.id},
                                           {'$pull': {'players': king}})
                    col_private.update_one({'user': king},
                                           {'$pull': {'groups': message.chat.id}})
                    try:
                        king = await jr.get_chat_member(message.chat.id, king)
                        king = king.user.first_name
                    except exceptions.InvalidUserId:
                        pass
                    await jr.send_message(message.chat.id, f'Король не пишет мне в лс! Игра была сброшена, {king} был удален из игры')
            except exceptions.UserDeactivated:
                await reset_game_command(message)
                collection2.update_one({'group': message.chat.id},
                                       {'$set': {'status': '0'}})
                collection2.update_one({'group': message.chat.id},
                                       {'$set': {'voted_users': []}})
                collection2.update_one({'group': message.chat.id},
                                       {'$pull': {'players': king}})
                col_private.update_one({'user': king},
                                       {'$pull': {'groups': message.chat.id}})
                await jr.send_message(message.chat.id, 'Король мертв. Игра сброшена в начальную стадию. \n/today_user')
        elif doc['status'] == '1':
            boyar = doc['boyar']
            try:
                boyar_name = await jr.get_chat_member(message.chat.id, boyar)
                boyar_name = boyar_name.user.first_name
            except exceptions.InvalidUserId:
                pass
            kb = types.InlineKeyboardMarkup()
            butt = types.InlineKeyboardButton('{}, придумывай задание и жми сюда'.format(boyar_name),
                                              url='https://telegram.me/{}?start={}'.format(jester_user,
                                                                                           message.chat.id))
            kb.add(butt)
            await jr.send_message(message.chat.id,
                                  '<a href="tg://user?id={}">{}</a>, придумывает задание для шута...'.format(
                                      boyar, boyar_name), parse_mode='html', reply_markup=kb)
        elif doc['status'] == '2':
            jester = doc['jester']
            try:
                jester_name = await jr.get_chat_member(message.chat.id, jester)
                jester_name = jester_name.user.first_name
            except exceptions.InvalidUserId:
                pass
            jester_mission_kb = types.InlineKeyboardMarkup()
            butt = types.InlineKeyboardButton('Задание для шута', callback_data='mission')
            jester_mission_kb.add(butt)
            await jr.send_message(message.chat.id,
                                  '<a href="tg://user?id={}">{}</a>, придворный шут, выполняет задание...'.format(
                                      jester, jester_name), parse_mode='html', reply_markup=jester_mission_kb)
        elif doc['status'] == '3':
            await jr.send_message(message.chat.id, 'Сегодняшняя игра уже закончена!')
    except:
        print(traceback.format_exc())


async def status_check(m, doc, boyar, chat_id):
    if doc['status'] == '1':
        if m.from_user.id == boyar:
            await jr.send_message(m.chat.id, 'Отправь задание ответом на ЭТО сообщение',
                                  reply_to_message_id=m.message_id, reply_markup=types.ForceReply())
            col_private.update_one({'user': m.chat.id},
                                   {'$set': {'main_chat': chat_id}})
            await Form.getting_mission.set()
        else:
            await jr.send_message(m.chat.id,
                                  'ЭТА КОПКА НЕ ДЛЯ ТЕБЯ, АЛЕ! Неужели, игра такая сложная, что у тебя мозги превратились в кашу? Может, тебе новые подарить?')
    elif doc['status'] == '0':
        await jr.send_message(m.chat.id, 'Игра еще не началась, начни ее командой /today_user в группе')
    elif doc['status'] == '2':
        await jr.send_message(m.chat.id,
                              'Задание уже выбрано, перевыбрать не получится, потому что разраб - пидор, все претензии к [нему](t.me/dr_forse), я всего лишь бот.',
                              parse_mode='markdown')
    elif doc['status'] == '3':
        await jr.send_message(m.chat.id,
                              'Дневной розыгрыш уже окончен, возвращайся завтра или зайди на гитхаб(в описании), возьми код, сделай розыгрыш постоянным и захости у себя, если, конечно не ужаснешься тому, какой это говнокод.')


@jp.message_handler(lambda m: m.chat.type == 'private', commands=['start'])
async def start_command(m):
    try:
        if len(m.text.split()) == 2 and m.text.split()[1].startswith('-') and m.text.split('/start -')[1].isdigit():
            chat_id = int(m.text.split()[1])
            try:
                doc = collection2.find_one({'group': chat_id})
                if m.from_user.id not in doc['players']:
                    group = await jr.get_chat(chat_id)
                    if group.username is not None:
                        await jr.send_message(m.chat.id, 'Вы не в игре, вернитесь в группу <a href=t.me/{}>{}</a> и зарегистрируйтесь(/reg\_me)'.format(group.username, group.title), parse_mode='html')
                    else:
                        for_link_chat_id = str(chat_id).replace('-100', '')
                        await jr.send_message(m.chat.id, 'Вы не в игре, вернитесь в группу <a href=t.me/c/{}>{}</a> и зарегистрируйтесь(/reg\_me)'.format(for_link_chat_id, group.title), parse_mode='html')
                else:
                    boyar = doc['boyar']
                    col_private.update_one({'user': m.chat.id},
                                           {'$set': {'main_chat': chat_id}},
                                           upsert=True)
                    await status_check(m, doc, boyar, chat_id)
            except KeyError:
                group = await jr.get_chat(chat_id)
                if group.username is not None:
                    await jr.send_message(m.chat.id,
                                          'Вы не в игре, вернитесь в группу <a href=t.me/{}>{}</a> и зарегистрируйтесь(/reg\_me)'.format(group.username, group.title),
                                          parse_mode='html')
                else:
                    for_link_chat_id = str(chat_id).replace('-100', '')
                    await jr.send_message(m.chat.id,
                                          'Вы не в игре, вернитесь в группу <a href=t.me/c/{}>{}</a> и зарегистрируйтесь(/reg\_me)'.format(for_link_chat_id, group.title),
                                          parse_mode='html')
        elif len(m.text.split()) == 2 and m.text.split()[1].startswith('reg'):
            chat_id = int(m.text.split('/start reg')[1])
            if m.from_user.id not in collection2.find_one({'group': chat_id})['players']:
                collection2.update_one({'group': chat_id},
                                       {'$push': {'players': m.from_user.id}})
            if col_private.find_one({'user': m.chat.id}) is None:
                col_private.insert_one({'user': m.from_user.id,
                                        'groups': [chat_id]})
            elif col_private.find_one({'user': m.chat.id}) is not None:
                doc = col_private.find_one({'user': m.chat.id})
                if chat_id not in doc['groups']:
                    col_private.update_one({'user': m.from_user.id},
                                           {'$push': {'groups': chat_id}})
            await jr.send_message(m.chat.id, 'Вы зарегистрированы!')
            await jr.send_message(chat_id, f'{m.from_user.first_name} зарегистрировался.')
        else:
            await jr.send_message(m.chat.id, 'Привет. Я игровой бот(ежедневные конкурсы). \nБольше в /help\nСаппорт-группа: @jestersupport (За вопросы, ответы на которые есть в хелпе - бан!)')
    except:
        print(str(m.chat.id) + '\n' + traceback.format_exc())


@jp.message_handler(state=Form.getting_mission)
async def getting_mission(m, state: FSMContext):
    try:
        chat_id = col_private.find_one({'user': m.chat.id})['main_chat']
        doc = collection2.find_one({'group': chat_id})
        boyar = doc['boyar']
        king = doc['king']
        jester = doc['jester']
        col_private.update_one({'user': m.chat.id},
                               {'$set': {'mission': m.text}},
                               upsert=True)
        check_kb = types.InlineKeyboardMarkup()
        accept = types.InlineKeyboardButton('Да', callback_data='accept')
        decline = types.InlineKeyboardButton('Нет',
                                             url=f'https://telegram.me/{jester_user}?start={chat_id}')
        check_kb.add(accept, decline)
        if m.reply_to_message is not None:
            if m.reply_to_message.text == 'Отправь задание ответом на ЭТО сообщение' and (
                    time.time() - (m.reply_to_message.date - datetime(1970, 1, 1)).total_seconds()) < 21600:
                await jr.send_message(m.chat.id, 'Вы уверены?', reply_markup=check_kb)
                await state.finish()
            elif m.reply_to_message.text == 'Отправь задание ответом на ЭТО сообщение':
                await jr.send_message(m.chat.id, 'Это сообщение устарело. Вернитесь в чат и нажмите на кнопку заново.')
                await jr.delete_message(m.chat.id, m.reply_to_message.id)
                await state.finish()
        else:
            await jr.send_message(m.chat.id, 'Отправь задание ответом на ЭТО сообщение',
                                  reply_to_message_id=m.message_id, reply_markup=types.ForceReply())
    except:
        print(str(m.chat.id) + '\n' + traceback.format_exc())
        await state.finish()


@jp.callback_query_handler(lambda call: call.data == 'accept')
async def checking(call):
    try:
        tdoc = col_private.find_one({'user': call.message.chat.id})
        main_chat = tdoc['main_chat']
        doc = collection2.find_one({'group': main_chat})
        boyar = doc['boyar']
        king = doc['king']
        jester = doc['jester']
        if call.data == 'accept':
            member = await jr.get_chat(main_chat)
            if member.username != None:
                to_chat = await jr.get_chat(main_chat)
                await jr.send_message(call.message.chat.id,
                                      'Хорошо. Задание в группе [{}](t.me/{}) оглашено.'.format(to_chat.title,
                                                                                                to_chat.username),
                                      parse_mode='markdown')
            else:
                to_chat = await jr.get_chat(main_chat)
                for_link_chat_id = str(main_chat).replace('-100', '')
                await jr.send_message(call.message.chat.id,
                                      'Хорошо. Задание в группе [{}](t.me/c/{}) оглашено.'.format(to_chat.title,
                                                                                                  for_link_chat_id),
                                      parse_mode='markdown')
            collection2.update_one({'group': main_chat},
                                   {'$set': {'mission_text': tdoc['mission']}})
            collection2.update_one({'group': main_chat},
                                   {'$set': {'status': '2'}})
            jester_mission_kb = types.InlineKeyboardMarkup()
            butt = types.InlineKeyboardButton('Задание для шута', callback_data='mission')
            jester_mission_kb.add(butt)
            await jr.send_message(main_chat,
                                  'Всем внимание на <a href = "tg://user?id={}">Шута Дня</a>'.format(jester),
                                  parse_mode='html', reply_markup=jester_mission_kb)
        await jr.answer_callback_query(call.id)
        await jr.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    except:
        print(traceback.format_exc())


@jp.callback_query_handler(lambda call: call.data == 'mission')
async def jester_mission(call):
    try:
        call.data
        doc = collection2.find_one({'group': call.message.chat.id})
        boyar = doc['boyar']
        king = doc['king']
        jester = doc['jester']
        if call.from_user.id == boyar or call.from_user.id == jester or call.from_user.id == king:
            try:
                await jr.answer_callback_query(callback_query_id=call.id, text=doc['mission_text'], show_alert=True)
            except exceptions.BadRequest:
                await jr.send_message(chat_id=call.from_user.id, text=doc['mission_text'])
                await jr.answer_callback_query(callback_query_id=call.id,
                                               text='Слишком длинный текст. Отправил в лс.',
                                               show_alert=True)
        else:
            await jr.answer_callback_query(callback_query_id=call.id, text='Вы не можете прочитать это',
                                           show_alert=False)
    except:
        print(traceback.format_exc())


async def reset_game():
    collection2.update_many({'group': {'$exists': True}},
                            {'$unset': {'boyar': '$exists'}})
    collection2.update_many({'group': {'$exists': True}},
                            {'$unset': {'jester': '$exists'}})
    collection2.update_many({'group': {'$exists': True}},
                            {'$unset': {'king': '$exists'}})
    collection2.update_many({'group': {'$exists': True}},
                            {'$unset': {'mission_text': '$exists'}})
    collection2.update_many({'group': {'$exists': True}},
                            {'$unset': {'mission_complete': '$exists'}})
    collection2.update_many({'group': {'$exists': True}},
                            {'$set': {'status': '0'}})


@aiocron.crontab('0 0 * * *')
async def reset_game_aiocron():
    try:
        for doc in collection2.find({'group': {'$exists': True}}):
            try:
                if doc['status'] == '2':
                    try:
                        await jr.send_message(doc['group'],
                                              '<a href = "tg://user?id={}">Король</a> не удостоил шоу своим вниманием, меж тем задание было таким:\n{}'.format(doc['king'], doc['mission_text']),
                                              parse_mode='html')
                    except (exceptions.ChatNotFound, exceptions.BotKicked, exceptions.Unauthorized):
                        continue
                elif doc['status'] == '1':
                    try:
                        await jr.send_message(doc['group'],
                                              '<a href = "tg://user?id={}">Боярин</a> не выполнил приказ короля, не сносить ему головы!'.format(doc['boyar']),
                                              parse_mode='html')
                    except (exceptions.ChatNotFound, exceptions.BotKicked, exceptions.Unauthorized):
                        continue
            except(exceptions.ChatNotFound, exceptions.BotKicked, exceptions.Unauthorized):
                continue
        await reset_game()
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['lastdone'])
async def check_last_done(m):
    try:
        doc = collection2.find_one({'group': m.chat.id})
        if 'mission_complete' in doc:
            await jr.forward_message(chat_id=m.chat.id, from_chat_id=m.chat.id, message_id=doc['mission_complete'])
        else:
            await jr.send_message(m.chat.id, random.choice(skyrim_frases))
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['done'])
async def save_mission_message_by_command(m):
    try:
        doc = collection2.find_one({'group': m.chat.id})
        if doc['status'] == '2':
            from_member = await jr.get_chat_member(m.chat.id, m.from_user.id)
            if m.from_user.id == doc['jester'] or m.from_user.id in developers or from_member.status == 'creator' or from_member.status == 'administrator':
                collection2.update_one({'group': m.chat.id},
                                       {'$set': {'mission_complete': m.reply_to_message.message_id}})
                await jr.send_message(m.chat.id, 'okay, fine')
            else:
                await jr.send_message(m.chat.id, 'Это могут сделать только шут, разраб, создатель и админы чата.')
        else:
            await jr.send_message(m.chat.id, random.choice(skyrim_frases))
    except:
        print(traceback.format_exc())


@jp.message_handler(lambda m: m.reply_to_message and m.reply_to_message.from_user.id == jester_id, content_types=['text', 'photo', 'video', 'sticker', 'animation', 'audio', 'document', 'voice', 'video_note', 'contact, location', 'venue', 'poll'])
async def save_mission_message_AI(m):
    try:
        doc = collection2.find_one({'group': m.chat.id})
        if doc is not None and doc['status'] == '2':
            if ' придумывает задание для шута' in m.reply_to_message.text or 'Всем внимание на Шута Дня' in m.reply_to_message.text:
                if m.reply_to_message.from_user.id == jester_id and time.time() - time.mktime(
                        m.reply_to_message.date.timetuple()) < 43200 \
                        and m.from_user.id == doc['jester']:
                    collection2.update_one({'group': m.chat.id},
                                           {'$set': {'mission_complete': m.message_id}})
    except:
        print(traceback.format_exc())


async def show_mission_complete(m):
    doc = collection2.find_one({'group': m.chat.id})
    if 'mission_complete' in doc:
        await jr.send_message(m.chat.id, 'Выполнение задания:')
        await jr.forward_message(chat_id=m.chat.id, from_chat_id=m.chat.id, message_id=doc['mission_complete'])


@jp.message_handler(commands=['top'])
async def show_top(m):
    try:
        users_top = ''
        groups_top = ''
        users = col_private.find({'user': {'$exists': True}}).sort('stats', pymongo.DESCENDING)
        groups = collection2.find({'group': {'$exists': True}}).sort('stats', pymongo.DESCENDING)
        group_ind = 1
        user_ind = 1
        count_users = col_private.count_documents({'user': {'$exists': True}})
        count_groups = collection2.count_documents({'group': {'$exists': True}})
        for group in groups:
            grp_stats = group['stats']
            if group_ind < 11:
                try:
                    chat = await jr.get_chat(group['group'])
                    chat = chat.title
                    groups_top += f'{group_ind}. *{chat}*: {grp_stats}\n'
                except(exceptions.BotKicked, exceptions.ChatNotFound, exceptions.Unauthorized):
                    print(traceback.format_exc())
                    chat_id = group['group']
                    groups_top += f'{group_ind}. *{chat_id}*: {grp_stats}\n'
                group_ind += 1
            else:
                break
        for user in users:
            if user_ind < 11:
                if m.chat.id in user['groups']:
                    user_stats = user['stats']
                    try:
                        member = await jr.get_chat_member(m.chat.id, user['user'])
                        member = member.user.first_name
                        users_top += f'{user_ind}. *{member}*: {user_stats}\n'
                    except(exceptions.BotKicked, exceptions.ChatNotFound, exceptions.Unauthorized):
                        try:
                            member = await jr.get_chat(user['user'])
                            member = member.first_name
                            users_top += f'{user_ind}. *{member}*: {user_stats}\n'
                        except(exceptions.BotBlocked, exceptions.Unauthorized, exceptions.UserDeactivated,
                               exceptions.InvalidUserId, exceptions.ChatNotFound):
                            print(traceback.format_exc())
                            user_id = user['user']
                            users_top += f'{user_ind}. *{user_id}*: {user_stats}\n'
                    user_ind += 1
            else:
                break
        if len(m.text.split()) >= 2:
            command_args = ['-U', '-G']
            args = m.text.split()[1:3]
            for arg in args:
                if arg in command_args:
                    if arg == '-U':
                        await jr.send_message(m.chat.id, f'*Топ-10 участников чата*:\n {users_top}\nВсего юзеров в боте: {count_users}',
                                              reply_to_message_id=m.message_id, parse_mode='markdown')
                    elif arg == '-G':
                        await jr.send_message(m.chat.id, f'*Топ-10 групп*:\n {groups_top}\n Всего групп с ботом: {count_groups}',
                                              reply_to_message_id=m.message_id, parse_mode='markdown')
        else:
            await jr.send_message(m.chat.id, f'*Топ-10 участников чата*:\n {users_top}\nВсего юзеров в боте: {count_users}',
                                  reply_to_message_id=m.message_id, parse_mode='markdown')
            await jr.send_message(m.chat.id, f'*Топ-10 групп*:\n {groups_top}\n Всего групп с ботом: {count_groups}',
                                  parse_mode='markdown')
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['give_stats'])
async def give_stats(m):
    try:
        if m.from_user.id in developers:
            if m.reply_to_message:
                arg = int(m.text.split()[1])
                user_id = m.reply_to_message.from_user.id
                stats = col_private.find_one({'user': user_id})['stats']
                col_private.update_one({'user': user_id},
                                       {'$inc': {'stats': arg}})
                new_stats = stats+arg
                await jr.send_message(m.chat.id, f'Успех для {user_id}\n Было: {stats}\n Стало: {new_stats}')
            else:
                arg = int(m.text.split()[1])
                stats = collection2.find_one({'group': m.chat.id})['stats']
                collection2.update_one({'group': m.chat.id},
                                       {'$inc': {'stats': arg}})
                new_stats = stats + arg
                await jr.send_message(m.chat.id, f'Успех для {m.chat.id}\n Было: {stats}\n Стало: {new_stats}')
    except:
        print(traceback.format_exc())


@jp.message_handler(commands=['clean'])
async def clean(m):
    try:
        if m.from_user.id in developers:
            stopped_groups = await groups_check()
            for group in stopped_groups:
                collection2.delete_one({'group': group})
                for user in col_private.find({'user': {'$exists': True}}):
                    if group in user['groups']:
                        col_private.update_one({'user': user['user']},
                                               {'$pull': {'groups': group}})
            await jr.send_message(m.chat.id, str(stopped_groups) + ' cleaned.')
            stopped_users = await users_check()
            for user in stopped_users:
                if user['groups'] == []:
                    collection2.delete_one({'user': user})
                    for group in collection2.find({'group': {'$exists': True}}):
                        if user in group['players']:
                            collection2.update_one({'group': group['group']},
                                                   {'$pull': {'players': user}})
            await jr.send_message(m.chat.id, str(stopped_users) + ' cleaned.')
    except:
        print(traceback.format_exc())


async def groups_check():
    groups = collection2.find({'group': {'$exists': True}}).sort('stats', pymongo.DESCENDING)
    blocked = []
    for group in groups:
        try:
            await jr.get_chat_members_count(group['group'])
        except(exceptions.BotKicked, exceptions.Unauthorized):
            blocked.append(group['group'])
            continue
        except exceptions.ChatNotFound:
            continue
    return blocked


async def users_check():
    users = col_private.find({'user': {'$exists': True}})
    blocked = []
    for user in users:
        try:
            await jr.send_chat_action(user['user'], 'typing')
        except(exceptions.BotBlocked, exceptions.UserDeactivated, exceptions.Unauthorized, exceptions.UserDeactivated):
            blocked.append(user['user'])
            continue
        except(exceptions.ChatNotFound, exceptions.InvalidUserId):
            continue
    return blocked


executor.start_polling(jp, loop=loop, skip_updates=True)
