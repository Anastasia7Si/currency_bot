from datetime import datetime
import logging
import requests

from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, Updater

from models import db, User, UserRate

secret_token = '6316015774:AAGFBiErx6-CMrRk0x3e9YhL34bhFnVTxAo'
URL = 'https://www.cbr-xml-daily.ru/daily_json.js'


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


class AddBot:
    """"Класс дополнительного бота."""
    def __init__(self, token, db):
        self.updater = None
        self.dp = None
        self.dp = None

    def start(self):
        pass


class TelegramBot:
    """Класс телеграмм-бота."""
    def __init__(self, token, db):
        self.updater = Updater(token, use_context=True)
        self.dp = self.updater.dispatcher
        self.db = db
        self.button = ReplyKeyboardMarkup([
            ['/start'], ['/dollar_rate'],
            ['/subscribe'], ['/history']],
            resize_keyboard=True)
# self.add_bot = AddBot()

    def start(self, update, context):
        user_id = update.effective_user.id
        user = User.get_or_create(user_id=user_id)
        context.bot.send_message(
            chat_id=user_id,
            text='Привет, я - Валютный бот!',
            reply_markup=self.button
            )
# self.add_bot.start()

    def get_dollar_rate(self, update, context):
        response = None
        try:
            response = requests.get(URL)
        except Exception as error:
            logging.error(f'Ошибка при запросе к серверу: {error}. '
                          f'Пожалуйста, попробуйте позже')
        if response is not None:
            user_id = update.effective_user.id
            response = response.json()
            dollar_rate = response['Valute']['USD']['Value']
            UserRate.create(user_id=user_id, rate=dollar_rate)
            massege = f'Текущий курс доллара {dollar_rate} рублей.'
            context.bot.send_message(chat_id=user_id, text=massege)
            return dollar_rate

    def get_subscribe_updates(self, update, context):
        user_id = update.effective_user.id
        user = User.get(User.user_id == user_id)
        job_queue = context.job_queue
        if user.subscribed is False:
            jobs = job_queue.get_jobs_by_name('send_rate_subscribe')
            updated_rate = self.get_dollar_rate(update, context)
            if updated_rate is not None:
                if len(jobs) == 0:
                    UserRate.create(user_id=user_id, rate=updated_rate)
                    job_queue.run_repeating(
                      self.send_rate_subscribe,
                      interval=60,
                      context=user_id,
                      name='send_rate_subscribe'
                    )
                    context.bot.send_message(
                      chat_id=user_id,
                      text='Подписка на курс доллара успешно оформлена.'
                    )
                    user.subscribed = True
                    user.save()
        else:
            jobs = job_queue.get_jobs_by_name('send_rate_subscribe')
            if len(jobs) > 0:
                jobs[0].schedule_removal()
                context.bot.send_message(
                   chat_id=user_id,
                   text='Подписка на курс доллара успешно отменена.'
                )
                user.subscribed = False
                user.save()

    def send_rate_subscribe(self, context: CallbackContext):
        date = datetime.now()
        date_now = date.strftime("%Y-%m-%d %H:%M:%S")
        user_id = context.job.context
        user_rate = UserRate.select().where(
            UserRate.user_id == user_id).order_by(UserRate.id.desc()).first()
        context.bot.send_message(
            chat_id=user_id,
            text=f'Курс доллара: {user_rate.rate} на {date_now}'
        )

    def get_history(self, update, context):
        user_id = update.effective_user.id
        history = UserRate.select().where(
            UserRate.user_id == user_id).order_by(UserRate.id.desc())[:5]
        response = 'История изменения курса доллара:\n'
        for entry in history:
            response += f'{entry.rate}\n'
        context.bot.send_message(chat_id=user_id, text=response)

    def main(self):
        self.dp.add_handler(CommandHandler('start', self.start))
        self.dp.add_handler(CommandHandler(
            'dollar_rate', self.get_dollar_rate)
        )
        self.dp.add_handler(CommandHandler(
            'subscribe', self.get_subscribe_updates)
        )
        self.dp.add_handler(CommandHandler('history', self.get_history))
# self.dp.add_handler(CommandHandler('add_bot_command', self.add_bot))
        self.updater.start_polling()
        self.updater.idle()


if __name__ == '__main__':
    bot = TelegramBot(token=secret_token, db=db)
    bot.main()
