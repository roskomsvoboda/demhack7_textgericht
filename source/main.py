import logging
import os
import re
import sys
import traceback

from telegram import Update, constants
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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
    parse_patterns = [re.compile(".*не обнаружен.*"), re.compile(".*отсутствует.*"), re.compile(".* нет .*")]
    result = gptController.process_text(text=update.message.text, parse_patterns=parse_patterns)
    if isinstance(result, str):
        await update.message.reply_text(result)
        return
    # Store data about request
    await dbController.process_text_check(update.message.text, result)
    await update.message.reply_text(result['logical_fallacies'])

async def link_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("No URL were provided. Aborting")
        return
    await update.message.reply_text(dbController.get_link_info(context.args[0]))

async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("No language were provided. Aborting")
        return
    context.user_data["lang"] = context.args[0]
    await update.message.reply_text("All responses to you would be in {} language".format(context.args[0]))

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=os.getenv("DEVELOPER_CHAT_ID"), text="This error has occured: " + ''.join(traceback.format_exception(etype=type(context.error), value=context.error, tb=context.error.__traceback__))
    )


def main() -> None:
    
    application = Application.builder().token(os.getenv('BOT_TOKEN')).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("link_info", link_info))
    application.add_handler(CommandHandler("set_lang", set_lang))
    application.add_error_handler(error)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_check))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()