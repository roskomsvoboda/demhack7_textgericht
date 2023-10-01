import logging
import traceback
import os
import re
from telegram import ForceReply, Update, constants, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import sys
sys.path.append("./Controllers")
from DBController import DBController
from GPTController import GPTController

gptController = GPTController(os.getenv('GPT_TOKEN'))
dbController = DBController(os.getenv('DB_PATH'))

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def get_info():
    return """This bot can check if given text manipulative or not.
To do this simply send your text to the bot and it will reply on the language of the given text to you.
Text could be also forwarded message. If you send a single URL, then command /link_info will be used.
If you want to get answer in any other language please call /set_lang {Full name of language: English}.
If you want to check the source by URL please use /link_info {URL}.
    """

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hello {user.mention_html()}! Here is the info how to use this bot:" + get_info(),
    )
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(get_info())

async def text_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Use this link to make bot typing
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=constants.ChatAction.TYPING)

    result = gptController.check_text(update.message.text, context.chat_data["lang"] if "lang" in context.chat_data.keys() else "As text")
    # Store data about request
    await dbController.process_text_check(update.message.text, result)

    await update.message.reply_text(result)
    # You can put info of any text instead of 'metainfo' word, this is to understand for which text feedback is
    feedback_options=[
        InlineKeyboardButton("Good", callback_data="metainfo;answer:1"), 
        InlineKeyboardButton("Bad", callback_data="metainfo;answer:0"), 
        InlineKeyboardButton("No idea", callback_data="metainfo;answer:-1")
    ]
    await update.message.reply_text("Plase provide your feedback on the answer",
     reply_markup=InlineKeyboardMarkup(
            [feedback_options]
        ),)

async def link_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("No URL were provided. Aborting")
        return
    
    await context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=constants.ChatAction.TYPING)

    result = gptController.check_url(context.args[0], context.chat_data["lang"] if "lang" in context.chat_data.keys() else "As text")
    await dbController.process_url_check(update.message.text, result)

    await update.message.reply_text(result)

    feedback_options=[
        InlineKeyboardButton("Good", callback_data="metainfo;answer:1"), 
        InlineKeyboardButton("Bad", callback_data="metainfo;answer:1"), 
        InlineKeyboardButton("No idea", callback_data="metainfo;answer:1")
    ]
    await update.message.reply_text("Plase provide your feedback on the answer",
     reply_markup=InlineKeyboardMarkup(
            [feedback_options]
        ),)


async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("No language were provided. Aborting")
        return
    context.chat_data["lang"] = context.args[0]
    await update.message.reply_text("All responses to you would be in {} language".format(context.args[0]))

async def feedback_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    reply = query.data # info that you put in feedback options in text check of url check
    await dbController.process_feedback(reply)
    
    await query.answer()
    await query.edit_message_text(text="Thank you for your feedback!")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Sorry, but there is an error on our side and I can't proccess your request right now. Incident was reported.")
    await context.bot.send_message(
        chat_id=os.getenv("DEVELOPER_CHAT_ID"), text="This error has occured: " + ''.join(traceback.format_exception(etype=type(context.error), value=context.error, tb=context.error.__traceback__))
    )


def main() -> None:
    
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("link_info", link_info, filters=(filters.Entity("url") | filters.Entity("text_link"))))
    application.add_handler(CommandHandler("set_lang", set_lang))
    application.add_error_handler(error)
    application.add_handler(CallbackQueryHandler(feedback_button))

    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, text_check))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()